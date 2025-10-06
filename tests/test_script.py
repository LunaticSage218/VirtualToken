import argparse
import csv
import os
import tempfile
import time
import tracemalloc
from pathlib import Path

import psutil

# Import the protocol functions
from NFT.utils import (
    derive_key_from_file,
    generate_address_table,
    generate_ephemeral_key,
)

def generate_dummy_file(path: Path, size: int):
    """Create a file of exactly `size` random bytes at `path`."""
    with path.open("wb") as f:
        f.write(os.urandom(size))

def benchmark(func, *args, **kwargs):
    """
    Run func(*args, **kwargs) and measure:
      - real elapsed time (s)
      - CPU time (user+sys, s)
      - peak Python allocation (tracemalloc, bytes)
      - RSS memory delta (bytes)
    Returns (real_time, cpu_time, peak_alloc, rss_delta, result).
    """
    proc = psutil.Process(os.getpid())

    # Snapshot before
    cpu_before = sum(proc.cpu_times()[:2])
    rss_before = proc.memory_info().rss

    tracemalloc.start()
    start = time.perf_counter()
    result = func(*args, **kwargs)
    real_time = time.perf_counter() - start
    peak, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Snapshot after
    cpu_after = sum(proc.cpu_times()[:2])
    rss_after = proc.memory_info().rss

    cpu_time = cpu_after - cpu_before
    rss_delta = rss_after - rss_before

    return real_time, cpu_time, peak, rss_delta, result

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark the NFT protocol (derive_key, address_table, ephemeral_key)."
    )
    parser.add_argument(
        "--file-sizes",
        type=int,
        nargs="+",
        default=[1024, 10*1024, 100*1024, 500*1024, 1000*1024,
                 5000*1024, 10000*1024, 50000*1024],
        help="File sizes in bytes to test."
    )
    parser.add_argument(
        "--crypto-lengths",
        type=int,
        nargs="+",
        default=[256*1000, 512*1000, 1024*1000],
        help="Output lengths (bytes) for derive_key_from_file."
    )
    parser.add_argument(
        "--rows-cols",
        type=int,
        nargs=2,
        default=[256, 256],
        metavar=("ROWS", "COLS"),
        help="Address table dimensions."
    )
    parser.add_argument(
        "--key-lengths",
        type=int,
        nargs="+",
        default=[32],
        help="Ephemeral key lengths in bytes."
    )
    parser.add_argument(
        "--password",
        type=str,
        default="benchmark123456",
        help="Password to pass to derive_key_from_file."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1000,
        help="How many times to repeat each configuration."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark_results.csv"),
        help="CSV file to append results to."
    )
    args = parser.parse_args()

    # Ensure output CSV has header
    write_header = not args.output.exists()
    with args.output.open("a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow([
                "file_size", "crypto_length", "rows", "cols",
                "key_length", "run",
                "t_derive(s)", "cpu_derive(s)", "mem_peak_derive(bytes)", "rss_delta_derive(bytes)",
                "t_addr(s)",   "cpu_addr(s)",   "mem_peak_addr(bytes)",   "rss_delta_addr(bytes)",
                "t_eph(s)",    "cpu_eph(s)",    "mem_peak_eph(bytes)",    "rss_delta_eph(bytes)",
                "t_total(s)",
            ])

        rows, cols = args.rows_cols

        for file_size in args.file_sizes:
            for crypto_len in args.crypto_lengths:
                for run_idx in range(1, args.runs + 1):
                    # 1) Create a fresh dummy file
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp_path = Path(tmp.name)
                    generate_dummy_file(tmp_path, file_size)

                    # 2) derive_key_from_file
                    t1, cpu1, peak1, rss1, crypto_table = benchmark(
                        derive_key_from_file,
                        tmp_path,
                        args.password,
                        crypto_len
                    )

                    # 3) generate_address_table
                    t2, cpu2, peak2, rss2, (_, addr_table) = benchmark(
                        generate_address_table,
                        rows,
                        cols
                    )

                    # 4) generate_ephemeral_key
                    t3, cpu3, peak3, rss3, _ = benchmark(
                        generate_ephemeral_key,
                        addr_table,
                        crypto_table,
                        args.key_lengths[0]
                    )

                    # 5) Compute total protocol time
                    t_total = t1 + t2 + t3

                    # 6) Record results
                    writer.writerow([
                        file_size, crypto_len, rows, cols,
                        args.key_lengths[0], run_idx,
                        f"{t1:.6f}", f"{cpu1:.6f}", peak1, rss1,
                        f"{t2:.6f}", f"{cpu2:.6f}", peak2, rss2,
                        f"{t3:.6f}", f"{cpu3:.6f}", peak3, rss3,
                        f"{t_total:.6f}",
                    ])

                    # 7) Delete the dummy file
                    tmp_path.unlink()

    print(f"Benchmark complete — results appended to {args.output}")


if __name__ == "__main__":
    main()
