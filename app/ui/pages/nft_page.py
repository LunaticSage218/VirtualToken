from __future__ import annotations

from typing import Optional
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)

from app.objects.state import AppState
from app.workers.nft import NFTWorker

class NFTPage(QWidget):
    request_prev = pyqtSignal()
    request_restart = pyqtSignal()
    request_log = pyqtSignal(str, str)

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.thread: Optional[QThread] = None
        self.worker: Optional[NFTWorker] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("<h2>3. Generate NFT Key</h2>")
        layout.addWidget(title)

        desc = QLabel(
            "<b>What happens?</b><br>"
            "• Derive a crypto table from your decrypted file & password.<br>"
            "• Generate an address table and combine it to produce an ephemeral key.<br>"
            "• Receive a unique, one‑time NFT key (hex‑encoded)."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        form = QFormLayout()
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw.setPlaceholderText("Choose a secure password")
        form.addRow("NFT Password", self.pw)
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.gen_btn = QPushButton("Generate NFT Key")
        self.gen_btn.clicked.connect(self._on_generate_clicked)
        self.restart_btn = QPushButton("Restart Protocol")
        self.restart_btn.clicked.connect(lambda: self.request_restart.emit())
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(lambda: self.request_prev.emit())
        btns.addWidget(self.gen_btn)
        btns.addWidget(self.restart_btn)
        btns.addWidget(self.back_btn)
        btns.addStretch(1)
        layout.addLayout(btns)
        layout.addStretch(1)

    def _on_generate_clicked(self):
        if not self.state.decrypted_path:
            QMessageBox.critical(self, "Not Ready", "Decrypt the file first.")
            return
        password = self.pw.text().strip()
        if not password:
            QMessageBox.warning(self, "Missing Password", "Please enter a password for NFT key derivation.")
            return

        self.gen_btn.setEnabled(False)

        self.thread = QThread(self)
        self.worker = NFTWorker(self.state.decrypted_path, password)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.request_log.emit)
        self.worker.finished.connect(self._nft_finished)
        self.worker.failed.connect(self._nft_failed)
        self.worker.finished.connect(lambda _res: self._cleanup())
        self.worker.failed.connect(lambda _err: self._cleanup())

        self.thread.start()

    def _nft_finished(self, res: dict):
        if res.get("success"):
            self.state.last_action = "nft"
        self.gen_btn.setEnabled(True)

    def _nft_failed(self, _err: str):
        self.gen_btn.setEnabled(True)

    def _cleanup(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            self.worker = None