from __future__ import annotations

import shutil
import time
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal

# External protocols (match your Flask imports)
from DataEncap.enrollment.enrollment import enrollment_protocol

from app.objects.utils import secure_filename
from app.objects.paths import UPLOAD_DIR

class EnrollmentWorker(QObject):
    progress = pyqtSignal(str, str)   # message, category
    finished = pyqtSignal(dict)       # result dict
    failed = pyqtSignal(str)

    def __init__(self, src_path: Path, description: str,
                 usb_path: Optional[str], storage_password: Optional[str]):
        super().__init__()
        self.src_path = src_path
        self.description = description or ""
        self.usb_path = usb_path or None
        self.storage_password = storage_password or None

    def run(self):
        try:
            filename = secure_filename(self.src_path.name)
            dst = UPLOAD_DIR / filename
            if dst.resolve() != self.src_path.resolve():
                shutil.copy2(self.src_path, dst)

            ext = dst.suffix
            filepath = str(dst)

            self.progress.emit(f"ℹ️ [Enrollment] Starting enrollment at {time.strftime('%H:%M:%S')}…", "info")
            self.progress.emit("   • Generating ephemeral key and hashing", "info")
            self.progress.emit("   • Encrypting file content", "info")
            self.progress.emit("   • Encrypting description and serializing keys", "info")

            start = time.time()
            success, file_info, msg = enrollment_protocol(
                filepath, filename, self.description, ext,
                external_path=self.usb_path, external_pw=self.storage_password
            )
            duration = time.time() - start

            if not success:
                self.progress.emit(f"❌ Enrollment failed: {msg}", "error")
                self.finished.emit({"success": False, "message": msg, "duration": duration})
                return

            info_dict: Dict[str, Any] = getattr(file_info, "__dict__", None) or dict(file_info)
            self.progress.emit(f"✅ Enrollment completed in {duration:.2f}s!", "success")
            self.progress.emit(f"   • Stored encrypted file: {info_dict.get('file_path', 'N/A')}", "info")
            if self.usb_path and self.storage_password:
                self.progress.emit("   • Kc, Kr, H(file) encrypted and saved to USB", "info")
            else:
                self.progress.emit("   • Kc, Kr, H(file) encoded and stored locally", "info")

            self.finished.emit({
                "success": True,
                "file_info": info_dict,
                "usb_path": self.usb_path,
                "storage_password": self.storage_password,
                "duration": duration,
            })

        except Exception as e:
            err = f"Enrollment exception: {e}\n{traceback.format_exc()}"
            self.progress.emit(f"❌ {err}", "error")
            self.failed.emit(err)