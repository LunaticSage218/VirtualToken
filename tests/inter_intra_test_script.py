import itertools
import hashlib
import secrets
import struct
import csv

import numpy as np
import pandas as pd
from NFT.utils import derive_key_from_file

# --- CONFIG ---
PASSWORD      = "password123456"
FILE_SIZE     = 500 * 1024    # 500 KiB
NUM_INTER     = 10            # how many random inputs for inter-test
NUM_INTRA     = 10            # how many runs for intra-test
ROWS, COLS    = 256, 256

# --- HELPERS ---

def generate_address_table_fixed(r1: bytes = None, rows: int = ROWS, cols: int = COLS):
    """
    Duplicate of your generate_address_table but with injectable r1.
    """
    if r1 is None:
        r1 = secrets.token_bytes(32)
    elif len(r1) != 32:
        raise ValueError("r1 must be exactly 32 bytes")

    shake = hashlib.shake_256()
    shake.update(r1)
    digest_len = rows * cols * 2
    msg_digest = shake.digest(digest_len)

    adds_struct = struct.Struct(f'>{rows*cols}H')
    adds = adds_struct.unpack(msg_digest)

    addresses = [((w // rows) % cols, w % rows) for w in adds]
    table = np.array(addresses, dtype=np.int64).reshape(rows, cols, 2)
    return r1, table


def select_bytes_from_tables(address_table: np.ndarray, crypto_table: bytes) -> bytes:
    """
    Given your address_table and crypto_table, pull out one byte per (x,y).
    """
    flat = address_table.reshape(-1, 2)
    return bytes(crypto_table[x * COLS + y] for x, y in flat)


def difference_pct(a: bytes, b: bytes) -> float:
    """
    Compute the percentage of differing bytes between two selections.
    """
    arr = np.frombuffer(a, dtype=np.uint8) != np.frombuffer(b, dtype=np.uint8)
    return float(arr.sum()) / arr.size * 100.0

# --- PREPARE RANDOM INPUTS FOR INTER TEST ---
random_inputs = [secrets.token_bytes(FILE_SIZE) for _ in range(NUM_INTER)]

# --- INTER TEST ---
def run_inter_test():
    """
    INTER TEST:
    - Purpose: Verify variability when using *different* random inputs (files) but the *same* address-table seed (r1).
    - Expectation: High % differences if crypto_table truly depends on file contents.
    """
    fixed_r1, addr_table = generate_address_table_fixed(r1=None)

    # Derive and select for each random input
    results = []
    for data in random_inputs:
        crypto = derive_key_from_file(data, PASSWORD)
        sel = select_bytes_from_tables(addr_table, crypto)
        results.append(sel)

    # Compute pairwise difference percentages
    pairs = list(itertools.combinations(range(len(results)), 2))
    records = []
    for i, j in pairs:
        pct = difference_pct(results[i], results[j])
        records.append({'run1': i, 'run2': j, 'diff_pct': pct})

    df = pd.DataFrame(records)
    print("\n=== Inter-test Results ===")
    print("(Different inputs, same R1)")
    print(df.to_string(index=False, float_format='%.2f'))
    print("\nSummary stats:")
    print(df['diff_pct'].describe().to_string())
    df.to_csv('inter_test_results.csv', index=False)
    print("Saved inter-test results to 'inter_test_results.csv'\n")

# --- INTRA TEST ---
def run_intra_test():
    """
    INTRA TEST:
    - Purpose: Verify variability when using the *same* random input (file) but *different* address-table seeds (r1) each run.
    - Expectation: High % differences if address mapping truly reorders bytes.
    """
    data = random_inputs[0]
    crypto = derive_key_from_file(data, PASSWORD)

    selections = []
    for _ in range(NUM_INTRA):
        _, addr_tab = generate_address_table_fixed(r1=None)
        sel = select_bytes_from_tables(addr_tab, crypto)
        selections.append(sel)

    # Compute pairwise difference percentages
    pairs = list(itertools.combinations(range(len(selections)), 2))
    records = []
    for i, j in pairs:
        pct = difference_pct(selections[i], selections[j])
        records.append({'run1': i, 'run2': j, 'diff_pct': pct})

    df = pd.DataFrame(records)
    print("\n=== Intra-test Results ===")
    print("(Same input, different R1)")
    print(df.to_string(index=False, float_format='%.2f'))
    print("\nSummary stats:")
    print(df['diff_pct'].describe().to_string())
    df.to_csv('intra_test_results.csv', index=False)
    print("Saved intra-test results to 'intra_test_results.csv'\n")

if __name__ == "__main__":
    run_inter_test()
    run_intra_test()