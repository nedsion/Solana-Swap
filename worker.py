import os
import json
import time
import random
import threading
import traceback

from PyQt5.QtCore import QThread

from helper import Transfer
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



if __name__ == '__main__':
    worker = Transfer()
    private_key = '37v4xuhNFhgzSevL6xr84JjHMEUErirYvLvdKedaK2rYRdvjC35Dpm6RKRBWRq2xLnCmWxxaWE6gmi4BrDPa7PWY'
    worker.transfer_sol(private_key)