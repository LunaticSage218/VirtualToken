from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AppState:
    file_info: Optional[Dict[str, Any]] = None
    usb_path: Optional[str] = None
    storage_password: Optional[str] = None
    decrypted_path: Optional[str] = None
    decrypted_desc: Optional[str] = None
    last_action: Optional[str] = None  # 'enroll' | 'decrypt' | 'nft'

    def clear(self):
        self.file_info = None
        self.usb_path = None
        self.storage_password = None
        self.decrypted_path = None
        self.decrypted_desc = None
        self.last_action = None