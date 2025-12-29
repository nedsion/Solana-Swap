import json
import time
import base58
import traceback

from solders.pubkey import Pubkey # type: ignore
from solana.rpc.api import Client, Keypair, Transaction
from solders.system_program import TransferParams, transfer

from solana.rpc.types import TokenAccountOpts, TxOpts
from solana.rpc.types import TxOpts
import solders.system_program as system_program
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price #type: ignore
from solders.keypair import Keypair #type: ignore
from solders.transaction import VersionedTransaction #type: ignore
from solders.message import MessageV0 #type: ignore
from spl.token.client import Token
from spl.token.constants import WRAPPED_SOL_MINT
from spl.token.instructions import close_account, CloseAccountParams, transfer_checked, get_associated_token_address, TransferCheckedParams
import spl.token.instructions as spl_token_instructions

from config import CONFIG
from constants import CONSTANTS
from layouts import ACCOUNT_LAYOUT
from utils import fetch_pool_keys, make_swap_instruction, get_token_account, confirm_txn, get_token_balance_lamports, get_recent_prioritization_fees, get_token_price


class Transfer:
    def __init__(self, rpc_endpoint: str, update_table_log = None) -> None:
        self.client = Client(rpc_endpoint)
        self.update_table_log = update_table_log

    def send_log(self, to_private_key: str, message: str):
        if self.update_table_log:
            self.update_table_log.emit(to_private_key, message)

    def get_pubkey(self, private_key: str) -> str:
        key_pair = Keypair.from_base58_string(private_key)
        return key_pair.pubkey()

    def get_sol_balance(self, private_key) -> int:
        try:
            key_pair = Keypair.from_base58_string(private_key)
            balance = self.client.get_balance(key_pair.pubkey())
            return balance.value
        
        except Exception as e:
            return False
    
    
    def transfer_sol(self, private_key: str, to_private_key: str, amounts: float):
        try:
            st = time.time()
            key_pair = Keypair.from_base58_string(private_key)

            amounts = int(float(amounts) * (10**9))
            print('Amounts:', amounts)
            balance = self.get_sol_balance(private_key)

            if balance < amounts:
                print("Balance is not enough")
                return

            # Get rent exempt minimum
            rent_exempt_minimum_response = self.client.get_minimum_balance_for_rent_exemption(0)
            rent_exempt_minimum = rent_exempt_minimum_response.value

            # Get recipient balance
            to_pubkey = Keypair.from_base58_string(to_private_key).pubkey()
            recipient_balance = self.client.get_balance(to_pubkey)

            if recipient_balance.value < rent_exempt_minimum:
                fund_amount = rent_exempt_minimum - recipient_balance.value
                print(f"Recipient account is not rent exempt. Funding with {fund_amount} SOL")
                self.send_log(to_private_key, f"Recipient account is not rent exempt. Funding with {fund_amount} SOL")
                fund_transfer_params = TransferParams(
                    from_pubkey=key_pair.pubkey(),
                    to_pubkey=to_pubkey,
                    lamports=fund_amount,
                )
                fund_transaction = Transaction().add(transfer(fund_transfer_params))
                fund_response = self.client.send_transaction(fund_transaction, key_pair)
                print(f"Fund transaction signature: {fund_response}")
                print('-'*50)
                data = self.client.confirm_transaction(fund_response.value, sleep_seconds = 1)
                print('Fund Response:', data)

            # Transfer SOL to the recipient
            transfer_fee = 5000 
            amounts -= transfer_fee
            transfer_params = TransferParams(
                from_pubkey=key_pair.pubkey(),
                to_pubkey=to_pubkey,
                lamports=amounts,
            )

            recent_blockhash_response = self.client.get_latest_blockhash()
            recent_blockhash = recent_blockhash_response.value.blockhash

            
            transaction = Transaction(recent_blockhash=recent_blockhash).add(transfer(transfer_params))
            print('Transaction:', transaction)
            print('-'*50)
            response = self.client.send_transaction(transaction, key_pair)
            print('Response:', response.value)
            data = self.client.confirm_transaction(response.value, sleep_seconds = 3)
            print('Confirm Response:', data)
            print("Time taken:", time.time() - st)
            return True
        
        except Exception as e:
            traceback.print_exc()
            return False
        
    def get_token_balance(self, private_key: str, mint: str) -> int:
        try:
            print('Getting token balance...')
            print('Private Key:', private_key)
            print('Mint:', mint)
            key_pair = Keypair.from_base58_string(private_key)
            token_amount = get_token_balance_lamports(str(key_pair.pubkey()), mint)

            return token_amount
        
        except Exception as e:
            traceback.print_exc()
            return False

    def transfer_token(self, private_key: str, to_private_key: str, mint: str, amounts: float):
        try:
            st = time.time()
            from_wallet = Keypair.from_base58_string(private_key)
            to_wallet = Keypair.from_base58_string(to_private_key)
            
            balance = self.get_token_balance(private_key, mint)

            if balance < amounts:
                print("Balance is not enough")
                return False

            token = Token(self.client, Pubkey.from_string(mint), CONSTANTS.TOKEN_PROGRAM_ID, from_wallet)

            mint_info = token.get_mint_info()

            decimals = mint_info.decimals
            amounts = int(amounts * (10 ** decimals))

                # Get or create the associated token account for the sender
            sender_token_account = get_associated_token_address(from_wallet.pubkey(), Pubkey.from_string(mint))
            sender_account_info = self.client.get_account_info(sender_token_account)
            if sender_account_info.value is None:
                token.create_associated_token_account(from_wallet.pubkey())

            # Get or create the associated token account for the recipient
            recipient_token_account = get_associated_token_address(to_wallet.pubkey(), Pubkey.from_string(mint))
            recipient_account_info = self.client.get_account_info(recipient_token_account)
            if recipient_account_info.value is None:
                token.create_associated_token_account(to_wallet.pubkey())

            # Prepare the transfer_checked parameters
            params = TransferCheckedParams(
                program_id=CONSTANTS.TOKEN_PROGRAM_ID,      # Token program ID
                source=sender_token_account,      # Source account
                mint=Pubkey.from_string(mint),                 # Token mint address
                dest=recipient_token_account,     # Destination account
                owner=from_wallet.pubkey(),       # Owner of source account
                amount=amounts,                   # Amount to transfer
                decimals=decimals,                # Token decimals
                signers=[from_wallet.pubkey()]    # Signers
            )

            # Prepare transaction with transfer_checked
            transaction = Transaction().add(transfer_checked(params))

            # Send transaction
            response = self.client.send_transaction(transaction, from_wallet)
            confirm = self.client.confirm_transaction(response.value, sleep_seconds = 3)
            print('Confirm Response:', confirm)
            print("Time taken:", time.time() - st)
            
        except Exception as e:
            traceback.print_exc()
            return False
        


