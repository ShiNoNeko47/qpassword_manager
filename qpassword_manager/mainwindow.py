import sys
import logging
import base64
import requests
from Crypto.Hash import SHA256
from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton
from PyQt5.Qt import Qt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from qpassword_manager.managepasswordswindow import ManagePasswordsWindow
from qpassword_manager.displaypasswordswindow import DisplayPasswordsWindow
from qpassword_manager.setupwindow import SetupWindow
from qpassword_manager.messagebox import MessageBox
from qpassword_manager.conf.connectorconfig import Config
from qpassword_manager.conf.settings import Settings


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.key_input_hashed = None

        self.setWindowTitle("qpassword_manager")
        self.setFixedHeight(250)
        self.setFixedWidth(600)

        self.layout = QGridLayout()

        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.check_input)
        self.name_input.setPlaceholderText("Username")
        self.layout.addWidget(self.name_input, 0, 0, 1, 3)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.textChanged.connect(self.check_input)
        self.key_input.setPlaceholderText("Master key")
        self.layout.addWidget(self.key_input, 1, 0, 1, 3)

        self.display_passwords_btn = QPushButton("Display passwords")
        self.display_passwords_btn.setEnabled(False)
        self.display_passwords_btn.clicked.connect(self.display_passwords)
        self.layout.addWidget(self.display_passwords_btn, 2, 0, 1, 3)

        self.manage_passwords_btn = QPushButton("Manage passwords")
        self.manage_passwords_btn.setEnabled(False)
        self.manage_passwords_btn.clicked.connect(self.manage_passwords)
        self.layout.addWidget(self.manage_passwords_btn, 3, 0, 1, 3)

        self.newUser_btn = QPushButton("New user")
        self.newUser_btn.clicked.connect(self.new_user)
        self.layout.addWidget(self.newUser_btn, 4, 1)

        self.setLayout(self.layout)

        self.w_display = DisplayPasswordsWindow(self.display_passwords_btn)
        self.w_manage = ManagePasswordsWindow(
            self.w_display, self.manage_passwords_btn
        )
        self.w_setup = SetupWindow(self)

        self.settings = Settings()
        self.messagebox = MessageBox(self, "Wrong username or password!")

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            self.display_passwords_btn.click()

        if e.key() == Qt.Key_Escape:
            self.settings.show()

    def check_input(self):
        self.manage_passwords_btn.setEnabled(False)
        self.display_passwords_btn.setEnabled(False)
        if len(self.key_input.text()) >= 4 and len(self.name_input.text()) > 0:
            self.manage_passwords_btn.setEnabled(True)
            self.display_passwords_btn.setEnabled(True)

    def check_key(self):
        self.key_input_hashed = SHA256.new(self.key_input.text().encode())
        user_id = requests.post(
            Config.config()["host"],
            {"action": "get_id"},
            auth=(
                self.name_input.text(),
                self.key_input_hashed.hexdigest(),
            ),
        ).text
        logging.debug(self.name_input.text())
        logging.debug(self.key_input_hashed.hexdigest())
        logging.debug(user_id)
        if user_id:
            return True

        self.messagebox.show()

    def manage_passwords(self):
        if self.check_key():
            self.w_manage.auth = (
                self.name_input.text(),
                self.key_input_hashed.hexdigest(),
            )
            self.w_manage.set_key(self.get_key())

            self.w_display.auth = (
                self.name_input.text(),
                self.key_input_hashed.hexdigest(),
            )
            self.w_display.set_key(self.get_key())

            self.w_manage.create_table()
            self.w_manage.show()

            self.manage_passwords_btn.setDisabled(True)

    def display_passwords(self):
        if self.check_key():
            self.w_display.auth = (
                self.name_input.text(),
                self.key_input_hashed.hexdigest(),
            )
            self.w_display.set_key(self.get_key())
            self.w_display.create_table()
            self.w_display.show()

            self.display_passwords_btn.setDisabled(True)

    def new_user(self):
        self.w_setup.show()

    def get_key(self):
        password = self.key_input.text().encode()
        salt = b"sw\xea\x01\x9d\x109\x0eF\xef/\n\xb0mWK"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
            length=32,
            salt=salt,
            iterations=10000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password))

    def closeEvent(self, event):
        if all([self.w_manage.isHidden(), self.w_display.isHidden()]):
            event.accept()
            sys.exit()
        else:
            event.ignore()
