import json
import time
import base58
import traceback

from solders.pubkey import Pubkey # type: ignore
from solana.rpc.api import Client, Keypair, Transaction
from solders.system_program import TransferParams, transfer

from config import CONFIG


class Transfer:
    def __init__(self, rpc_endpoint: str) -> None:
        self.client = Client(rpc_endpoint)

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
    
    def transfer_sol(self, private_key, to_address: str, amounts: float):
        try:
            st = time.time()
            key_pair = Keypair.from_base58_string(private_key)
            # 0.00006450000
            amounts = amounts * 10**9
            balance = self.get_sol_balance(private_key)

            if balance < amounts:
                print("Balance is not enough")
                return

            # Get rent exempt minimum
            rent_exempt_minimum_response = self.client.get_minimum_balance_for_rent_exemption(0)
            rent_exempt_minimum = rent_exempt_minimum_response.value

            # Get recipient balance

            to_pubkey = Pubkey.from_string(to_address)
            recipient_balance = self.client.get_balance(to_pubkey)

            if recipient_balance.value < rent_exempt_minimum:
                fund_amount = rent_exempt_minimum - recipient_balance.value
                print(f"Recipient account is not rent exempt. Funding with {fund_amount} SOL")
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
            data = self.client.confirm_transaction(response.value, sleep_seconds = 1)
            print('Confirm Response:', data)
            print("Time taken:", time.time() - st)
            return True
        
        except Exception as e:
            traceback.print_exc()
            return False
        


if __name__ == '__main__':
    transfer = Transfer(CONFIG.SOLANA_RPC_END_POINT)
    private_key = '37v4xuhNFhgzSevL6xr84JjHMEUErirYvLvdKedaK2rYRdvjC35Dpm6RKRBWRq2xLnCmWxxaWE6gmi4BrDPa7PWY'
    