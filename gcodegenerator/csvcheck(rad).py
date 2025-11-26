import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# =============================
#  Forward Kinematics
# =============================
def compute_first_link(theta_l_deg, theta_r_deg, l1=65.0, d=50.0):
    tl = np.radians(theta_l_deg)
    tr = np.radians(theta_r_deg)
    M_L = np.array([-d/2, 0.0])
    M_R = np.array([ d/2, 0.0])
    L_tip = np.array([M_L[0] - l1*np.cos(tl), M_L[1] + l1*np.sin(tl)])
    R_tip = np.array([M_R[0] + l1*np.cos(tr), M_R[1] + l1*np.sin(tr)])
    return L_tip, R_tip

def compute_pen_position(L_tip, R_tip, l2=85.0):
    x1, y1 = L_tip
    x2, y2 = R_tip
    d = np.hypot(x2-x1, y2-y1)
    if d > 2*l2 or d < 1e-8: return None
    a = d/2
    h = np.sqrt(l2*l2 - a*a)
    xm = x1 + (x2-x1)*(a/d)
    ym = y1 + (y2-y1)*(a/d)
    rx = -(y2-y1)*(h/d)
    ry =  (x2-x1)*(h/d)
    p1 = np.array([xm + rx, ym + ry])
    p2 = np.array([xm - rx, ym - ry])
    return p1 if p1[1] >= p2[1] else p2

def forward_pen_tip(theta_l_deg, theta_r_deg,
                    l1=65, l2=85, d=50, offset=25):

    L_tip, R_tip = compute_first_link(theta_l_deg, theta_r_deg, l1=l1, d=d)
    if L_tip is None: return (None, None, None, None)

    P = compute_pen_position(L_tip, R_tip, l2=l2)
    if P is None: return (None, None, None, None)

    dir_vec = P - R_tip
    norm = np.hypot(*dir_vec)
    if norm < 1e-6: return (None, None, None, None)

    P_tip = P + (dir_vec / norm) * offset
    return P_tip, P, L_tip, R_tip


# =============================
#  CSV Loader
# =============================
def load_csv_angles(path):
    xs, ys, thLs, thRs, cids = [], [], [], [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            xs.append(float(r["x"]))
            ys.append(float(r["y"]))
            cids.append(int(r["curve_id"]))
            rawL = r["theta_L"].strip()
            rawR = r["theta_R"].strip()
            thLs.append(None if rawL in ("", "None") else float(rawL))
            thRs.append(None if rawR in ("", "None") else float(rawR))
    return xs, ys, thLs, thRs, cids


# =============================
#  Slider Plot
# =============================
def slider_plot_arm_csv(path):
    xs, ys, thLs, thRs, curve_ids = load_csv_angles(path)
    total = len(xs)

    fig, ax = plt.subplots(figsize=(7, 9))
    plt.subplots_adjust(bottom=0.15)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-150, 150)
    ax.set_ylim(-20, 180)

    # ---- 筆跡用ライン（1本だけ） ----
    traj_x = []
    traj_y = []
    traj_line, = ax.plot([], [], color="green", linewidth=2)

    # ---- 腕の描画（毎回再作成） ----
    arm_lines = []

    slider_ax = fig.add_axes([0.15, 0.03, 0.7, 0.03])
    slider = Slider(slider_ax, "Step", 1, total-1, valinit=1, valstep=1)

    def update(step):
        nonlocal arm_lines
        step = int(step)

        # ========================
        # A. 腕を削除
        # ========================
        for line in arm_lines:
            line.remove()
        arm_lines = []

        # ========================
        # B. 筆跡の更新
        # ========================
        traj_x.clear()
        traj_y.clear()

        prev_cid = None
        prev_pt = None

        for i in range(step):
            thL, thR = thLs[i], thRs[i]
            cid = curve_ids[i]

            if thL is None:
                prev_cid = cid
                prev_pt = None
                continue

            P_tip, _, _, _ = forward_pen_tip(thL, thR)
            if P_tip is None:
                prev_cid = cid
                prev_pt = None
                continue

            # ★ ペンダウン
            # ペンダウン（同じ curve_id）
            if prev_pt is not None and cid == prev_cid:
                ax.plot([prev_pt[0], P_tip[0]], [prev_pt[1], P_tip[1]],
                        color="green", linewidth=2)

            # ★ ペンアップ（curve_id が変わった）
            if prev_pt is not None and cid != prev_cid:
                ax.plot([prev_pt[0], P_tip[0]], [prev_pt[1], P_tip[1]],
                        color="white", linewidth=1)


            prev_cid = cid
            prev_pt = P_tip

        traj_line.set_data(traj_x, traj_y)

        # ========================
        # C. 現ステップの腕描画
        # ========================
        thL, thR = thLs[step], thRs[step]
        if thL is not None:
            P_tip, P, L_tip, R_tip = forward_pen_tip(thL, thR)

            if P_tip is not None:
                M_L = np.array([-20, 0])
                M_R = np.array([ 20, 0])

                arm_lines += ax.plot([M_L[0], L_tip[0]], [M_L[1], L_tip[1]], "o-", lw=3, color="blue")
                arm_lines += ax.plot([M_R[0], R_tip[0]], [M_R[1], R_tip[1]], "o-", lw=3, color="red")
                arm_lines += ax.plot([L_tip[0], P[0]],  [L_tip[1], P[1]],  "o-", lw=3, color="cyan")
                arm_lines += ax.plot([R_tip[0], P[0]],  [R_tip[1], P[1]],  "o-", lw=3, color="magenta")
                arm_lines += ax.plot(P_tip[0], P_tip[1], "ko", markersize=8)

        fig.canvas.draw_idle()

    slider.on_changed(update)
    update(1)
    plt.show()


if __name__ == "__main__":
    slider_plot_arm_csv("/Users/kawashimasatoshishin/cutting_machine/output_curves.csv")
