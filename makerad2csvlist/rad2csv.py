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

# 角度リストの生成（-180 ～ 180 を 1.8° 刻み）
ANGLES = np.arange(-180, 180 + 1e-6, 0.1125)
# モーター位置
D = 50
LEFT_MOTOR_X  = -D/2     # -25
RIGHT_MOTOR_X = +D/2     # +25

# モーター位置
D = 50
LEFT_MOTOR_X  = -D/2   # -25
RIGHT_MOTOR_X = +D/2   # +25

def generate_angle_csv(outpath="1-16angles_to_xy.csv"):

    best_map = {}   # key=(x,y) → (score, thL, thR, x, y)

    # ---- キャッシュ用（高速化） ----
    M_L = np.array([-D/2, 0.0])
    M_R = np.array([ D/2, 0.0])

    total = 0

    for thL in ANGLES:
        for thR in ANGLES:

            total += 1

            result = plot_full_arm(
                thL, thR,
                l1=65, l2=85, d=D, offset=25,
                plot=False
            )
            if result is None:
                continue

            P_tip, P, L_tip, R_tip = result
            x, y = P_tip  # 先に確保（重要）

            Lx, Ly = L_tip
            Rx, Ry = R_tip

            # =====================================
            # ① 外積による裏側 IK 解の高速フィルタ
            # =====================================

            # 左側：M_L → P と M_L → L_tip の外積
            v1x = P[0] - M_L[0]
            v1y = P[1] - M_L[1]
            v2x = L_tip[0] - M_L[0]
            v2y = L_tip[1] - M_L[1]
            crossL = v1x * v2y - v1y * v2x

            # ★符号は実機に合わせること（推奨：crossL > 0 が正解側）
            if crossL < 0:
                continue

            # 右側：M_R → P と M_R → R_tip の外積
            v1x = P[0] - M_R[0]
            v1y = P[1] - M_R[1]
            v2x = R_tip[0] - M_R[0]
            v2y = R_tip[1] - M_R[1]
            crossR = v1x * v2y - v1y * v2x

            # （こちらは符号逆：crossR < 0 が正解側のはず）
            if crossR > 0:
                continue

            # =====================================
            # ② 既存の安全フィルタ（軽い順に配置）
            # =====================================

            # 第二関節が左右関節の間にあるか
            if not (Lx + 1 < P[0] < Rx - 1):
                continue

            # 第一関節が低すぎる（危険領域）
            if Ly < 20 and Ry < 20:
                continue
            if Lx > RIGHT_MOTOR_X + 10 and Ly < -10:
                continue
            if Rx < LEFT_MOTOR_X - 10 and Ry < -10:
                continue

            # =====================================
            # ③ 安定スコア（最も軽量な形）
            # =====================================

            # (1) 第一関節間距離（最重要）
            dist1 = np.hypot(L_tip[0] - R_tip[0], L_tip[1] - R_tip[1])

            # (2) 第二関節三角形の外積面積（軽量版）
            vecLx = L_tip[0] - P[0]
            vecLy = L_tip[1] - P[1]
            vecRx = R_tip[0] - P[0]
            vecRy = R_tip[1] - P[1]
            area = abs(vecLx * vecRy - vecLy * vecRx)

            score = dist1 + 0.3 * area   # 軽く area を加点（重くしすぎない）

            # =====================================
            # ④ (x,y) をキーにしてベスト1のみ保持
            # =====================================

            key = (round(x, 3), round(y, 3))  # ← 高速のため 3 桁に

            if key not in best_map or score > best_map[key][0]:
                best_map[key] = (score, thL, thR, x, y)

    # =====================================
    # CSV 出力
    # =====================================

    rows = [ [thL, thR, x, y] for (_, thL, thR, x, y) in best_map.values() ]

    print(f"総計角度={total}, 採用={len(rows)}")
    print(f"CSV → {outpath}")

    with open(outpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["theta_L", "theta_R", "x", "y"])
        w.writerows(rows)



#generate_angle_csv(outpath="1-16angles_to_xy.csv")

print(plot_full_arm(0,90, l1=65, l2=85, d=50, offset=25, plot=False))
