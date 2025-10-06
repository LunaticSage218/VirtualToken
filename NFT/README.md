# NFT Gen2 Protocol

---

## Prerequisites

- **Python** 3.12.7 or later  
- **Dependencies**  
  - Standard library: `hashlib`, `secrets`, `struct`, `pathlib`, `typing`  
  - Third-party: `numpy`

Install NumPy if you haven’t already:

```bash
pip install numpy
```

---

## Quickstart Example

```python
from utils import (
    derive_key_from_file,
    generate_address_table,
    generate_ephemeral_key,
)

def main():
    # 1) Build the crypto-table from a file + password (default 500 KB)
    crypto_table = derive_key_from_file(
        "tests/sample_pdf.pdf",
        "password123",
    )
    print()

    # 2) Build a 256×256 address table (and log its 32-byte seed R1)
    seed1, addr_table = generate_address_table(rows=256, cols=256)
    print()

    # 3) Derive a 32-byte ephemeral key from the table + crypto-table
    seed2, ephemeral_key = generate_ephemeral_key(
        addr_table,
        crypto_table,
        key_length=32,
    )
    print()
```

---

## Protocol Overview

1. **Crypto-Table Generation**  
   - Read the input file in 8 KiB chunks and absorb into **SHA-256**.  
   - Hash the UTF-8 password with **SHA-256**.  
   - Seed **SHAKE-256** with both 32-byte digests and squeeze out a large pseudo-random buffer (default 1000 × 512 = 512 000 bytes).

2. **256×256 Address Table**  
   - Draw a fresh **32-byte** random seed **R1**.  
   - Run **SHAKE-256(R1)** to produce exactly **256 × 256 × 2 = 131 072** bytes.  
   - Unpack into 65 536 big-endian `uint16` words (`H` = 2 bytes each).  
   - Map each word **w** to  
     ```text
     x = (w // rows) % cols
     y =  w % rows
     ```  
     and reshape into a `(256, 256, 2)` NumPy array of `(x, y)` pairs.

3. **Ephemeral Key Derivation**  
   - Draw a second **32-byte** random seed **R2**.  
   - Flatten the `(x, y)` table to select one byte per coordinate from the crypto-table.  
   - Seed **SHAKE-256** with **R2‖selected_bytes** and squeeze out your one-time key (e.g. 32 bytes).

---

## Function Reference

### `derive_key_from_file(file_path, password, output_length: int = 1000*512) -> bytes`

- **Purpose**  
  Create a large, deterministic pseudo-random buffer from a file and password.

- **Parameters**  
  - `file_path` (`str` | `Path`): path to the input file.  
  - `password` (`str`): user’s secret passphrase.  
  - `output_length` (`int`): number of bytes to output (default 1000 × 512 = 512 000).

- **Returns**  
  - `bytes`: a pseudo-random buffer of length `output_length`.

---

### `generate_address_table(rows: int = 256, cols: int = 256) -> (bytes, np.ndarray)`

- **Purpose**  
  Create a reproducible 2D grid of coordinate pairs from a fresh random seed.

- **Parameters**  
  - `rows`, `cols` (`int`): dimensions of the table (default 256 each).

- **Returns**  
  - `seed1` (`bytes`): the 32-byte seed used for this SHAKE-256 run.  
  - `table` (`np.ndarray` of shape `(rows, cols, 2)`): each `[i, j]` is a tuple `(x, y)` in `[0…cols-1] × [0…rows-1]`.

---

### `generate_ephemeral_key(address_table: np.ndarray, crypto_table: bytes, key_length: int) -> (bytes, bytes)`

- **Purpose**  
  Derive a one-time ephemeral key by mixing a new random seed with bytes pulled via the address table.

- **Parameters**  
  - `address_table` (`np.ndarray (rows, cols, 2)`): coordinate pairs from the previous step.  
  - `crypto_table` (`bytes`): buffer returned by `derive_key_from_file`. Must be at least `rows*cols` bytes.  
  - `key_length` (`int`): desired output key size in bytes.

- **Returns**  
  - `seed2` (`bytes`): the 32-byte seed used for this phase.  
  - `ephemeral_key` (`bytes`): the final one-time key of length `key_length`.

---

## Data Flow Diagram

```text
File + Password
      │
      └─ SHA256(file) → 32 B digest
         SHA256(password) → 32 B digest
            │
            └─ SHAKE-256 → CryptoTable (512 KB)

         R1 (32 B)
            │
            └─ SHAKE-256 → 256×256×2 B
               unpack uint16 → map → AddressTable (256×256×2)

CryptoTable ─┴─ select bytes via AddressTable
      │
      └─ R2 (32 B) ‖ selected_bytes → SHAKE-256 → EphemeralKey (e.g. 32 B)
```
