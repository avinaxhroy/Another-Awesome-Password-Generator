import sys
import os
import random
import string
import winreg
import keyboard  # pip install keyboard
from win10toast import ToastNotifier  # pip install win10toast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QSlider,
    QCheckBox,
    QPushButton,
    QStatusBar,
    QProgressBar,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
    QMessageBox  # Import for error message
)


class SmartphonePasswordGenerator(QMainWindow):
    # Custom signal to trigger password generation from the global hotkey
    trigger_global_generate = Signal()

    def __init__(self):
        super().__init__()
        # Set fixed size to simulate a smartphone (360x640)
        self.setFixedSize(360, 640)
        self.setWindowTitle("Password Generator")

        # Determine the application's base path
        self.base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))

        # Load the icon
        icon_path = os.path.join(self.base_path, 'appicon.ico')
        try:
            self.setWindowIcon(QIcon(icon_path))
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Error loading icon: {e}")
            # Fallback icon if 'appicon.ico' is not found
            self.setWindowIcon(QIcon())  # Set a default empty icon
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon())

        # Create a Windows toast notifier
        self.toaster = ToastNotifier()

        # Store password history
        self.password_history = []

        # Connect our custom signal to generate_password (for the global hotkey)
        self.trigger_global_generate.connect(self.generate_password)

        # Main layout setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Heading (smaller font)
        self.title_label = QLabel("PASSWORD GENERATOR")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(self.title_label)

        # Display frame for password with pink-to-purple gradient
        self.display_frame = QFrame()
        self.display_frame.setObjectName("displayFrame")
        self.display_frame.setFixedHeight(50)
        disp_layout = QHBoxLayout(self.display_frame)
        disp_layout.setContentsMargins(10, 5, 10, 5)
        disp_layout.setSpacing(10)

        self.password_edit = QLineEdit()
        self.password_edit.setReadOnly(True)
        self.password_edit.setObjectName("passwordEdit")
        self.password_edit.setPlaceholderText("Generate a password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setFixedHeight(40)
        self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        disp_layout.addWidget(self.password_edit)

        # Toggle button for show/hide using emoji icons
        self.btn_toggle = QPushButton("🙂")
        self.btn_toggle.setObjectName("toggleButton")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setToolTip("Show Password")
        self.btn_toggle.setFixedSize(40, 40)
        self.btn_toggle.setFont(QFont("Segoe UI Emoji", 18))
        self.btn_toggle.clicked.connect(self.toggle_password_visibility)
        disp_layout.addWidget(self.btn_toggle)

        main_layout.addWidget(self.display_frame)

        # Strength Progress Bar (green gradient)
        self.strength_bar = QProgressBar()
        self.strength_bar.setObjectName("strengthBar")
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(12)
        self.strength_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.strength_bar)

        # Slider for password length
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(4, 32)
        self.slider.setValue(12)
        self.slider.valueChanged.connect(self.update_length_label)
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.slider)

        self.length_label = QLabel("Length: 12")
        self.length_label.setObjectName("lengthLabel")
        self.length_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.length_label)

        # Options: Checkboxes arranged in rows (2 per row)
        self.chk_letters = QCheckBox("Letters")
        self.chk_letters.setObjectName("optionCheck")
        self.chk_letters.setChecked(True)
        self.chk_digits = QCheckBox("Digits")
        self.chk_digits.setObjectName("optionCheck")
        self.chk_digits.setChecked(True)
        self.chk_symbols = QCheckBox("Symbols")
        self.chk_symbols.setObjectName("optionCheck")
        self.chk_symbols.setChecked(True)
        self.chk_mixed = QCheckBox("Mixed")
        self.chk_mixed.setObjectName("optionCheck")
        self.chk_mixed.setChecked(True)
        self.chk_custom = QCheckBox("Custom")
        self.chk_custom.setObjectName("optionCheck")
        self.chk_custom.setChecked(False)
        self.chk_custom.toggled.connect(self.toggle_custom_chars)

        options_vlayout = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(self.chk_letters)
        row1.addWidget(self.chk_digits)
        options_vlayout.addLayout(row1)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(self.chk_symbols)
        row2.addWidget(self.chk_mixed)
        options_vlayout.addLayout(row2)
        row3 = QHBoxLayout()
        row3.setSpacing(10)
        row3.addWidget(self.chk_custom)
        options_vlayout.addLayout(row3)
        main_layout.addLayout(options_vlayout)

        # Custom Characters Input (hidden by default)
        self.custom_chars_edit = QLineEdit()
        self.custom_chars_edit.setPlaceholderText("Enter custom chars")
        self.custom_chars_edit.setObjectName("customCharsEdit")
        self.custom_chars_edit.setVisible(False)
        self.custom_chars_edit.setFixedHeight(30)
        main_layout.addWidget(self.custom_chars_edit)

        # Buttons: Generate, Copy, History (emoji-only)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_generate = QPushButton("🔄")
        self.btn_generate.setObjectName("generateButton")
        self.btn_generate.setToolTip("Generate Password")
        self.btn_generate.clicked.connect(self.generate_password)
        self.btn_generate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_generate.setFont(QFont("Segoe UI Emoji", 18))
        btn_layout.addWidget(self.btn_generate)

        self.btn_copy = QPushButton("📋")
        self.btn_copy.setObjectName("copyButton")
        self.btn_copy.setToolTip("Copy Password")
        self.btn_copy.clicked.connect(self.copy_password)
        self.btn_copy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_copy.setFont(QFont("Segoe UI Emoji", 18))
        btn_layout.addWidget(self.btn_copy)

        self.btn_history = QPushButton("📅")
        self.btn_history.setObjectName("historyButton")
        self.btn_history.setToolTip("View History")
        self.btn_history.clicked.connect(self.show_history)
        self.btn_history.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_history.setFont(QFont("Segoe UI Emoji", 18))
        btn_layout.addWidget(self.btn_history)

        main_layout.addLayout(btn_layout)

        # Status Bar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Local shortcut (Ctrl+Shift+F) for generating password
        QShortcut(QKeySequence("Ctrl+Shift+F"), self).activated.connect(
            self.generate_password)
        # Global hotkey: Ctrl+Alt+P triggers generation via our custom signal
        keyboard.add_hotkey("ctrl+alt+p", lambda: self.trigger_global_generate.emit())

        # Create system tray icon so that the app keeps running in background
        self.create_tray_icon()

        # Apply custom style
        self.setStyleSheet(self.vibrant_style())

        # Add to startup
        self.add_to_startup()

        # Generate initial password
        self.generate_password()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        try:
            icon_path = os.path.join(self.base_path, 'appicon.ico')
            self.tray_icon.setIcon(QIcon(icon_path))
        except:
            print("Icon not found for tray icon")

        tray_menu = QMenu(self)
        action_show = QAction("Show", self)
        action_show.triggered.connect(self.show_normal)
        tray_menu.addAction(action_show)
        action_generate = QAction("Generate Password", self)
        action_generate.triggered.connect(self.generate_password)
        tray_menu.addAction(action_generate)
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.exit_app)
        tray_menu.addAction(action_exit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        QApplication.quit()

    def closeEvent(self, event):
        # Minimize to system tray instead of closing the app
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Password Generator",
            "Application minimized to tray and running in background.",
            QSystemTrayIcon.Information,
            2000
        )

    def update_length_label(self):
        val = self.slider.value()
        self.length_label.setText(f"Length: {val}")

    def toggle_custom_chars(self, checked):
        self.custom_chars_edit.setVisible(checked)

    def toggle_password_visibility(self):
        if self.password_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle.setToolTip("Hide Password")
            self.btn_toggle.setText("👁")
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle.setToolTip("Show Password")
            self.btn_toggle.setText("🙈")

    def calculate_strength(self, password):
        score = 0
        length = len(password)
        if length >= 8:
            score += 20
        if length >= 12:
            score += 20
        if any(c.isdigit() for c in password):
            score += 20
        if any(c.isupper() for c in password) and any(c.islower() for c in password):
            score += 20
        if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>/?" for c in password):
            score += 20
        return min(score, 100)

    def generate_password(self):
        length = self.slider.value()
        char_set = ""
        if self.chk_letters.isChecked():
            if self.chk_mixed.isChecked():
                char_set += string.ascii_lowercase + string.ascii_uppercase
            else:
                char_set += string.ascii_lowercase
        if self.chk_digits.isChecked():
            char_set += string.digits
        if self.chk_symbols.isChecked():
            char_set += "!@#$%^&*()-_=+[]{}|;:,.<>/?"
        if self.chk_custom.isChecked():
            custom = self.custom_chars_edit.text()
            if custom:
                char_set += custom
        if not char_set:
            char_set = string.ascii_lowercase
        pwd = "".join(random.choice(char_set) for _ in range(length))
        self.password_edit.setText(pwd)

        if pwd:  # Only copy if password is not empty
            QApplication.clipboard().setText(pwd)
            self.statusbar.showMessage("Password generated and copied!", 3000)
            # Show Windows toast notification
            try:
                self.toaster.show_toast(
                    "Password Generated",
                    "Your new password has been copied to the clipboard!",
                    duration=3,
                    threaded=True
                )
            except Exception as e:
                print(f"Toast notification failed: {e}")
        else:
            self.statusbar.showMessage("Could not generate password!", 3000)

        strength = self.calculate_strength(pwd)
        self.strength_bar.setValue(strength)
        self.password_history.append(pwd)

    def copy_password(self):
        pwd = self.password_edit.text().strip()
        if pwd:
            QApplication.clipboard().setText(pwd)
            self.statusbar.showMessage("Password copied!", 3000)
        else:
            self.statusbar.showMessage("No password to copy.", 3000)

    def show_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Password History")
        dialog.setFixedSize(300, 400)
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        for p in self.password_history:
            item = QListWidgetItem(p)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        btn_clear = QPushButton("Clear History")
        btn_clear.clicked.connect(lambda: self.clear_history(list_widget))
        layout.addWidget(btn_clear)
        dialog.exec()

    def clear_history(self, list_widget):
        self.password_history.clear()
        list_widget.clear()
        self.statusbar.showMessage("History cleared!", 3000)

    def vibrant_style(self):
        return """
        /* Main window background */
        QMainWindow {
            background-color: #FFFFFF;
        }
        /* Title styling */
        QLabel#titleLabel {
            color: #212121;
            font-size: 20px;
            font-family: 'Arial';
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        /* Display frame with pink-to-purple gradient */
        QFrame#displayFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF80AB, stop:1 #9C27B0);
            border: 2px solid #E91E63;
            border-radius: 12px;
        }
        QLineEdit#passwordEdit {
            background-color: transparent;
            color: #212121;
            font-size: 20px;
            border: none;
            padding: 4px;
            min-width: 300px;
        }
        /* Toggle button for show/hide */
        QPushButton#toggleButton {
            background-color: #FFFFFF;
            border: 2px solid #E91E63;
            border-radius: 20px;
        }
        QPushButton#toggleButton:hover {
            background-color: #F8BBD0;
        }
        /* Green progress bar */
        QProgressBar#strengthBar {
            border: 1px solid #BDBDBD;
            border-radius: 8px;
            background-color: #E8F5E9;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:1 #66BB6A);
            border-radius: 8px;
        }
        /* Length label styling */
        QLabel#lengthLabel {
            color: #212121;
            font-size: 16px;
        }
        /* Option toggles */
        QCheckBox#optionCheck {
            background-color: #E8E8E8;
            color: #212121;
            font-size: 14px;
            padding: 6px 10px;
            border-radius: 10px;
            margin: 2px;
        }
        QCheckBox#optionCheck::indicator {
            width: 26px;
            height: 26px;
            border: 2px solid #4CAF50;
            border-radius: 13px;
            background-color: #FFFFFF;
            margin-right: 8px;
        }
        QCheckBox#optionCheck::indicator:checked {
            background-color: #4CAF50;
        }
        /* Custom characters input */
        QLineEdit#customCharsEdit {
            background-color: #FFFFFF;
            color: #212121;
            font-size: 16px;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            padding: 4px;
        }
        /* Buttons: Generate, Copy, History */
        QPushButton#generateButton, QPushButton#copyButton, QPushButton#historyButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #64B5F6);
            border: none;
            border-radius: 10px;
            padding: 10px;
        }
        QPushButton#generateButton:hover, QPushButton#copyButton:hover, QPushButton#historyButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976D2, stop:1 #42A5F5);
        }
        QPushButton#generateButton:pressed, QPushButton#copyButton:pressed, QPushButton#historyButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1565C0, stop:1 #1E88E5);
        }
        /* Status bar styling */
        QStatusBar {
            background-color: #FFFFFF;
            color: #212121;
        }
        /* List widget in history dialog */
        QListWidget {
            background-color: #FFFFFF;
            color: #212121;
            border: 2px solid #BDBDBD;
            border-radius: 8px;
        }
        """

    def add_to_startup(self):
        """Adds this executable to the Windows startup registry for the current user."""
        try:
            # Get executable path
            if getattr(sys, 'frozen', False):
                # If the application is run as a bundle, the pyInstaller bootloader
                # extends the sys module by a flag frozen=True and sets the app
                # path into variable _MEIPASS'.
                exe_path = os.path.abspath(sys.executable)
            else:
                exe_path = os.path.abspath(sys.argv[0])

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "PasswordGenerator", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except Exception as e:
            print("Failed to add to startup:", e)
            QMessageBox.warning(None, "Startup Error", f"Failed to add to startup: {e}")


def main():
    app = QApplication(sys.argv)
    window = SmartphonePasswordGenerator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
