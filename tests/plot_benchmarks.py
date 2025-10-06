import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def parse_size(hr: str) -> float:
    """
    Convert a human-readable size (e.g. '1.0 MB') back to bytes for sorting.
    """
    num, unit = hr.split()
    mapping = {'bytes': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    return float(num) * mapping[unit]

def make_line_chart(df, metric, outfname):
    """
    Plot `metric` vs file_size_hr for each crypto_length_hr.
    Saves figure to `outfname`.
    """
    # sort categories
    file_sizes = sorted(df['file_size_hr'].unique(), key=parse_size)
    x = np.arange(len(file_sizes))
    plt.figure(figsize=(6, 4))
    for length in sorted(df['crypto_length_hr'].unique(), key=parse_size):
        sub = df[df['crypto_length_hr'] == length].set_index('file_size_hr').loc[file_sizes]
        plt.plot(x, sub[metric], marker='o', label=length)
    plt.xticks(x, file_sizes, rotation=45)
    plt.xlabel('File Size')
    plt.ylabel(metric.replace('_', ' '))
    plt.title(metric.replace('_', ' '))
    plt.legend(title='Crypto Length', loc='best')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outfname, dpi=300)
    plt.close()

def main():
    # 1) Load summary
    df = pd.read_csv('benchmark_summary.csv')
    # 2) Add numeric sizes for ordering
    df['file_size_bytes']   = df['file_size_hr'].apply(parse_size)
    df['crypto_length_bytes'] = df['crypto_length_hr'].apply(parse_size)

    # 3) List of metrics you care about
    time_metrics   = ['t_derive(s)', 't_addr(s)', 't_eph(s)', 't_total(s)']
    mem_metrics    = ['mem_peak_derive(bytes)', 'mem_peak_addr(bytes)', 'mem_peak_eph(bytes)']
    rss_metrics    = ['rss_delta_derive(bytes)', 'rss_delta_addr(bytes)', 'rss_delta_eph(bytes)']

    # 4) Generate one chart per metric
    for m in time_metrics:
        make_line_chart(df, m,   f'chart_{m}.png')
    for m in mem_metrics:
        make_line_chart(df, m,   f'chart_{m}.png')
    for m in rss_metrics:
        make_line_chart(df, m,   f'chart_{m}.png')

    print("Charts saved as chart_<metric>.png in the current directory.")

if __name__ == '__main__':
    main()