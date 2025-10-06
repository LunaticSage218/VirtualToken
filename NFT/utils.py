import hashlib
import secrets
import struct
import numpy as np
from pathlib import Path
from typing import Union, Tuple

def derive_key_from_file(
    file_input: Union[str, Path, bytes],
    password: str,
    output_length: int = 1000 * 512  # Default length in bytes (500 KB)
) -> bytes:
    """
    Derive a symmetric key (crypto table) by:
      1. SHA-256 hashing the file contents or provided bytes → 32-byte digest.
      2. SHA-256 hashing the UTF-8 password → 32-byte digest.
      3. Seeding SHAKE-256 with both digests and squeezing out `output_length` bytes.
    """
    # 1) Compute the 32-byte SHA-256 digest of the file or data
    file_sha = hashlib.sha256()
    total_len = 0
    if isinstance(file_input, (bytes, bytearray)):
        file_sha.update(file_input)
        total_len = len(file_input)
        print(f"[derive_key_from_file] Hashed {total_len} bytes of provided data.")
    else:
        path = Path(file_input)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_input}")
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                file_sha.update(chunk)
                total_len += len(chunk)
        print(f"[derive_key_from_file] Hashed {total_len} bytes from file: {file_input}")
    file_digest = file_sha.digest()
    print(f"[derive_key_from_file] SHA256(file): {file_digest.hex()}")

    # 2) Hash the password to 32-byte digest
    pwd_bytes = password.encode("utf-8")
    pwd_digest = hashlib.sha256(pwd_bytes).digest()
    print(f"[derive_key_from_file] SHA256(password): {pwd_digest.hex()}")

    # 3) Use SHAKE-256 with both digests to generate the key bytes
    shake = hashlib.shake_256()
    shake.update(file_digest)
    shake.update(pwd_digest)
    key = shake.digest(output_length)
    print(f"[derive_key_from_file] Derived key length: {len(key)} bytes.")
    print(f"[derive_key_from_file] First 32 bytes: {key[:32].hex()}")

    return key

def generate_address_table(
    rows: int = 256,
    cols: int = 256,
    seed: bytes = None
) -> Tuple[bytes, np.ndarray]:
    """
    Generate a deterministic 2D address table from a 32-byte random seed (R1).
    Each entry of the table is a tuple (x, y) computed from SHAKE-256(seed).
    Returns:
        R1 (bytes): The 32-byte seed used.
        table (np.ndarray): Array of shape (rows, cols, 2) of address coordinates.
    """
    # 1) Draw or use provided R1
    if seed is not None:
        r1 = seed
    else:
        r1 = secrets.token_bytes(32)
    print(f"[generate_address_table] R1 (hex): {r1.hex()}")

    # 2) SHAKE-256(R1) to produce rows*cols*2 bytes
    shake = hashlib.shake_256()
    shake.update(r1)
    digest_len = rows * cols * 2  # number of bytes needed for 16-bit words
    msg_digest = shake.digest(digest_len)
    print(f"[generate_address_table] SHAKE output length: {len(msg_digest)} bytes.")

    # 3) Unpack into 16-bit unsigned integers
    adds_struct = struct.Struct(f'>{rows*cols}H')
    adds = adds_struct.unpack(msg_digest)
    print(f"[generate_address_table] Unpacked {len(adds)} words (first two: {adds[0]}, {adds[1]}).")

    # 4) Map each 16-bit word to (x, y) coordinates in [0, rows-1]x[0, cols-1]
    addresses = [((w // rows) % cols, w % rows) for w in adds]

    # 5) Reshape to a 256x256x2 array
    table = np.array(addresses, dtype=np.int64).reshape(rows, cols, 2)
    print(f"[generate_address_table] Final table shape: {table.shape}")
    print(f"[generate_address_table] First 2 addresses:\n {table[:1, :2]}")
    return r1, table

def generate_ephemeral_key(
    address_table: np.ndarray,
    crypto_table: bytes,
    key_length: int
) -> Tuple[bytes, bytes]:
    """
    (Original NFT protocol) Generate an ephemeral key from:
      - a new 32-byte random number R2,
      - the crypto_table (bytes),
      - and the 256×256 address_table.
    Not used in combined protocol (kept for reference).
    """
    rows, cols, _ = address_table.shape
    n = len(crypto_table)
    print(f"[generate_ephemeral_key] Address table shape: {rows}×{cols}")
    print(f"[generate_ephemeral_key] crypto_table length: {n} bytes (must be ≥ {rows*cols}).")

    # 1) draw R2
    r2 = secrets.token_bytes(32)
    print(f"[generate_address_table] R2 (hex): {r2.hex()}")

    # 2) select one byte per (x,y) from crypto_table
    flat = address_table.reshape(-1, 2)
    selected = bytearray(len(flat))
    for i, (x, y) in enumerate(flat):
        idx = x * cols + y
        if idx >= n:
            raise IndexError(f"Address index {idx} out of range for crypto_table")
        selected[i] = crypto_table[idx]
    print(f"[generate_ephemeral_key] Selected bytes length: {len(selected)}")
    print(f"[generate_ephemeral_key] First 16 selected bytes: {selected[:16].hex()}")

    # 3) SHAKE-256(R2 || selected_bytes) to derive key_length bytes
    xof = hashlib.shake_256()
    xof.update(r2 + selected)
    ephemeral_key = xof.digest(key_length)
    print(f"[generate_ephemeral_key] Ephemeral key length: {len(ephemeral_key)} bytes")
    print(f"[generate_ephemeral_key] First 32 bytes of key: {ephemeral_key[:32].hex()}")

    return r2, ephemeral_key
