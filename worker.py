import os
import json
import time
import random
import threading
import traceback
import utils

from PyQt5.QtCore import QThread

from helper import Transfer, RaydiumSwap
from config import CONFIG


class Worker_Transfer(QThread):
    def __init__(self, list_info_private_key: list, main_private_key: list, sleep_range_min: str, sleep_range_max: str, is_transfer_sol: bool, is_from_main_wallet: bool, token_contract: str, update_table_1 = None, error_signal = None, parent = None):
        super().__init__(parent)
        self.list_info_private_key = list_info_private_key
        self.main_private_key = main_private_key
        self.sleep_range_min = sleep_range_min
        self.sleep_range_max = sleep_range_max
        self.update_table_1 = update_table_1
        self.error_signal = error_signal
        self.is_transfer_sol = is_transfer_sol
        self.is_from_main_wallet = is_from_main_wallet
        self.token_contract = token_contract
        self.is_stop = False


    def run(self):
        print('Worker Transfer started')
        print('List private key:', self.list_info_private_key)
        # get balance of main private key
        transfer = Transfer(CONFIG.SOLANA_RPC_END_POINT)
        
        if self.is_from_main_wallet == True:
            if self.is_transfer_sol == True:
                print('Main private key:', self.main_private_key)
                main_balance = transfer.get_sol_balance(self.main_private_key)

                print('Main balance:', main_balance)
                
                total_amount_to_transfer = 0
                for info in self.list_info_private_key:
                    total_amount_to_transfer += float(info[1])

                if main_balance == False:
                    self.error_signal.emit('Invalid private key or network error', 1)
                    return
                
                main_balance = main_balance / 10**9
                print('Main balance:', main_balance)

                if main_balance < total_amount_to_transfer:
                    self.error_signal.emit('Balance is not enough', 1)
                    return
                
                threads = []
                for info in self.list_info_private_key:
                    to_private_key = info[0]
                    amount = info[1]
                    self.update_table_1.emit(to_private_key, 'Processing')
                    t = threading.Thread(
                        target=self.transfer_to_each_wallet,
                        args=(self.main_private_key, to_private_key, amount)
                    )
                    t.start()
                    threads.append(t)

                    time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

                for t in threads:
                    t.join()

            else:
                print('Main private key:', self.main_private_key)
                print(self.main_private_key, self.token_contract)
                main_balance = transfer.get_token_balance(self.main_private_key, self.token_contract)

                print('Main balance:', main_balance)

                total_amount_to_transfer = 0

                for info in self.list_info_private_key:
                    total_amount_to_transfer += float(info[1])

                if main_balance == False:
                    self.error_signal.emit('Invalid private key or network error', 1)
                    return
                
                main_balance = main_balance / 10**9
                print('Main balance:', main_balance)

                if main_balance < total_amount_to_transfer:
                    self.error_signal.emit('Balance is not enough', 1)
                    return
                
                threads = []
                for info in self.list_info_private_key:
                    to_private_key = info[0]
                    amount = float(info[1])
                    mint = self.token_contract
                    self.update_table_1.emit(to_private_key, 'Processing')
                    t = threading.Thread(
                        target=self.transfer_token_to_each_wallet,
                        args=(self.main_private_key, to_private_key, amount, mint)
                    )
                    t.start()
                    threads.append(t)

                    time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))
                

                for t in threads:
                    t.join()

        else:
            if self.is_transfer_sol == True:
                threads = []
                for info in self.list_info_private_key:
                    from_private_key = info[0]
                    to_private_key = self.main_private_key
                    # get balance of from private key
                    from_balance = transfer.get_sol_balance(from_private_key)
                    if from_balance == 0:
                        self.update_table_1.emit(from_private_key, 'Oups! Balance is 0')
                        continue
                    
                    from_balance = from_balance / 10**9
                    self.update_table_1.emit(from_private_key, 'Processing')
                    t = threading.Thread(
                        target=self.transfer_to_each_wallet,
                        args=(from_private_key, to_private_key, from_balance)
                    )
                    t.start()
                    threads.append(t)

                    time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

                for t in threads:
                    t.join()

            else:
                threads = []
                for info in self.list_info_private_key:
                    from_private_key = info[0]
                    to_private_key = self.main_private_key
                    # get balance of from private key
                    from_balance = transfer.get_token_balance(from_private_key, self.token_contract)
                    if from_balance == 0:
                        self.update_table_1.emit(from_private_key, 'Oups! Balance is 0')
                        continue

                    from_balance = from_balance / 10**9
                    mint = self.token_contract
                    self.update_table_1.emit(from_private_key, 'Processing')
                    t = threading.Thread(
                        target=self.transfer_token_to_each_wallet,
                        args=(from_private_key, to_private_key, from_balance, mint)
                    )
                    t.start()
                    threads.append(t)

                    time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))
                

                for t in threads:
                    t.join()

        print('Worker Transfer finished')


    def transfer_token_to_each_wallet(self, from_private_key: str, to_private_key: str, amount: float, mint: str):
        try:
            transfer = Transfer(CONFIG.SOLANA_RPC_END_POINT, self.update_table_1)
            flag = transfer.transfer_token(from_private_key, to_private_key, mint, amount)

            emit_wallet = to_private_key if self.is_from_main_wallet == True else from_private_key
            if flag == False:
                self.update_table_1.emit(emit_wallet, 'Failed')
                return
            
            self.update_table_1.emit(emit_wallet, 'Success')


        except Exception as e:
            self.update_table_1.emit(emit_wallet, 'Failed')
            traceback.print_exc()
            print('Transfer failed')
            return
    

    def transfer_to_each_wallet(self, from_private_key: str, to_private_key: str, amount: float):
        try:
            transfer = Transfer(CONFIG.SOLANA_RPC_END_POINT, self.update_table_1)
            print('Transfering from:', from_private_key)
            print('Transfering to:', to_private_key)
            print('Amount:', amount)
            flag = transfer.transfer_sol(from_private_key, to_private_key, amount)

            emit_wallet = to_private_key if self.is_from_main_wallet == True else from_private_key
            if flag == False:
                self.update_table_1.emit(emit_wallet, 'Failed')
                return
            
            self.update_table_1.emit(emit_wallet, 'Success')
            
        except Exception as e:
            self.update_table_1.emit(emit_wallet, 'Failed')
            traceback.print_exc()
            print('Transfer failed')
            return
        print('Transfer success')
        return
    

