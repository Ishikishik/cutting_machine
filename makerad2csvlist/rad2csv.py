import csv
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
#  FK-1 : 第一リンク（l1）先端座標を求める
# ============================================================
def compute_first_link(theta_l_deg, theta_r_deg, l1=65.0, d=50.0, theta_min=10.0):
    tl = np.radians(theta_l_deg)
    tr = np.radians(theta_r_deg)

    M_L = np.array([-d/2, 0.0])
    M_R = np.array([ d/2, 0.0])

    L_tip = np.array([
        M_L[0] - l1 * np.cos(tl),
        M_L[1] + l1 * np.sin(tl)
    ])

    R_tip = np.array([
        M_R[0] + l1 * np.cos(tr),
        M_R[1] + l1 * np.sin(tr)
    ])

    return L_tip, R_tip


# ============================================================
#  FK-2 : 第二リンクの交点（基準点 P）
# ============================================================
def compute_pen_position(L_tip, R_tip, l2):
    x1, y1 = L_tip
    x2, y2 = R_tip
    d = np.hypot(x2 - x1, y2 - y1)

    if d > 2*l2:
        return None

    a = d/2
    h = np.sqrt(l2**2 - a*a)

    xm = x1 + (x2-x1)*a/d
    ym = y1 + (y2-y1)*a/d

    rx = -(y2 - y1) * (h/d)
    ry =  (x2 - x1) * (h/d)

    p1 = np.array([xm + rx, ym + ry])
    p2 = np.array([xm - rx, ym - ry])

    return p1 if p1[1] >= p2[1] else p2


# ============================================================
#  FK-3 ：ペン先（25mm延長した実ペン先）
# ============================================================
def forward_pen_tip(theta_l_deg, theta_r_deg, l1=65.0, l2=85, d=50.0, offset=25.0):
    L_tip, R_tip = compute_first_link(theta_l_deg, theta_r_deg, l1=l1, d=d)
    P = compute_pen_position(L_tip, R_tip, l2)
    if P is None:
        return None

    dir_vec = P - R_tip
    norm = np.hypot(dir_vec[0], dir_vec[1])
    if norm < 1e-6:
        return None

    unit_vec = dir_vec / norm
    P_tip = P + unit_vec * offset
    return P_tip


# ============================================================
#  IK 初期値：第二リンク交点を目標として解く（通常の5bar IK）
# ============================================================
def ik_candidates(Px, Py, l1=65.0, l2=85.0, d=50.0):
    cands = []

    # 左側
    XL = Px + d/2
    YL = Py
    rL = np.hypot(XL, YL)
    cos_L = (l1*l1 + rL*rL - l2*l2) / (2*l1*rL)
    if abs(cos_L) > 1:
        return []
    baseL = np.arctan2(YL, XL)
    phiL = np.arccos(cos_L)
    left = [baseL + phiL, baseL - phiL]

    # 右側
    XR = Px - d/2
    YR = Py
    rR = np.hypot(XR, YR)
    cos_R = (l1*l1 + rR*rR - l2*l2) / (2*l1*rR)
    if abs(cos_R) > 1:
        return []
    baseR = np.arctan2(YR, XR)
    phiR = np.arccos(cos_R)
    right = [baseR + phiR, baseR - phiR]

    # 4組
    for tL in left:
        for tR in right:
            cands.append((np.degrees(tL), np.degrees(tR)))

    return cands


