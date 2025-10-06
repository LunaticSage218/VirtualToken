from __future__ import annotations

import time
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal

# External protocols
from DataEncap.verification.verification import verification_protocol

from app.objects.paths import UPLOAD_DIR
from app.objects.utils import secure_filename, unique_path

class DecryptWorker(QObject):
    progress = pyqtSignal(str, str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, file_info: Dict[str, Any],
                 usb_path: Optional[str], storage_password: Optional[str]):
        super().__init__()
        self.file_info = file_info
        self.usb_path = usb_path
        self.storage_password = storage_password

    def run(self):
        try:
            self.progress.emit("ℹ️ [Decryption] Retrieving and decoding keys…", "info")
            self.progress.emit("   • Running verification protocol to reconstruct key", "info")

            start = time.time()
            ns = SimpleNamespace(**self.file_info)
            dec_bytes, dec_desc = verification_protocol(
                ns, external_path=self.usb_path, external_pw=self.storage_password
            )
            duration = time.time() - start

            if dec_bytes is None:
                self.progress.emit("❌ Decryption failed: integrity check or key recovery error.", "error")
                self.finished.emit({"success": False, "duration": duration})
                return

            filename = self.file_info.get("filename", "file")
            decrypted_name = f"decrypted_{secure_filename(filename)}"
            decrypted_path = unique_path(UPLOAD_DIR / decrypted_name)

            with open(decrypted_path, "wb") as f:
                f.write(dec_bytes)

            self.progress.emit(f"✅ Decryption successful in {duration:.2f}s!", "success")
            self.progress.emit(f"   • Decrypted file saved at: {decrypted_path}", "info")
            self.progress.emit(f'   • Decrypted description: "{dec_desc}"', "info")

            self.finished.emit({
                "success": True,
                "decrypted_path": str(decrypted_path),
                "decrypted_desc": dec_desc,
                "duration": duration,
            })

        except Exception as e:
            err = f"Decryption exception: {e}\n{traceback.format_exc()}"
            self.progress.emit(f"❌ {err}", "error")
            self.failed.emit(err)