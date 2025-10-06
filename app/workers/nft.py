from __future__ import annotations

import time
import traceback
from PyQt6.QtCore import QObject, pyqtSignal

# External protocol
from NFT.protocol import nft_protocol

class NFTWorker(QObject):
    progress = pyqtSignal(str, str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, decrypted_path: str, password: str):
        super().__init__()
        self.decrypted_path = decrypted_path
        self.password = password

    def run(self):
        try:
            self.progress.emit("ℹ️ [NFT] Deriving crypto table from file & password…", "info")
            self.progress.emit("   • Generating address table from random seed R1", "info")
            self.progress.emit("   • Generating ephemeral NFT key from address table & crypto table and a new random seed R2", "info")

            start = time.time()
            key, seed1, seed2 = nft_protocol(self.decrypted_path, self.password)
            duration = time.time() - start

            hex_key = key.hex()
            r1 = seed1.hex()
            r2 = seed2.hex()

            self.progress.emit(f"✅ NFT key generated in {duration:.2f}s!", "success")
            self.progress.emit(f"   • R1 (address table): {r1}", "info")
            self.progress.emit(f"   • R2 (ephemeral key generation): {r2}", "info")
            self.progress.emit(f"   • Ephemeral NFT key (hex): {hex_key}", "info")

            self.finished.emit({
                "success": True,
                "key_hex": hex_key,
                "seed1_hex": r1,
                "seed2_hex": r2,
                "duration": duration,
            })

        except Exception as e:
            err = f"NFT exception: {e}\n{traceback.format_exc()}"
            self.progress.emit(f"❌ {err}", "error")
            self.failed.emit(err)