def plot_full_arm(theta_l_deg, theta_r_deg, l1=65, l2=85, d=50, offset=25, plot=True):
    """
    角度制限・干渉チェックを完全削除したバージョン。
    θL, θR が 0〜360° のどこでも順運動を返せる。
    """

    # --- 第一リンク先端 ---
    L_tip, R_tip = compute_first_link(theta_l_deg, theta_r_deg, l1=l1, d=d)

    # 計算不可 → None
    if L_tip is None or R_tip is None:
        return None

    # --- 第二リンク交点 P ---
    P = compute_pen_position(L_tip, R_tip, l2)
    if P is None:
        return None

    # --- 実ペン先（延長） ---
    dir_vec = P - R_tip
    norm = np.hypot(dir_vec[0], dir_vec[1])

    if norm < 1e-8:
        # 方向が決まらない＝第二リンクが真上などの特異点
        return None

    unit_vec = dir_vec / norm
    P_tip = P + unit_vec * offset

    # --- 描画（オプション） ---
    if plot:
        plt.figure(figsize=(6, 6))
        ax = plt.gca()
        ax.set_aspect("equal")
        ax.set_xlim(-150, 200)
        ax.set_ylim(-50, 200)
        ax.grid(True)

        M_L = np.array([-d/2, 0.0])
        M_R = np.array([ d/2, 0.0])

        ax.plot([M_L[0], L_tip[0]], [M_L[1], L_tip[1]], "o-", lw=3, color="blue")
        ax.plot([M_R[0], R_tip[0]], [M_R[1], R_tip[1]], "o-", lw=3, color="red")

        ax.plot([L_tip[0], P[0]], [L_tip[1], P[1]], "o-", lw=3, color="cyan")
        ax.plot([R_tip[0], P[0]], [R_tip[1], P[1]], "o-", lw=3, color="magenta")

        ax.plot([P[0], P_tip[0]], [P[1], P_tip[1]], "--", lw=2, color="orange")

        ax.plot(P[0], P[1], "ko", markersize=6)
        ax.plot(P_tip[0], P_tip[1], "ro", markersize=8)

        plt.title(f"θL={theta_l_deg}°, θR={theta_r_deg}°（offset={offset}mm）")
        plt.show()

    # --- 順運動の結果を返す ---    
    return P_tip, P, L_tip, R_tip 



print(plot_full_arm(40,60, l1=65, l2=85, d=50, offset=25, plot=True))

# 角度リストの生成（-180 ～ 180 を 1.8° 刻み）
ANGLES = np.arange(-180, 180 + 1e-6, 1.8)
# モーター位置
D = 50
LEFT_MOTOR_X  = -D/2     # -25
RIGHT_MOTOR_X = +D/2     # +25

# モーター位置
D = 50
LEFT_MOTOR_X  = -D/2   # -25
RIGHT_MOTOR_X = +D/2   # +25

def generate_angle_csv(outpath="angles_to_xy.csv"):
    rows = []
    total = 0
    ok = 0

    for thL in ANGLES:
        for thR in ANGLES:

            total += 1

            # 順運動
            result = plot_full_arm(
                thL, thR,
                l1=65, l2=85, d=D, offset=25,
                plot=False
            )

            if result is None:
                continue

            P_tip, P, L_tip, R_tip = result

            Lx, Ly = L_tip
            Rx, Ry = R_tip
            Px, Py = P

            # 第二関節の左右関係
            if not (Lx + 1 < Px < Rx - 1):
                continue

            # 両方の第一関節が低い（危険領域）
            if Ly < 20 and Ry < 20:
                continue

            # 左第一関節が右モーター側へ大きく侵入したらNG（余裕を持たせる）
            if Lx > RIGHT_MOTOR_X + 10 and Ly < -10:
                continue

            # 右第一関節が左側へ大きく侵入したらNG
            if Rx < LEFT_MOTOR_X - 10 and Ry < -10:
                continue


            # ------------------------------------------------------
            # すべての安全チェックを通過した場合のみ採用
            # ------------------------------------------------------

            x, y = P_tip
            rows.append([thL, thR, x, y])
            ok += 1

    print(f"総角度={total}  OK={ok}  (安全角度のみ採用)")
    print(f"CSV → {outpath}")

    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["theta_L", "theta_R", "x", "y"])
        writer.writerows(rows)

generate_angle_csv(outpath="angles_to_xy.csv")