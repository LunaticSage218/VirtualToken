import pandas as pd
import matplotlib.pyplot as plt

def plot_hist(df: pd.DataFrame, title: str, outfname: str):
    """
    Plot a histogram of the diff_pct column.
    """
    plt.figure(figsize=(6, 4))
    plt.hist(df['diff_pct'], bins=20, edgecolor='black')
    plt.xlabel('Difference Percentage (%)')
    plt.ylabel('Count')
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outfname, dpi=300)
    plt.close()

def plot_box(inter_df: pd.DataFrame, intra_df: pd.DataFrame, outfname: str):
    """
    Plot a boxplot comparing inter- and intra-test diff_pct distributions.
    """
    plt.figure(figsize=(6, 4))
    data = [inter_df['diff_pct'], intra_df['diff_pct']]
    plt.boxplot(data, labels=['Inter-test', 'Intra-test'], showfliers=True)
    plt.ylabel('Difference Percentage (%)')
    plt.title('Inter vs Intra Test: Difference %')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outfname, dpi=300)
    plt.close()

def main():
    # 1) Load your results
    inter = pd.read_csv('inter_test_results.csv')
    intra = pd.read_csv('intra_test_results.csv')

    # 2) Plot and save
    plot_hist(inter, 'Inter-test Difference % Distribution', 'inter_hist.png')
    plot_hist(intra, 'Intra-test Difference % Distribution', 'intra_hist.png')
    plot_box(inter, intra, 'inter_intra_boxplot.png')

    print("✅ Saved:\n • inter_hist.png\n • intra_hist.png\n • inter_intra_boxplot.png")

if __name__ == '__main__':
    main()