class RaydiumSwap:
    def __init__(self, rpc_endpoint, private_key, update_table_log = None) -> None:
        self.client = Client(rpc_endpoint)
        self.private_key = private_key
        self.update_table_log = update_table_log

        self.key_pair = Keypair.from_base58_string(private_key)

    def send_log(self, private_key: str, message: str):
        if self.update_table_log:
            self.update_table_log.emit(private_key, message)

    def get_sol_balance(self) -> int:
        try:
            key_pair = Keypair.from_base58_string(self.private_key)
            balance = self.client.get_balance(key_pair.pubkey())
            return balance.value
        
        except Exception as e:
            traceback.print_exc()
            return False
        
    def get_pubkey(self) -> str:
        key_pair = Keypair.from_base58_string(self.private_key)
        return key_pair.pubkey()
    
    def get_token_balance(self, mint: str) -> int:
        try:
            key_pair = Keypair.from_base58_string(self.private_key)
            token_amount = get_token_balance_lamports(str(key_pair.pubkey()), mint)
            print('Token Amount:', token_amount)
            return token_amount
        
        except Exception as e:
            return False
        

    def get_token_price(self, pair_address: str, amount_token_in: int) -> float:
        """
        Returns the price of the tokens in SOL
        """
        try:
            token_price_on_sol = get_token_price(self.client, pair_address)
            if token_price_on_sol is None:
                return None
            
            return token_price_on_sol * amount_token_in
            

        except Exception as e:
            traceback.print_exc()
            return False
        

    def calculate_token_from_sol(self, pair_address: str, amount_in_sol: float) -> float:
        try:
            token_price_on_sol = get_token_price(self.client, pair_address)
            if token_price_on_sol is None:
                return None
            
            return amount_in_sol / token_price_on_sol
            
            
        except Exception as e:
            traceback.print_exc()
            return False
    

    def buy(self, pair_address: str, amount_in_sol: float):
        try:
            # Fetch pool keys
            print("Fetching pool keys...")
            pool_keys = fetch_pool_keys(self.client, pair_address)
            
            # Check if pool keys exist
            if pool_keys is None:
                print("No pools keys found...")
                return None

            # Determine the mint based on pool keys
            mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != CONSTANTS.SOL else pool_keys['quote_mint']
            amount_in = int(amount_in_sol * CONSTANTS.LAMPORTS_PER_SOL)

            # Get token account and token account instructions
            print("Getting token account...")
            token_account, token_account_instructions = get_token_account(self.client, self.key_pair.pubkey(), mint)

            # Get minimum balance needed for token account
            print("Getting minimum balance for token account...")
            balance_needed = Token.get_min_balance_rent_for_exempt_for_account(self.client)

            # Create a keypair for wrapped SOL (wSOL)
            print("Creating keypair for wSOL...")
            wsol_account_keypair = Keypair()
            wsol_token_account = wsol_account_keypair.pubkey()
            
            instructions = []

            # Create instructions to create a wSOL account, include the amount in 
            print("Creating wSOL account instructions...")
            create_wsol_account_instructions = system_program.create_account(
                system_program.CreateAccountParams(
                    from_pubkey=self.key_pair.pubkey(),
                    to_pubkey=wsol_account_keypair.pubkey(),
                    lamports=int(balance_needed + amount_in),
                    space=ACCOUNT_LAYOUT.sizeof(),
                    owner=CONSTANTS.TOKEN_PROGRAM_ID,
                )
            )

            # Initialize wSOL account
            print("Initializing wSOL account...")
            init_wsol_account_instructions = spl_token_instructions.initialize_account(
                spl_token_instructions.InitializeAccountParams(
                    account=wsol_account_keypair.pubkey(),
                    mint=CONSTANTS.WSOL,
                    owner=self.key_pair.pubkey(),
                    program_id=CONSTANTS.TOKEN_PROGRAM_ID,
                )
            )

            # Create swap instructions
            print("Creating swap instructions...")
            swap_instructions = make_swap_instruction(amount_in, wsol_token_account, token_account, pool_keys, self.key_pair)

            # Create close account instructions for wSOL account
            print("Creating close account instructions...")
            close_account_instructions = close_account(CloseAccountParams(CONSTANTS.TOKEN_PROGRAM_ID, wsol_token_account, self.key_pair.pubkey(), self.key_pair.pubkey()))

            # Append instructions to the list
            print("Appending instructions...")
            instructions.append(set_compute_unit_limit(CONSTANTS.UNIT_BUDGET)) 
            instructions.append(set_compute_unit_price(CONSTANTS.UNIT_PRICE))
            instructions.append(create_wsol_account_instructions)
            instructions.append(init_wsol_account_instructions)
            if token_account_instructions:
                instructions.append(token_account_instructions)
            instructions.append(swap_instructions)
            instructions.append(close_account_instructions)

            # Compile the message
            print("Compiling message...")
            compiled_message = MessageV0.try_compile(
                self.key_pair.pubkey(),
                instructions,
                [],  
                self.client.get_latest_blockhash().value.blockhash,
            )

            # Create and send transaction
            print("Creating and sending transaction...")
            transaction = VersionedTransaction(compiled_message, [self.key_pair, wsol_account_keypair])
            txn_sig = self.client.send_transaction(transaction, opts=TxOpts(skip_preflight=True, preflight_commitment="processed", max_retries=10)).value
            print("Transaction Signature:", txn_sig)
            
            # Confirm transaction
            print("Confirming transaction...")
            confirm = confirm_txn(self.client, txn_sig)
            
            return confirm
        
        except Exception as e:
            traceback.print_exc()
            return False

    def sell(self, pair_address: str, amount_in_lamports: int):
        try:
            # Convert amount to integer
            amount_in = int(amount_in_lamports)
            
            # Fetch pool keys
            print("Fetching pool keys...")
            pool_keys = fetch_pool_keys(self.client, pair_address)
            
            # Check if pool keys exist
            if pool_keys is None:
                print("No pools keys found...")
                return None
                
            # Determine the mint based on pool keys
            mint = pool_keys['base_mint'] if str(pool_keys['base_mint']) != CONSTANTS.SOL else pool_keys['quote_mint']
            
            # Get token account
            print("Getting token account...")
            token_account = self.client.get_token_accounts_by_owner(self.key_pair.pubkey(), TokenAccountOpts(mint)).value[0].pubkey
            
            # Get wSOL token account and instructions
            print("Getting wSOL token account...")
            wsol_token_account, wsol_token_account_instructions = get_token_account(self.client, self.key_pair.pubkey(), WRAPPED_SOL_MINT)
            
            # Create swap instructions
            print("Creating swap instructions...")
            swap_instructions = make_swap_instruction(amount_in, token_account, wsol_token_account, pool_keys, self.key_pair)
            
            # Create close account instructions for wSOL account
            print("Creating close account instructions...")
            close_account_instructions = close_account(CloseAccountParams(CONSTANTS.TOKEN_PROGRAM_ID, wsol_token_account, self.key_pair.pubkey(), self.key_pair.pubkey()))

            # Initialize instructions list
            instructions = []
            print("Appending instructions...")
            instructions.append(set_compute_unit_limit(CONSTANTS.UNIT_BUDGET)) 
            instructions.append(set_compute_unit_price(CONSTANTS.UNIT_PRICE))
            if wsol_token_account_instructions:
                instructions.append(wsol_token_account_instructions)
            instructions.append(swap_instructions)
            instructions.append(close_account_instructions)
            
            # Compile the message
            print("Compiling message...")
            compiled_message = MessageV0.try_compile(
                self.key_pair.pubkey(),
                instructions,
                [],  
                self.client.get_latest_blockhash().value.blockhash,
            )

            # Create and send transaction
            print("Creating and sending transaction...")
            transaction = VersionedTransaction(compiled_message, [self.key_pair])
            txn_sig = self.client.send_transaction(transaction, opts=TxOpts(skip_preflight=True, preflight_commitment="confirmed", max_retries=10)).value
            print("Transaction Signature:", txn_sig)
            
            # Confirm transaction
            print("Confirming transaction...")
            confirm = confirm_txn(self.client, txn_sig)
            return confirm
        
        except Exception as e:
            traceback.print_exc()
            return False

        


