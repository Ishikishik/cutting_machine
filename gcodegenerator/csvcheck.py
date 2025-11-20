# csvcheck.py
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# =====================================================
# CSV 読込
# =====================================================
def load_csv_sequence(path):
    xs, ys, cids = [], [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            xs.append(float(r["x"]))
            ys.append(-float(r["y"]))
            cids.append(int(r["curve_id"]))
    return np.array(xs), np.array(ys), np.array(cids)


# =====================================================
# スライダー付き
# =====================================================
def slider_plot_csv(path, show_penup=True):

    xs, ys, cids = load_csv_sequence(path)
    total = len(xs)

    fig, ax = plt.subplots(figsize=(7, 9))
    plt.subplots_adjust(bottom=0.15)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.set_xlim(xs.min(), xs.max())
    ax.set_ylim(ys.min(), ys.max())

    # ---- 線オブジェクトを用意（再生成はしない） ----
    green_line, = ax.plot([], [], color="green", linewidth=2)     # ペンダウン（常に緑）
    penup_color = "pink" if show_penup else "white"               # ペンアップだけ白化
    penup_line, = ax.plot([], [], color=penup_color, linewidth=1)

    # ---- スライダー ----
    slider_ax = fig.add_axes([0.15, 0.03, 0.7, 0.03])
    slider = Slider(slider_ax, "Step", 1, total - 1, valinit=1, valstep=1)

    # ---- 更新 ----
    def update(step):
        step = int(step)

        gx, gy = [], []
        px, py = [], []

        for i in range(1, step):
            x0, y0 = xs[i - 1], ys[i - 1]
            x1, y1 = xs[i], ys[i]

            if cids[i] == cids[i - 1]:
                # ★ 同じ curve_id → 緑（ペンダウン）
                gx += [x0, x1]
                gy += [y0, y1]
            else:
                # ★ 異なる curve_id → ペンアップ
                # show_penup=True → ピンク
                # show_penup=False → 白（不可視）
                px += [x0, x1]
                py += [y0, y1]

        green_line.set_data(gx, gy)
        penup_line.set_data(px, py)

        fig.canvas.draw_idle()

    slider.on_changed(update)
    update(1)
    plt.show()


# =====================================================
# 実行
# =====================================================
if __name__ == "__main__":
    slider_plot_csv(
        "/Users/kawashimasatoshishin/cutting_machine/gcodegenerator/output_curves.csv",
        show_penup=False   # ← ペンアップだけ白になるモード
    )