class Worker_RaydiumSwap(QThread):
    def __init__(self, list_info_private_key: list, swap_token_contract: str, sleep_range_min, sleep_range_max, update_table_2 = None, error_signal = None, parent = None):
        super().__init__(parent)
        self.list_info_private_key = list_info_private_key
        self.swap_token_contract = swap_token_contract
        self.sleep_range_min = sleep_range_min
        self.sleep_range_max = sleep_range_max
        self.update_table_2 = update_table_2
        self.error_signal = error_signal
        self.control_list = []
        self.is_stop = False

    def make_swap(self, private_key: str, amount_buy: float, amount_sell: float):
        try:
            swap = RaydiumSwap(CONFIG.SOLANA_RPC_END_POINT, private_key, self.update_table_2)
            # buy token
            while True:
                if private_key not in self.control_list:
                    return
                for _ in range(10):
                    sol_balance = swap.get_sol_balance()
                    if sol_balance != None:
                        break
                    time.sleep(3)

                sol_balance = sol_balance / 10**9
                # percent of sol to swap
                amount_lamports_buy = sol_balance * int(amount_buy) / 100
                pair_address = utils.get_pair_address(self.swap_token_contract)
                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return
                
                self.update_table_2.emit(private_key, 'Processing buy')
                for _ in range(10):
                    flag = swap.buy(pair_address, amount_lamports_buy)
                    if not flag:
                        self.update_table_2.emit(private_key, 'Transaction buy error or max try reached retrying...')
                    
                    if flag == False:
                        self.update_table_2.emit(private_key, 'Transaction buy failed retrying...')
                    
                    if flag == True:
                        break

                if flag != True:
                    self.update_table_2.emit(private_key, 'Transaction buy to many failed stop!!!')
                    return
                    
                if flag == True:
                    self.update_table_2.emit(private_key, 'Transaction buy success')

                    time.sleep(5)

                    self.update_table_2.emit(private_key, 'Processing sell')

                    for _ in range(10):
                        token_balance = swap.get_token_balance(self.swap_token_contract)
                        if token_balance != None:
                            if token_balance != 0:
                                break

                        time.sleep(3)

                    amount_lamports_sell = token_balance * int(amount_sell) / 100
                    
                    for _ in range(10):
                        flag = swap.sell(pair_address, amount_lamports_sell)
                        if not flag:
                            self.update_table_2.emit(private_key, 'Transaction sell error or max try reached retrying...')
                        
                        if flag == False:
                            self.update_table_2.emit(private_key, 'Transaction sell failed retrying...')
                            
                        elif flag == True:
                            self.update_table_2.emit(private_key, 'Transaction sell success')
                            break

                    if flag != True:
                        self.update_table_2.emit(private_key, 'Transaction to many failed stop!!!')
                        return

                
                time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

        except Exception as e:
            self.update_table_2.emit(private_key, 'Swap error')
            traceback.print_exc()
            print('Swap error')
            return
        

    def make_swap_v2(self, private_key: str, pair_address: str, amount_buy_in_sol: float, amount_sell_in_sol: float, is_buy_first: bool):
        try:
            amount_buy_in_sol = float(amount_buy_in_sol)
            amount_sell_in_sol = float(amount_sell_in_sol)
            swap = RaydiumSwap(CONFIG.SOLANA_RPC_END_POINT, private_key, self.update_table_2)
            if is_buy_first == True:
                if private_key not in self.control_list:
                    return
                # get sol balance
                for _ in range(10):
                    sol_balance = swap.get_sol_balance()
                    if sol_balance != None:
                        break

                sol_balance = sol_balance / 10**9
                if sol_balance < amount_buy_in_sol:
                    self.update_table_2.emit(private_key, 'Not enough sol balance')
                    return

                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return
                
                self.update_table_2.emit(private_key, 'Processing buy')
                for _ in range(10):
                    flag = swap.buy(pair_address, amount_buy_in_sol)
                    if not flag:
                        self.update_table_2.emit(private_key, 'Transaction buy error or max try reached retrying...')
                    
                    if flag == False:
                        self.update_table_2.emit(private_key, 'Transaction buy failed retrying...')
                    
                    if flag == True:
                        break

                if flag != True:
                    self.update_table_2.emit(private_key, 'Transaction buy to many failed stop!!!')
                    return
                
                if flag == True:
                    self.update_table_2.emit(private_key, 'Transaction buy success')

                
                for _ in range(10):
                    token_balance = swap.get_token_balance(self.swap_token_contract)
                    if token_balance != None:
                        if token_balance != 0:
                            break

                if token_balance == 0:
                    self.update_table_2.emit(private_key, 'Token balance is 0')
                    return

                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return  
                
                token_amount = swap.calculate_token_from_sol(pair_address=pair_address, amount_in_sol=amount_sell_in_sol)

                if token_balance < token_amount:
                    self.update_table_2.emit(private_key, 'Not enough token balance')
                    return

                amount_lamports_sell = token_amount * 10**9

                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return

                self.update_table_2.emit(private_key, 'Processing sell')

                for _ in range(10):
                    flag = swap.sell(pair_address, amount_lamports_sell)
                    if not flag:
                        self.update_table_2.emit(private_key, 'Transaction sell error or max try reached retrying...')
                    
                    if flag == False:
                        self.update_table_2.emit(private_key, 'Transaction sell failed retrying...')
                        
                    elif flag == True:
                        self.update_table_2.emit(private_key, 'Transaction sell success')
                        break

                if flag != True:
                    self.update_table_2.emit(private_key, 'Transaction to many failed stop!!!')
                    return
                
                
                time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

            else:
                if private_key not in self.control_list:
                    return
                
                for _ in range(10):
                    token_balance = swap.get_token_balance(self.swap_token_contract)
                    if token_balance != None:
                        if token_balance != 0:
                            break

                if token_balance == 0:
                    self.update_table_2.emit(private_key, 'Token balance is 0')
                    return

                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return  
                
                token_amount = swap.calculate_token_from_sol(pair_address=pair_address, amount_in_sol=amount_sell_in_sol)

                if token_balance < token_amount:
                    self.update_table_2.emit(private_key, 'Not enough token balance')
                    return

                amount_lamports_sell = token_amount * 10**9

                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return

                self.update_table_2.emit(private_key, 'Processing sell')

                for _ in range(10):
                    flag = swap.sell(pair_address, amount_lamports_sell)
                    if not flag:
                        self.update_table_2.emit(private_key, 'Transaction sell error or max try reached retrying...')
                    
                    if flag == False:
                        self.update_table_2.emit(private_key, 'Transaction sell failed retrying...')
                        
                    elif flag == True:
                        self.update_table_2.emit(private_key, 'Transaction sell success')
                        break

                if flag != True:
                    self.update_table_2.emit(private_key, 'Transaction to many failed stop!!!')
                    return
                

                # get sol balance
                for _ in range(10):
                    sol_balance = swap.get_sol_balance()
                    if sol_balance != None:
                        break

                sol_balance = sol_balance / 10**9
                if sol_balance < amount_buy_in_sol:
                    self.update_table_2.emit(private_key, 'Not enough sol balance')
                    return

                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return
                
                self.update_table_2.emit(private_key, 'Processing buy')
                for _ in range(10):
                    flag = swap.buy(pair_address, amount_buy_in_sol)
                    if not flag:
                        self.update_table_2.emit(private_key, 'Transaction buy error or max try reached retrying...')
                    
                    if flag == False:
                        self.update_table_2.emit(private_key, 'Transaction buy failed retrying...')
                    
                    if flag == True:
                        break

                if flag != True:
                    self.update_table_2.emit(private_key, 'Transaction buy to many failed stop!!!')
                    return
                
                if flag == True:
                    self.update_table_2.emit(private_key, 'Transaction buy success')

        
        except Exception as e:
            self.update_table_2.emit(private_key, 'Swap error')
            traceback.print_exc()
            print('Swap error')
            return
        

    def run(self):
        self.threads = []

        # for info in self.list_info_private_key:
        #     private_key = info[0]
        #     amount_buy = info[1]
        #     amount_sell = info[2]

        #     self.update_table_2.emit(private_key, 'Processing')
        #     self.control_list.append(private_key)
        #     t = threading.Thread(
        #         target=self.make_swap,
        #         args=(private_key, amount_buy, amount_sell)
        #     )
            
        #     t.start()
        #     self.threads.append(t)
        #     time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

        # for t in self.threads:
        #     t.join()

        # print('Worker Raydium Swap finished')

        # create a flow for buy and sell in same time different thread different private key with 4 threads in same time

        pair_address = utils.get_pair_address(self.swap_token_contract)
        print('Pair address:', pair_address)

        is_buy_first = True
        while True:
            if self.is_stop == True:
                break

            for info in self.list_info_private_key:
                private_key = info[0]
                amount_buy_in_sol = info[1]
                amount_sell_in_sol = info[2]

                self.update_table_2.emit(private_key, 'Processing')
                self.control_list.append(private_key)
                t = threading.Thread(
                    target=self.make_swap_v2,
                    args=(private_key, pair_address, amount_buy_in_sol, amount_sell_in_sol, is_buy_first)
                )
                
                t.start()
                self.threads.append(t)

                is_buy_first = not is_buy_first

            for t in self.threads:
                t.join()

    
    def stop_now(self):
        self.control_list.clear()
        self.is_stop = True




if __name__ == '__main__':
    worker = Transfer()
    private_key = '37v4xuhNFhgzSevL6xr84JjHMEUErirYvLvdKedaK2rYRdvjC35Dpm6RKRBWRq2xLnCmWxxaWE6gmi4BrDPa7PWY'
    worker.transfer_sol(private_key)