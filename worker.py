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
    def __init__(self, list_info_private_key: list, main_private_key: list, sleep_range_min, sleep_range_max, update_table_1 = None, error_signal = None, parent = None):
        super().__init__(parent)
        self.list_info_private_key = list_info_private_key
        self.main_private_key = main_private_key
        self.sleep_range_min = sleep_range_min
        self.sleep_range_max = sleep_range_max
        self.update_table_1 = update_table_1
        self.error_signal = error_signal


    def run(self):
        print('Worker Transfer started')
        print('List private key:', self.list_info_private_key)
        # get balance of main private key
        transfer = Transfer(CONFIG.SOLANA_RPC_END_POINT)
        print('Main private key:', self.main_private_key)
        main_balance = transfer.get_sol_balance(self.main_private_key)
        
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
                args=(to_private_key, amount)
            )
            t.start()
            threads.append(t)

            time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

        for t in threads:
            t.join()

        print('Worker Transfer finished')
    

    def transfer_to_each_wallet(self, to_private_key: str, amount: float):
        try:
            transfer = Transfer(CONFIG.SOLANA_RPC_END_POINT, self.update_table_1)

            flag = transfer.transfer_sol(self.main_private_key, to_private_key, amount)
            if flag == False:
                self.update_table_1.emit(to_private_key, 'Failed')
                return
            
            self.update_table_1.emit(to_private_key, 'Success')
            
        except Exception as e:
            self.update_table_1.emit(to_private_key, 'Failed')
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

    def make_swap(self, private_key: str, amount_buy: float, amount_sell: float):
        try:
            swap = RaydiumSwap(CONFIG.SOLANA_RPC_END_POINT, private_key, self.update_table_2)
            # buy token
            while True:
                if private_key not in self.control_list:
                    return
                sol_balance = swap.get_sol_balance()
                sol_balance = sol_balance / 10**9
                # percent of sol to swap
                amount_lamports_buy = sol_balance * int(amount_buy) / 100
                pair_address = utils.get_pair_address(self.swap_token_contract)
                if not pair_address:
                    self.update_table_2.emit(private_key, 'Get pair address failed')
                    return
                
                flag = swap.buy(pair_address, amount_lamports_buy)
                if not flag:
                    self.update_table_2.emit(private_key, 'Transaction buy error or max try reached')
                
                if flag == False:
                    self.update_table_2.emit(private_key, 'Transaction buy failed')
                    
                elif flag == True:
                    self.update_table_2.emit(private_key, 'Transaction buy success')

                    token_balance = swap.get_token_balance(self.swap_token_contract)

                    amount_lamports_sell = token_balance * int(amount_sell) / 100
                    flag = swap.sell(pair_address, amount_lamports_sell)
                    if not flag:
                        self.update_table_2.emit(private_key, 'Transaction sell error or max try reached')
                    
                    if flag == False:
                        self.update_table_2.emit(private_key, 'Transaction sell failed')
                        
                    elif flag == True:
                        self.update_table_2.emit(private_key, 'Transaction sell success')

                
                time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

        except Exception as e:
            self.update_table_2.emit(private_key, 'Swap error')
            traceback.print_exc()
            print('Swap error')
            return
        

    def run(self):
        self.threads = []

        for info in self.list_info_private_key:
            private_key = info[0]
            amount_buy = info[1]
            amount_sell = info[2]

            self.update_table_2.emit(private_key, 'Processing')
            self.control_list.append(private_key)
            t = threading.Thread(
                target=self.make_swap,
                args=(private_key, amount_buy, amount_sell)
            )
            
            t.start()
            self.threads.append(t)
            time.sleep(random.uniform(float(self.sleep_range_min), float(self.sleep_range_max)))

        for t in self.threads:
            t.join()

        print('Worker Raydium Swap finished')

    
    def stop_now(self):
        self.control_list.clear()




if __name__ == '__main__':
    worker = Transfer()
    private_key = '37v4xuhNFhgzSevL6xr84JjHMEUErirYvLvdKedaK2rYRdvjC35Dpm6RKRBWRq2xLnCmWxxaWE6gmi4BrDPa7PWY'
    worker.transfer_sol(private_key)