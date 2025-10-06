import pandas as pd
import tabulate


def bytes_to_human(n: int) -> str:
    """
    Convert a byte count to a human-readable string using binary prefixes.
    E.g. 1024 -> '1.0 KB', 1048576 -> '1.0 MB'.
    """
    units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(n)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == 'bytes':
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def main():
    # 1) Load raw data
    df = pd.read_csv('benchmark_results.csv')

    # 2) Human-readable size columns
    df['file_size_hr'] = df['file_size'].apply(bytes_to_human)
    df['crypto_length_hr'] = df['crypto_length'].apply(bytes_to_human)

    # 3) Metrics to average
    metrics = [
        't_derive(s)', 'cpu_derive(s)', 'mem_peak_derive(bytes)', 'rss_delta_derive(bytes)',
        't_addr(s)',   'cpu_addr(s)',   'mem_peak_addr(bytes)',   'rss_delta_addr(bytes)',
        't_eph(s)',    'cpu_eph(s)',    'mem_peak_eph(bytes)',    'rss_delta_eph(bytes)',
        't_total(s)'
    ]

    # 4) Group & compute mean
    summary = (
        df
        .groupby(['file_size_hr', 'crypto_length_hr'])[metrics]
        .mean()
        .reset_index()
    )

    # 5) Save summary
    summary.to_csv('benchmark_summary.csv', index=False)

    # 6) Print outputs with fallback if tabulate missing
    print("Average metrics by file size and crypto table length:\n")
    try:
        print(summary.to_markdown(index=False))
    except ImportError:
        print(summary.to_string(index=False))

if __name__ == '__main__':
    main()