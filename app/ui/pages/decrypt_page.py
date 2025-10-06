from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QMessageBox
)

from app.objects.state import AppState
from app.workers.decrypt import DecryptWorker

class DecryptPage(QWidget):
    request_prev = pyqtSignal()
    request_next = pyqtSignal()
    request_log = pyqtSignal(str, str)

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.thread: Optional[QThread] = None
        self.worker: Optional[DecryptWorker] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("<h2>2. Decrypt &amp; Verify</h2>")
        layout.addWidget(title)

        desc = QLabel(
            "<b>What happens?</b><br>"
            "• Retrieve and decode stored keys (Kc, Kr, hash) from your USB drive.<br>"
            "• Run the verification protocol to recover the ephemeral key.<br>"
            "• Decrypt the file and check its integrity.<br>"
            "• Save the decrypted file locally and reveal the description."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btns = QHBoxLayout()
        self.decrypt_btn = QPushButton("Decrypt & Verify")
        self.decrypt_btn.clicked.connect(self._on_decrypt_clicked)
        self.next_btn = QPushButton("Next: NFT Key")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(lambda: self.request_next.emit())
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(lambda: self.request_prev.emit())
        btns.addWidget(self.decrypt_btn)
        btns.addWidget(self.next_btn)
        btns.addWidget(self.back_btn)
        btns.addStretch(1)
        layout.addLayout(btns)
        layout.addStretch(1)

    def _on_decrypt_clicked(self):
        if not self.state.file_info:
            QMessageBox.critical(self, "No Enrolled File", "No enrolled file is available in state.")
            return

        self.decrypt_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

        self.thread = QThread(self)
        self.worker = DecryptWorker(self.state.file_info, self.state.usb_path, self.state.storage_password)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.request_log.emit)
        self.worker.finished.connect(self._decrypt_finished)
        self.worker.failed.connect(self._decrypt_failed)
        self.worker.finished.connect(lambda _res: self._cleanup())
        self.worker.failed.connect(lambda _err: self._cleanup())

        self.thread.start()

    def _decrypt_finished(self, res: dict):
        if res.get("success"):
            self.state.decrypted_path = res.get("decrypted_path")
            self.state.decrypted_desc = res.get("decrypted_desc")
            self.state.last_action = "decrypt"
            self.next_btn.setEnabled(True)
        else:
            self.decrypt_btn.setEnabled(True)

    def _decrypt_failed(self, _err: str):
        self.decrypt_btn.setEnabled(True)

    def _cleanup(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            self.worker = None