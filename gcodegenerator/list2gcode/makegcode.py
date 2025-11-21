# =========================
#   makegcode.py (LUT対応版)
# =========================

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

    # --- 順運動の結果を返す ---    return P_tip, P, L_tip, R_tip

# =========================================
#  🔵 新規追加: LUT 読み込み
# =========================================
def load_lut(path="/Users/kawashimasatoshishin/cutting_machine/gcodegenerator/list2gcode/rad2xy.csv"):
    """
    LUT CSV を読み込んで配列として返す
    columns = [theta_L, theta_R, x, y]
    """
    lut = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            thL = float(r["theta_L"])
            thR = float(r["theta_R"])
            x   = float(r["x"])
            y   = float(r["y"])
            lut.append((thL, thR, x, y))
    return lut


# =========================================
#  🔵 新規追加: LUT から最も近い角度を検索する
# =========================================
def ik_from_lut(x, y, lut, max_dist=1.0):
    """
    ペン先 (x,y) に最も近い LUT の点を返す。
    max_dist mm 以内のものだけ採用する。

    return:
        (theta_L, theta_R) or None
    """

    best = None
    best_err = 1e12

    for (thL, thR, lx, ly) in lut:
        err = np.hypot(lx - x, ly - y)
        if err < best_err:
            best_err = err
            best = (thL, thR)

    if best_err <= max_dist:
        return best
    else:
        return None


# =========================================
#  🔵 新規追加: radcheck（今はダミー）
# =========================================
def radcheck(thL, thR):
    """
    機構干渉などを後でここで実装する。

    今は常に OK とする。
    """
    return True
