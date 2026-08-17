"""パレートフロントの世代変化をアニメーションで可視化するツール。"""
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def animate_trajectory(csv_path: str, interval: int = 200) -> None:
    df = pd.read_csv(csv_path)
    generations = sorted(df['generation'].unique())

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlabel('f1')
    ax.set_ylabel('f2')
    ax.set_title(f'Pareto Front Evolution\n{csv_path}')
    scat = ax.scatter([], [], s=20, color='steelblue')

    # 軸範囲を全世代のデータから設定
    margin = 0.05
    x_min, x_max = df['f1'].min(), df['f1'].max()
    y_min, y_max = df['f2'].min(), df['f2'].max()
    x_range = x_max - x_min if x_max != x_min else 1.0
    y_range = y_max - y_min if y_max != y_min else 1.0
    ax.set_xlim(x_min - margin * x_range, x_max + margin * x_range)
    ax.set_ylim(y_min - margin * y_range, y_max + margin * y_range)

    gen_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

    def update(frame: int) -> tuple:
        gen = generations[frame]
        subset = df[df['generation'] == gen]
        scat.set_offsets(subset[['f1', 'f2']].values)
        gen_text.set_text(f'Generation: {gen}')
        return scat, gen_text

    ani = animation.FuncAnimation(
        fig, update, frames=len(generations),
        interval=interval, blit=True, repeat=False
    )
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python graphDrawing.py <trajectory_csv_path> [interval_ms]')
        sys.exit(1)
    csv_path = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    animate_trajectory(csv_path, interval)