import os
import sys
import json
import time
import threading
import subprocess
import pandas as pd

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QFileDialog, QComboBox, QTabWidget, QHeaderView, QStyleOptionButton, QStyle, QCheckBox, QMenu, QAction, QMessageBox, QRadioButton
)

from config import CONFIG
from worker import Worker_Transfer, Worker_RaydiumSwap


class HoverButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super(HoverButton, self).__init__(*args, **kwargs)
        self.default_style = self.styleSheet()

    def enterEvent(self, event):
        if self.isEnabled():
            self.setStyleSheet(self.default_style)
        super(HoverButton, self).enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled():
            self.setStyleSheet(self.default_style)
        super(HoverButton, self).leaveEvent(event)

    def paintEvent(self, event):
        if self.isEnabled() or self.isDown():
            super().paintEvent(event)
        else:
            painter = QPainter(self)
            option = self._get_button_option()
            self.style().drawControl(QStyle.CE_PushButton, option, painter, self)

    def _get_button_option(self):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.state &= ~QStyle.State_MouseOver
        return option

    def setHoverStyle(self, hover_style):
        self.default_style = hover_style


class MainWindow(QMainWindow):
    update_table1 = pyqtSignal(str, str)
    update_table2 = pyqtSignal(str, str)
    error_signal = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()

        self.setWindowTitle(CONFIG.PROGRAM_TITLE)
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()

        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        self.tabs.addTab(self.tab1, "Transfer Manager")
        self.tabs.addTab(self.tab2, "Swap Manager")
        self.tabs.addTab(self.tab3, "Settings")


        self.initTab1()
        self.initTab2()
        # self.initTab3()

        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.setCentralWidget(self.tabs)

        self.applyStyles()


    def contextMenuEvent(self, event):
        contextMenu = QMenu(self)
        action_list = ["Select All", "Unselect All"]
        actions = [contextMenu.addAction(action) for action in action_list]

        try:
            action = contextMenu.exec_(self.table1.mapToGlobal(event))
        except Exception as e:
            return

        if action == actions[0]:
            for i in range(self.table1.rowCount()):
                check_box = self.table1.cellWidget(i, 0)
                check_box.setChecked(True)
        elif action == actions[1]:
            for i in range(self.table1.rowCount()):
                check_box = self.table1.cellWidget(i, 0)
                check_box.setChecked(False)
        else:
            return
        
    def contextMenuEvent2(self, event):
        contextMenu = QMenu(self)
        action_list = ["Select All", "Unselect All"]
        actions = [contextMenu.addAction(action) for action in action_list]

        try:
            action = contextMenu.exec_(self.table2.mapToGlobal(event))
        except Exception as e:
            return

        if action == actions[0]:
            for i in range(self.table2.rowCount()):
                check_box = self.table2.cellWidget(i, 0)
                check_box.setChecked(True)
        elif action == actions[1]:
            for i in range(self.table2.rowCount()):
                check_box = self.table2.cellWidget(i, 0)
                check_box.setChecked(False)
        else:
            return
        
    def contextMenuEvent3(self, event):
        contextMenu = QMenu(self)
        action_list = ["Select All", "Unselect All"]
        actions = [contextMenu.addAction(action) for action in action_list]

        try:
            action = contextMenu.exec_(self.table3.mapToGlobal(event))
        except Exception as e:
            return

        if action == actions[0]:
            for i in range(self.table3.rowCount()):
                check_box = self.table3.cellWidget(i, 0)
                check_box.setChecked(True)
        elif action == actions[1]:
            for i in range(self.table3.rowCount()):
                check_box = self.table3.cellWidget(i, 0)
                check_box.setChecked(False)
        else:
            return

    def initTab1(self):
        layout = QVBoxLayout()

        # Table
        self.table1 = QTableWidget()
        self.table1.setRowCount(0)
        self.table1.setColumnCount(4)
        self.table1.setHorizontalHeaderLabels(["Choice", "Wallet", "Amount", "Status"])
        self.table1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table1.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.table1.setColumnWidth(0, 100)

        # Context Menu
        self.table1.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table1.customContextMenuRequested.connect(self.contextMenuEvent)

        # Options
        self.option_label = QLabel()
        options_layout = QVBoxLayout()

        # input file info .csv
        qhbox2 = QHBoxLayout()
        self.file_label = QLabel("File Selection:")
        self.file_line_edit = QLineEdit()
        self.file_button = HoverButton("Open File")
        self.file_button.setObjectName("fileButton")
        self.file_button.setHoverStyle("background-color: #1B5E20; color: white;")
        self.file_line_edit.setReadOnly(True)
        # connect the file button to open file dialog and insert the file path to the line edit
        self.file_button.clicked.connect(lambda: self.openFile(self.file_line_edit))
        self.file_line_edit.textChanged.connect(lambda: self.on_file_line_edit_changed(self.table1, self.file_line_edit.text(), 1))


        qhbox2.addWidget(self.file_label)
        qhbox2.addWidget(self.file_line_edit)
        qhbox2.addWidget(self.file_button)

        qhbox3 = QHBoxLayout()
        self.main_wallet_label = QLabel("Main Wallet:")
        self.main_wallet_line_edit = QLineEdit()
        self.main_wallet_line_edit.setPlaceholderText("Main Wallet")
        qhbox3.addWidget(self.main_wallet_label)
        qhbox3.addWidget(self.main_wallet_line_edit)

        
        qhbox = QHBoxLayout()
        self.sleep_range_label = QLabel("Sleep Range:")
        self.sleep_range_min = QLineEdit()
        self.sleep_range_min.setPlaceholderText("Min")
        self.split_label = QLabel("-")
        self.sleep_range_max = QLineEdit()
        self.sleep_range_max.setPlaceholderText("Max")

        # make sure the values are integers
        self.sleep_range_min.setValidator(QtGui.QIntValidator())
        self.sleep_range_max.setValidator(QtGui.QIntValidator())

        qhbox.addWidget(self.sleep_range_label)
        qhbox.addWidget(self.sleep_range_min)
        qhbox.addWidget(self.split_label)
        qhbox.addWidget(self.sleep_range_max)
        
        options_layout.addLayout(qhbox2)
        options_layout.addLayout(qhbox)
        options_layout.addLayout(qhbox3)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_button1 = HoverButton("Start")
        self.start_button1.setObjectName("startButton")
        self.start_button1.setHoverStyle(
            "background-color: #45a049; color: white;")
        self.stop_button1 = HoverButton("Stop")
        self.stop_button1.setObjectName("stopButton")
        self.stop_button1.setStyleSheet("background-color: gray; color: white;")
        self.stop_button1.setHoverStyle(
            "background-color: #e53935; color: white;")
        self.stop_button1.setDisabled(True)

        self.start_button1.clicked.connect(self.on_start_button1_clicked)
        self.stop_button1.clicked.connect(self.on_stop_button1_clicked)

        button_layout.addWidget(self.start_button1)
        button_layout.addWidget(self.stop_button1)

        layout.addWidget(self.table1)
        layout.addLayout(options_layout)
        layout.addLayout(button_layout)

        self.tab1.setLayout(layout)

    def initTab2(self):
        layout = QVBoxLayout()

        # Table
        self.table2 = QTableWidget()
        self.table2.setRowCount(0)
        self.table2.setColumnCount(5)
        self.table2.setHorizontalHeaderLabels(
            ["Choice", "Wallet", "Amount Buy", "Amount Sell", "Status"])
        self.table2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table2.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.table2.setColumnWidth(0, 100)

        # Context Menu
        self.table2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table2.customContextMenuRequested.connect(self.contextMenuEvent2)

        # File Selection
        file_layout = QHBoxLayout()
        file_label = QLabel("File Selection:")
        self.file_line_edit2 = QLineEdit()
        self.file_button2 = HoverButton("Open File")
        self.file_button2.setObjectName("fileButton")
        self.file_button2.setHoverStyle("background-color: #1B5E20; color: white;")
        # not editable
        self.file_line_edit2.setReadOnly(True)
        self.file_button2.clicked.connect(lambda: self.openFile(self.file_line_edit2))
        self.file_line_edit2.textChanged.connect(lambda: self.on_file_line_edit_changed(self.table2, self.file_line_edit2.text(), 2))

        token_layout = QHBoxLayout()
        token_label = QLabel("Token contract:")
        self.token_line_edit = QLineEdit()
        self.token_line_edit.setPlaceholderText("Token contract")
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_line_edit)


        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_line_edit2)
        file_layout.addWidget(self.file_button2)

        qhbox = QHBoxLayout()
        self.sleep_range_label_2 = QLabel("Sleep Range:")
        self.sleep_range_min_2 = QLineEdit()
        self.sleep_range_min_2.setPlaceholderText("Min")
        self.split_label_2 = QLabel("-")
        self.sleep_range_max_2 = QLineEdit()
        self.sleep_range_max_2.setPlaceholderText("Max")

        # make sure the values are integers
        self.sleep_range_min_2.setValidator(QtGui.QIntValidator())
        self.sleep_range_max_2.setValidator(QtGui.QIntValidator())

        qhbox.addWidget(self.sleep_range_label_2)
        qhbox.addWidget(self.sleep_range_min_2)
        qhbox.addWidget(self.split_label_2)
        qhbox.addWidget(self.sleep_range_max_2)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_button2 = HoverButton("Start")
        self.start_button2.setObjectName("startButton")
        self.start_button2.setHoverStyle("background-color: #45a049; color: white;")
        self.refresh_button2 = HoverButton("Refresh")
        self.refresh_button2.setObjectName("refreshButton")
        self.refresh_button2.setHoverStyle(
            "background-color: #FDD835; color: black;")
        
        self.stop_button2 = HoverButton("Stop")
        self.stop_button2.setObjectName("stopButton")
        self.stop_button2.setStyleSheet("background-color: gray; color: white;")
        self.stop_button2.setHoverStyle(
            "background-color: #e53935; color: white;")
        self.stop_button2.setDisabled(True)
        
        self.start_button2.clicked.connect(self.on_start_button2_clicked)
        self.stop_button2.clicked.connect(self.on_stop_button2_clicked)

        button_layout.addWidget(self.start_button2)
        button_layout.addWidget(self.stop_button2)

        layout.addWidget(self.table2)
        layout.addLayout(file_layout)
        layout.addLayout(qhbox)
        layout.addLayout(token_layout)
        layout.addLayout(button_layout)

        self.tab2.setLayout(layout)

    @QtCore.pyqtSlot()
    def on_tab_changed(self):
        if self.tabs.currentIndex() == 0:
            pass
        elif self.tabs.currentIndex() == 1:
            pass
        elif self.tabs.currentIndex() == 2:
            pass


    def initTab3(self):
        layout = QVBoxLayout()
        self.table3 = QTableWidget()
        self.table3.setRowCount(0)
        headers = ["Choice", "Device", "Status"]
        self.table3.setColumnCount(len(headers))
        self.table3.setHorizontalHeaderLabels(headers)
        self.table3.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table3.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.table3.setColumnWidth(0, 100)

        self.table3.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table3.customContextMenuRequested.connect(self.contextMenuEvent3)

        self.on_refresh_button3_clicked()

        # Script Selection
        script_layout = QHBoxLayout()
        script_label = QLabel("Script Selection:")
        self.script_line_edit = QLineEdit()
        script_button = HoverButton("Open File")
        script_button.setObjectName("fileButton")
        script_button.setHoverStyle("background-color: #1B5E20; color: white;")
        script_button.clicked.connect(self.openScriptFile)

        script_layout.addWidget(script_label)
        script_layout.addWidget(self.script_line_edit)
        script_layout.addWidget(script_button)

        # ComboBox
        self.combo_box = QComboBox()
        self.on_tab3_clicked()

        # Buttons
        button_layout = QHBoxLayout()
        self.action_button = HoverButton("Push Script")
        self.action_button.setObjectName("actionButton")
        self.action_button.setHoverStyle("background-color: #45a049; color: white;")
        self.delete_button = HoverButton("Delete All Scripts")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setHoverStyle("background-color: #e53935; color: white;")
        self.refresh_button3 = HoverButton("Refresh")
        self.refresh_button3.setObjectName("refreshButton")
        self.refresh_button3.setHoverStyle(
            "background-color: #FDD835; color: black;")

        self.action_button.clicked.connect(self.on_action_button_clicked)
        self.delete_button.clicked.connect(self.on_delete_button_clicked)
        self.refresh_button3.clicked.connect(self.on_refresh_button3_clicked)

        button_layout.addWidget(self.action_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button3)

        layout.addWidget(self.table3)
        layout.addLayout(script_layout)
        layout.addWidget(self.combo_box)
        layout.addLayout(button_layout)

        self.tab3.setLayout(layout)


    def openFile(self, line_edit):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "CSV Files (*.csv)")
        if file_name:
            line_edit.setText(file_name)

    def create_error_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(title)
        msg.setInformativeText(message)
        msg.setWindowTitle("Error")
        msg.exec_()

    def on_file_line_edit_changed(self, table, data_path, from_tab):
        if not data_path:
            return
        
        table.setRowCount(0)

        if from_tab == 1:
            try:
                df = pd.read_csv(data_path)
                private_keys = df['PRIVATE_KEY'].tolist()
                amounts = df['AMOUNT_IN_SOL'].tolist()
                table.setRowCount(len(private_keys))
                for i, (private_key, amount) in enumerate(zip(private_keys, amounts)):
                    check_box = QCheckBox()
                    check_box.setChecked(True)
                    amount = format(amount, CONFIG.DEFAULT_FORMAT)
                    table.setCellWidget(i, 0, check_box)
                    table.setItem(i, 1, QTableWidgetItem(private_key))
                    table.setItem(i, 2, QTableWidgetItem(str(amount)))
                    table.setItem(i, 3, QTableWidgetItem("Idle"))
            except Exception as e:
                # create a message box
                table.setRowCount(0)
                self.create_error_message("Error", str(e))
            

        elif from_tab == 2:
            try:
                df = pd.read_csv(data_path)
                private_keys = df['PRIVATE_KEY'].tolist()
                amounts_buy = df['AMOUNT_BUY'].tolist()
                amounts_sell = df['AMOUNT_SELL'].tolist()
                table.setRowCount(len(private_keys))
                for i, (private_key, amount_buy, amount_sell) in enumerate(zip(private_keys, amounts_buy, amounts_sell)):
                    check_box = QCheckBox()
                    check_box.setChecked(True)
                    table.setCellWidget(i, 0, check_box)
                    table.setItem(i, 1, QTableWidgetItem(private_key))
                    table.setItem(i, 2, QTableWidgetItem(str(amount_buy)))
                    table.setItem(i, 3, QTableWidgetItem(str(amount_sell)))
                    table.setItem(i, 4, QTableWidgetItem("Idle"))
            except Exception as e:
                # create a message box
                table.setRowCount(0)
                self.create_error_message("Error", str(e))


    def applyStyles(self):
        style = """
        QTabWidget::pane { 
            border: 1px solid lightgray; 
            background: #f2f2f2; 
        }
        QTabBar::tab {
            background: #e0e0e0; 
            border: 1px solid lightgray; 
            padding: 10px; 
        }
       
        QTabBar::tab:selected {
            background: #d0d0d0; 
        }
        QTableWidget {
            gridline-color: lightgray; 
        }
        QHeaderView::section {
            background: #e0e0e0; 
            padding: 5px; 
            border: 1px solid lightgray; 
        }
        QPushButton {
            border: none; 
            padding: 10px 20px; 
            text-align: center; 
            text-decoration: none; 
            font-size: 14px; 
            margin: 4px 2px; 
            border-radius: 5px; 
        }
        QPushButton#startButton {
            background-color: #4CAF50; 
            color: white; 
        }
        QPushButton#stopButton {
            background-color: #f44336; 
            color: white; 
        }
        QPushButton#refreshButton {
            background-color: #FFEB3B; 
            color: black; 
        }
        QPushButton#fileButton {
            background-color: #2E7D32; 
            color: white; 
        }
        QPushButton#actionButton {
            background-color: #4CAF50; 
            color: white; 
        }
        QPushButton#deleteButton {
            background-color: #f44336; 
            color: white; 
        }
        QLabel {
            font-size: 14px; 
        }
        QLineEdit {
            padding: 5px; 
            border: 1px solid lightgray; 
            border-radius: 3px; 
        }
        QComboBox {
            padding: 5px; 
            border: 1px solid lightgray; 
            border-radius: 3px; 
        }
        """
        self.setStyleSheet(style)


    def _on_error(self, error, from_tab):
        if from_tab == 1:
            self.create_error_message("Error", error)
            self.on_stop_button1_clicked()
        elif from_tab == 2:
            self.create_error_message("Error", error)
            self.on_stop_button2_clicked()


    def disable_button_1(self):
        self.start_button1.setDisabled(True)
        self.start_button1.setStyleSheet(
            "background-color: gray; color: white;")
        
        self.stop_button1.setDisabled(False)
        self.stop_button1.setStyleSheet(
            "background-color: #f44336; color: white;")
    
    def enable_button_1(self):
        self.start_button1.setDisabled(False)
        self.start_button1.setStyleSheet(
            "background-color: #4CAF50; color: white;")

        self.stop_button1.setDisabled(True)
        self.stop_button1.setStyleSheet(
            "background-color: gray; color: white;")

    @QtCore.pyqtSlot()
    def on_start_button1_clicked(self):
        self.disable_button_1()
        list_info_private_key = []

        for i in range(self.table1.rowCount()):
            check_box = self.table1.cellWidget(i, 0)
            if check_box.isChecked():
                wallet = self.table1.item(i, 1).text()
                amount = self.table1.item(i, 2).text()
                list_info_private_key.append((wallet, amount))

        main_private_key = self.main_wallet_line_edit.text()
        sleep_range_min = self.sleep_range_min.text()
        sleep_range_max = self.sleep_range_max.text()

        if not main_private_key:
            self.create_error_message("Error", "Main Wallet is empty")
            self.enable_button_1()
            return
        
        if not sleep_range_min or not sleep_range_max:
            self.create_error_message("Error", "Sleep Range is empty")
            self.enable_button_1()
            return
        
        if int(sleep_range_min) > int(sleep_range_max):
            self.create_error_message("Error", "Sleep Range is invalid")
            self.enable_button_1()
            return
        
        self.worker_transfer = Worker_Transfer(
            list_info_private_key, main_private_key, sleep_range_min, sleep_range_max, self.update_table1, self.error_signal)
        self.worker_transfer.update_table_1.connect(self.update_status_table_1)
        self.worker_transfer.error_signal.connect(self._on_error)
        self.worker_transfer.finished.connect(self.on_stop_button1_clicked)
        self.worker_transfer.start()

    def update_status_table_1(self, private_key: str, status: str):
        for i in range(self.table1.rowCount()):
            if self.table1.item(i, 1).text() == private_key:
                self.table1.item(i, 3).setText(status)

    
    @QtCore.pyqtSlot()
    def on_stop_button1_clicked(self):
        self.enable_button_1()
        self.worker_transfer.terminate()

    # Tab 2


    def disable_button_2(self):
        self.start_button2.setDisabled(True)
        self.start_button2.setStyleSheet(
            "background-color: gray; color: white;")
        
        self.stop_button2.setDisabled(False)
        self.stop_button2.setStyleSheet(
            "background-color: #f44336; color: white;")
    
    def enable_button_2(self):
        self.start_button2.setDisabled(False)
        self.start_button2.setStyleSheet(
            "background-color: #4CAF50; color: white;")

        self.stop_button2.setDisabled(True)
        self.stop_button2.setStyleSheet(
            "background-color: gray; color: white;")

    @QtCore.pyqtSlot()
    def on_start_button2_clicked(self):
        self.disable_button_2()
        list_info_private_key = []

        for i in range(self.table2.rowCount()):
            check_box = self.table2.cellWidget(i, 0)
            if check_box.isChecked():
                wallet = self.table2.item(i, 1).text()
                amount_buy = self.table2.item(i, 2).text()
                amount_sell = self.table2.item(i, 3).text()
                list_info_private_key.append((wallet, amount_buy, amount_sell))

        token_contract = self.token_line_edit.text()
        sleep_range_min = self.sleep_range_min_2.text()
        sleep_range_max = self.sleep_range_max_2.text()

        if not token_contract:
            self.create_error_message("Error", "Token Contract is empty")
            self.enable_button_2()
            return
        
        if not sleep_range_min or not sleep_range_max:
            self.create_error_message("Error", "Sleep Range is empty")
            self.enable_button_2()
            return
        
        if int(sleep_range_min) > int(sleep_range_max):
            self.create_error_message("Error", "Sleep Range is invalid")
            self.enable_button_2()
            return
        
        self.worker_swap = Worker_RaydiumSwap(
            list_info_private_key, token_contract, sleep_range_min, sleep_range_max, self.update_table2, self.error_signal)
        
        self.worker_swap.update_table_2.connect(self.update_status_table_2)
        self.worker_swap.error_signal.connect(self._on_error)
        self.worker_swap.finished.connect(self.on_stop_button2_clicked)
        self.worker_swap.start()

    def update_status_table_2(self, private_key: str, status: str):
        for i in range(self.table2.rowCount()):
            if self.table2.item(i, 1).text() == private_key:
                self.table2.item(i, 4).setText(status)
    
    @QtCore.pyqtSlot()
    def on_stop_button2_clicked(self):
        self.enable_button_2()
        self.worker_swap.stop_now()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
