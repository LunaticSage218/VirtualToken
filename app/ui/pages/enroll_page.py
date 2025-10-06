from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QPushButton,
    QPlainTextEdit, QHBoxLayout, QFileDialog, QMessageBox
)

from app.objects.state import AppState
from app.workers.enrollment import EnrollmentWorker

class EnrollPage(QWidget):
    completed = pyqtSignal(dict)
    request_next = pyqtSignal()
    request_log = pyqtSignal(str, str)

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.thread: Optional[QThread] = None
        self.worker: Optional[EnrollmentWorker] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("<h2>1. Encrypt &amp; Enroll</h2>")
        layout.addWidget(title)

        desc = QLabel(
            "<b>What happens?</b><br>"
            "• Generate a cryptographically secure ephemeral key.<br>"
            "• Hash that key (for integrity checks).<br>"
            "• Encrypt your file with AES‑256‑CBC.<br>"
            "• Encrypt your description and serialize keys (Kc, Kr, hash).<br>"
            "Encrypted data is stored locally. Keys and file hash can be encrypted with your password and written to a USB drive."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        form = QFormLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Choose a file to enroll")
        self.file_btn = QPushButton("Browse…")
        self.file_btn.clicked.connect(self._choose_file)
        file_row = QHBoxLayout()
        file_row.addWidget(self.file_edit)
        file_row.addWidget(self.file_btn)
        form.addRow("Choose File", self._wrap(file_row))

        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setPlaceholderText("Brief summary of your file")
        self.desc_edit.setFixedHeight(60)
        form.addRow("Description", self.desc_edit)

        self.usb_edit = QLineEdit()
        self.usb_edit.setPlaceholderText("e.g. /Volumes/MyUSB or /mnt/usbdrive")
        self.usb_btn = QPushButton("Browse…")
        self.usb_btn.clicked.connect(self._choose_usb)
        usb_row = QHBoxLayout()
        usb_row.addWidget(self.usb_edit)
        usb_row.addWidget(self.usb_btn)
        form.addRow("USB Storage Path (optional)", self._wrap(usb_row))

        self.store_pw = QLineEdit()
        self.store_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.store_pw.setPlaceholderText("Password to encrypt keys file")
        form.addRow("Storage Password (optional)", self.store_pw)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.enroll_btn = QPushButton("Encrypt & Enroll")
        self.enroll_btn.clicked.connect(self._on_enroll_clicked)
        self.next_btn = QPushButton("Next: Decrypt")
        self.next_btn.clicked.connect(lambda: self.request_next.emit())
        self.next_btn.setEnabled(False)
        btns.addWidget(self.enroll_btn)
        btns.addWidget(self.next_btn)
        btns.addStretch(1)
        layout.addLayout(btns)
        layout.addStretch(1)

    @staticmethod
    def _wrap(inner_layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(inner_layout)
        return w

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose File to Encrypt")
        if path:
            self.file_edit.setText(path)

    def _choose_usb(self):
        path = QFileDialog.getExistingDirectory(self, "Select USB / External Directory")
        if path:
            self.usb_edit.setText(path)

    def _on_enroll_clicked(self):
        src = self.file_edit.text().strip()
        if not src:
            QMessageBox.warning(self, "Missing File", "Please choose a file to enroll.")
            return
        p = Path(src)
        if not p.exists():
            QMessageBox.critical(self, "Invalid Path", "Selected file does not exist.")
            return

        description = self.desc_edit.toPlainText().strip()
        usb_path = self.usb_edit.text().strip() or None
        storage_pw = self.store_pw.text().strip() or None

        self.enroll_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

        self.thread = QThread(self)
        self.worker = EnrollmentWorker(p, description, usb_path, storage_pw)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.request_log.emit)
        self.worker.finished.connect(self._enroll_finished)
        self.worker.failed.connect(self._enroll_failed)
        self.worker.finished.connect(lambda _res: self._cleanup())
        self.worker.failed.connect(lambda _err: self._cleanup())

        self.thread.start()

    def _enroll_finished(self, res: dict):
        if res.get("success"):
            self.state.file_info = res.get("file_info")
            self.state.usb_path = res.get("usb_path")
            self.state.storage_password = res.get("storage_password")
            self.state.last_action = "enroll"
            self.next_btn.setEnabled(True)
        else:
            self.enroll_btn.setEnabled(True)

    def _enroll_failed(self, _err: str):
        self.enroll_btn.setEnabled(True)

    def _cleanup(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            self.worker = None