if __name__ == '__main__':
    transfers = Transfer(CONFIG.SOLANA_RPC_END_POINT)
    private_key = 'oiSvbPA5HT3Wn9CnxEwNcckw3QVhgvNvCs6SMk4TrdquEyEg3UVqadcgE5LEWaZuBkxLcyZFHCHTmuhnm6VW1D3'
    to_private_key = '3JRUKrrfxNsdsKkLvveEtnY4dAYFv5qxpSUNbcePbH4xNd5g1r5nihKpsj6Y5orkfPjjER6xJ84VEj9dctwJ98UK'
    mint = 'Hbqe8GJ6pM6roBGfK7bFHPajnEeX8gk9DYeQXu8gGDQF'


    # transfers.transfer_token(private_key, to_private_key, mint, 0.1)

    swap = RaydiumSwap(CONFIG.SOLANA_RPC_END_POINT, private_key)
    # price = swap.get_token_price('9iL89qfbTMWygtawzGikL2j6ASbRYX7XSM5ePUcoQ5fk', 5)
    # print(price)
    # # 8.345265247423214e-05 to real value
    # decimal_form = format(price, '.20f')
    # print(decimal_form)

    amount_token = swap.calculate_token_from_sol('9iL89qfbTMWygtawzGikL2j6ASbRYX7XSM5ePUcoQ5fk', 5)
    print(type(amount_token))



    # swap = RaydiumSwap(CONFIG.SOLANA_RPC_END_POINT, private_key)
    # print(swap.get_sol_balance())
    # print(swap.get_token_balance(mint))
    