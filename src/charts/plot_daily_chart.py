from pathlib import Path
import matplotlib.pyplot as plt


def plot_daily_chart(df, code: str, name: str, out_path: str):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    axes[0].plot(df["trade_date"], df["close"], label="Close")
    if "white_line" in df.columns:
        axes[0].plot(df["trade_date"], df["white_line"], label="White")
    if "yellow_line" in df.columns:
        axes[0].plot(df["trade_date"], df["yellow_line"], label="Yellow")
    axes[0].set_title(f"{code} {name}")
    axes[0].legend()

    axes[1].bar(df["trade_date"], df["volume"])
    axes[1].set_title("Volume")

    if "j_value" in df.columns:
        axes[2].plot(df["trade_date"], df["j_value"], label="J")
    if "k_value" in df.columns:
        axes[2].plot(df["trade_date"], df["k_value"], label="K")
    if "d_value" in df.columns:
        axes[2].plot(df["trade_date"], df["d_value"], label="D")
    axes[2].legend()
    axes[2].set_title("KDJ")

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close(fig)
