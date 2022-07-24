"""The window used for copying passwords from database"""

import logging
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
)
from cryptography.fernet import Fernet
import pyperclip
from qpassword_manager.database.database_handler import DatabaseHandler


class DisplayPasswordsWindow(QWidget):
    """
    The window used for copying passwords from database

    Attributes:
        fernet: Fernet object used for decryption
        btn: display_passwords_btn on MainWindow
    """

    def __init__(self, btn):
        super().__init__()

        self.fernet = None
        self.btn = btn

        self.setWindowTitle("Passwords")
        self.layout = QGridLayout()

        self.table = QTableWidget()
        # self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.itemClicked.connect(self.copy_selected)
        self.layout.addWidget(self.table, 0, 0)

        self.setFixedWidth(640)
        self.setLayout(self.layout)

        self.data = None

    def set_key(self, key):
        """
        Creates Fernet object using a key

        Parameters:
            key: key used for creating a Fernet object
        """

        self.fernet = Fernet(key)

    def create_table(self):
        """Updates data in the table"""

        self.table.clear()
        self.table.setColumnCount(3)
        self.table.setRowCount(0)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.table.setHorizontalHeaderLabels(
            ["Website", "Username", "Password"]
        )
        self.data = DatabaseHandler.create_table(self.auth)
        logging.debug(self.data)

        for i in range(3):
            self.table.setColumnWidth(i, 190)
        self.table.setColumnWidth(3, 30)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for i, row in enumerate(self.data):
            self.table.insertRow(i)
            for j in range(2):
                self.table.setItem(i, j, (QTableWidgetItem(row[j])))
            row = "*" * len(self.fernet.decrypt(row[2].encode()))
            self.table.setItem(i, 2, (QTableWidgetItem(row)))

    def copy_selected(self):
        """Copy selected item in table"""

        if self.table.selectedIndexes()[0].column() != 2:
            logging.debug(self.table.selectedItems()[0].text())
            pyperclip.copy(self.table.selectedItems()[0].text())
        else:
            pyperclip.copy(self.fernet.decrypt(
                self.data[self.table.selectedIndexes()[0].row()][2].encode()).decode())
        self.table.clearSelection()

    def closeEvent(self, event):  # pylint: disable=invalid-name
        """Enables display_passwords_btn in MainWindow"""

        self.btn.setDisabled(False)
        logging.debug(event)
