from __future__ import annotations

import json
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QProgressBar,
    QStackedWidget, QMessageBox, QPushButton
)

from app.objects.state import AppState
from app.objects.paths import APP_TITLE, UPLOAD_DIR, ROOT_DIR
from app.objects.utils import open_folder
from app.widgets.console import ConsoleWidget
from app.ui.pages.enroll_page import EnrollPage
from app.ui.pages.decrypt_page import DecryptPage
from app.ui.pages.nft_page import NFTPage

# State file location
STATE_FILE = ROOT_DIR / "enrollment_state.json"


class ModeSelectionPage(QWidget):
    """Initial page where user selects Enroll or Decrypt mode"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        title = QLabel("<h2>Select Operation Mode</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)
        
        desc = QLabel(
            "<p>Choose what you'd like to do:</p>"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(desc)
        
        layout.addStretch(1)
        
        # Enroll section
        enroll_box = QWidget()
        enroll_box.setStyleSheet("""
            QWidget {
                background: rgba(40, 167, 69, 0.1);
                border: 2px solid #28a745;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        enroll_layout = QVBoxLayout(enroll_box)
        
        enroll_title = QLabel("<h3>🔒 Enroll New File</h3>")
        enroll_layout.addWidget(enroll_title)
        
        enroll_desc = QLabel(
            "Encrypt a file and generate keys.<br>"
            "Use this when you want to secure a new file."
        )
        enroll_desc.setWordWrap(True)
        enroll_layout.addWidget(enroll_desc)
        
        self.enroll_btn = QPushButton("Start Enrollment")
        self.enroll_btn.setMinimumHeight(40)
        enroll_layout.addWidget(self.enroll_btn)
        
        layout.addWidget(enroll_box)
        
        # Decrypt section
        decrypt_box = QWidget()
        decrypt_box.setStyleSheet("""
            QWidget {
                background: rgba(13, 202, 240, 0.1);
                border: 2px solid #0dcaf0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        decrypt_layout = QVBoxLayout(decrypt_box)
        
        decrypt_title = QLabel("<h3>🔓 Decrypt & Generate NFT</h3>")
        decrypt_layout.addWidget(decrypt_title)
        
        decrypt_desc = QLabel(
            "Load a previously enrolled file to decrypt it<br>"
            "and generate an NFT key."
        )
        decrypt_desc.setWordWrap(True)
        decrypt_layout.addWidget(decrypt_desc)
        
        self.decrypt_btn = QPushButton("Start Decrypt & NFT")
        self.decrypt_btn.setMinimumHeight(40)
        decrypt_layout.addWidget(self.decrypt_btn)
        
        layout.addWidget(decrypt_box)
        
        layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(960, 680)
        self.state = AppState()
        self.current_mode = None  # 'enroll' or 'decrypt'

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        header = QLabel('<h1 style="margin:0;">DataEncap + NFT Portal</h1>')
        header.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(header)
        root.addWidget(self._hr())

        self.progress = QProgressBar()
        self.progress.setRange(1, 3)
        self.progress.setValue(1)
        self.progress.setFormat("Step %v of %m")
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.console = ConsoleWidget()
        root.addWidget(self.console)

        root.addWidget(self._hr())
        footer = QLabel('<span style="color:#6c757d;">© 2025 Work In Progress.</span>')
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(footer)

        # Pages
        self.mode_page = ModeSelectionPage()
        self.enroll_page = EnrollPage(self.state)
        self.decrypt_page = DecryptPage(self.state)
        self.nft_page = NFTPage(self.state)

        # Wire mode selection signals
        self.mode_page.enroll_btn.clicked.connect(self._start_enroll_mode)
        self.mode_page.decrypt_btn.clicked.connect(self._start_decrypt_mode)

        # Wire enroll page signals
        self.enroll_page.request_log.connect(self.console.log)
        # Override the next button to save state
        self.enroll_page.next_btn.clicked.disconnect()
        self.enroll_page.next_btn.clicked.connect(self._save_enrollment_state)

        # Wire decrypt page signals
        self.decrypt_page.request_prev.connect(lambda: self.goto_step(1))
        self.decrypt_page.request_next.connect(lambda: self.goto_step(2))
        self.decrypt_page.request_log.connect(self.console.log)

        # Wire NFT page signals
        self.nft_page.request_prev.connect(lambda: self.goto_step(1))
        self.nft_page.request_restart.connect(self._return_to_mode_selection)
        self.nft_page.request_log.connect(self.console.log)

        self.stack.addWidget(self.mode_page)    # index 0
        self.stack.addWidget(self.enroll_page)  # index 1
        self.stack.addWidget(self.decrypt_page) # index 2
        self.stack.addWidget(self.nft_page)     # index 3

        self._build_menu()

    def _build_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")

        act_mode = QAction("Return to Mode Selection", self)
        act_mode.triggered.connect(self._return_to_mode_selection)
        file_menu.addAction(act_mode)

        file_menu.addSeparator()

        act_open = QAction("Open Uploads Folder…", self)
        act_open.triggered.connect(lambda: open_folder(UPLOAD_DIR))
        file_menu.addAction(act_open)

        act_clear = QAction("Clear Console", self)
        act_clear.triggered.connect(self.console.clear_console)
        file_menu.addAction(act_clear)

        file_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

    def _hr(self) -> QWidget:
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background:#333;")
        return line

    def _start_enroll_mode(self):
        """Start enrollment workflow"""
        self.current_mode = 'enroll'
        self.progress.setVisible(True)
        self.progress.setRange(1, 1)
        self.progress.setValue(1)
        self.progress.setFormat("Enrollment")
        self.stack.setCurrentWidget(self.enroll_page)
        self.console.log("🔒 Enrollment mode activated", "info")

    def _start_decrypt_mode(self):
        """Start decrypt + NFT workflow"""
        # Try to load enrollment state
        if not STATE_FILE.exists():
            QMessageBox.warning(
                self,
                "No Enrollment State",
                f"No enrollment state file found:\n{STATE_FILE}\n\n"
                f"Please complete enrollment first."
            )
            self.console.log(f"❌ State file not found: {STATE_FILE}", "error")
            return

        try:
            with open(STATE_FILE, 'r') as f:
                state_data = json.load(f)

            # Load state
            self.state.file_info = state_data.get("file_info")
            self.state.usb_path = state_data.get("usb_path")
            self.state.storage_password = state_data.get("storage_password")
            self.state.last_action = state_data.get("last_action")

            if not self.state.file_info:
                raise ValueError("Invalid state file: missing file_info")

            self.current_mode = 'decrypt'
            self.progress.setVisible(True)
            self.progress.setRange(1, 2)
            self.progress.setValue(1)
            self.progress.setFormat("Step %v of %m")
            self.stack.setCurrentWidget(self.decrypt_page)
            
            self.console.log("✅ Enrollment state loaded successfully!", "success")
            self.console.log(f"   • File: {self.state.file_info.get('filename', 'N/A')}", "info")
            if self.state.usb_path:
                self.console.log(f"   • USB path: {self.state.usb_path}", "info")
            self.console.log("🔓 Decrypt & NFT mode activated", "info")

        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "Invalid State File",
                f"Failed to parse enrollment state file:\n{e}"
            )
            self.console.log(f"❌ Invalid JSON in state file: {e}", "error")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load enrollment state:\n{e}"
            )
            self.console.log(f"❌ Error loading state: {e}", "error")

    def _save_enrollment_state(self):
        """Save enrollment state and show completion message"""
        if not self.state.file_info:
            QMessageBox.warning(
                self,
                "No Enrollment",
                "Please complete enrollment first."
            )
            return

        try:
            # Prepare state data for JSON serialization
            state_data = {
                "file_info": self.state.file_info,
                "usb_path": self.state.usb_path,
                "storage_password": self.state.storage_password,
                "last_action": self.state.last_action
            }

            # Save to file
            with open(STATE_FILE, 'w') as f:
                json.dump(state_data, f, indent=2)

            self.console.log(f"💾 Enrollment state saved to: {STATE_FILE}", "success")
            self.console.log("✅ Enrollment complete! You can now:", "success")
            self.console.log("   • Return to mode selection to decrypt later", "info")
            self.console.log("   • Close the app and decrypt anytime", "info")

            QMessageBox.information(
                self,
                "Enrollment Complete",
                f"Enrollment successful!\n\n"
                f"State saved to: {STATE_FILE}\n\n"
                f"You can now:\n"
                f"• Return to mode selection and choose 'Decrypt & NFT'\n"
                f"• Close the app and decrypt later"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save enrollment state:\n{e}"
            )
            self.console.log(f"❌ Error saving state: {e}", "error")

    def goto_step(self, n: int):
        """Navigate between decrypt steps"""
        if self.current_mode == 'decrypt':
            n = max(1, min(2, n))
            self.progress.setValue(n)
            if n == 1:
                self.stack.setCurrentWidget(self.decrypt_page)
            elif n == 2:
                self.stack.setCurrentWidget(self.nft_page)

    def _return_to_mode_selection(self):
        """Clear state and return to mode selection"""
        reply = QMessageBox.question(
            self,
            "Return to Mode Selection?",
            "This will clear the current session data.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.state.clear()
            self.current_mode = None
            self.progress.setVisible(False)
            self.stack.setCurrentWidget(self.mode_page)
            self.console.log("🔄 Returned to mode selection", "info")

    def closeEvent(self, event):
        # Safety: ensure threads are not left running
        super().closeEvent(event)