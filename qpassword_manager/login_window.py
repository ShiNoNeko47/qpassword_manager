"""Login window"""

import os
import logging
import base64
import json
from xdg.BaseDirectory import xdg_config_home
from Crypto.Hash import SHA256
from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton
from PyQt5.Qt import Qt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from qpassword_manager.main_window import MainWindow
from qpassword_manager.setup_window import SetupWindow
from qpassword_manager.database.database_handler import DatabaseHandler
from qpassword_manager.conf.settings import Settings
from qpassword_manager.conf.connectorconfig import Config


class LoginWindow(QWidget):
    """
    Login window

    Attributes:
        key_input_hashed: hashed master key used for authentication
    """

    def __init__(self) -> None:
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

        self.login_btn = QPushButton("Login")
        self.login_btn.setEnabled(False)
        self.login_btn.clicked.connect(self.login)
        self.layout.addWidget(self.login_btn, 2, 0, 1, 3)

        self.new_user_btn = QPushButton("New user")
        self.new_user_btn.clicked.connect(self.new_user)
        self.layout.addWidget(self.new_user_btn, 4, 1)

        self.setLayout(self.layout)

        self.w_main = None
        self.w_setup = None

        self.database_handler = DatabaseHandler(Config.config())
        self.settings = Settings(self)
        self.autofill()

    def autofill(self) -> None:
        """Fills in credentials defined in autofill.json"""

        try:
            with open(
                os.path.join(
                    xdg_config_home, "qpassword_manager", "autofill.json"
                ),
                "r",
                encoding="utf8",
            ) as file:
                autofill = json.loads(file.read())

            self.name_input.setText(autofill["Username"])
            self.key_input.setText(autofill["Password"])

            if autofill["Username"]:
                self.key_input.setFocus()
        except FileNotFoundError as error:
            with open(
                os.path.join(
                    xdg_config_home, "qpassword_manager", "autofill.json"
                ),
                "w+",
                encoding="utf8",
            ) as file:
                file.write('{"Username": "", "Password": ""}')
            logging.debug(error)

    def load_config(self) -> None:
        """Loads config from file to DatabaseHandler object"""

        self.database_handler.config = Config.config()

    def keyPressEvent(self, event) -> None:  # pylint: disable=invalid-name
        """Opens MainWindow when you press enter or Settings when
        you press escape"""

        if event.key() == Qt.Key_Return:
            self.login_btn.click()

        if event.key() == Qt.Key_Escape:
            self.settings.show()

    def check_input(self) -> None:
        """Checks if name isn't empty and key is longer or equal to 4 and
        enables or disables buttons"""

        self.login_btn.setEnabled(False)
        if len(self.key_input.text()) >= 4 and len(self.name_input.text()) > 0:
            self.login_btn.setEnabled(True)

    def check_key(self) -> bool:
        """Checks if name and master key pair is correct"""

        self.key_input_hashed = SHA256.new(self.key_input.text().encode())
        credentials_match = self.database_handler.check_credentials(
            self.name_input.text(), self.key_input_hashed.hexdigest()
        )

        logging.debug(self.name_input.text())
        logging.debug(self.key_input_hashed.hexdigest())
        logging.debug(credentials_match)

        return credentials_match

    def login(self) -> None:
        """opens MainWindow if check_key returns True"""

        if self.check_key():
            self.w_main = MainWindow(self)
            self.w_main.show()

            self.key_input.setText("")
            self.key_input.setFocus()
            self.hide()

    def new_user(self) -> None:
        """Opens SetupWindow"""

        self.w_setup = SetupWindow(self)
        self.w_setup.show()

    def get_key(self) -> bytes:
        """Creates key for Fernet using plain text master key"""

        password = self.key_input.text().encode()
        salt = b"sw\xea\x01\x9d\x109\x0eF\xef/\n\xb0mWK"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=10000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
