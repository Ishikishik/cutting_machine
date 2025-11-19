# list2gcode/list2goodlist.py

import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb


# =========================================================
# 0. approxPolyDP で曲線点を approx N points へ簡略化
# =========================================================
def simplify_curve(points, target_points=80):
    pts = np.array(points, dtype=np.float32)

    if len(pts) <= target_points:
        return pts.tolist()

    epsilon = 0.01 * cv2.arcLength(pts, closed=False)
    simp = cv2.approxPolyDP(pts, epsilon, closed=False).reshape(-1, 2)

    # ε を調整して点数が target に近づくようにする
    for _ in range(10):
        n = len(simp)
        if n > target_points * 1.2:
            epsilon *= 1.4
        elif n < target_points * 0.8:
            epsilon *= 0.7
        else:
            break
        simp = cv2.approxPolyDP(pts, epsilon, closed=False).reshape(-1, 2)

    return simp.tolist()


# =========================================================
# 1. 曲線内部の点を並べ替える（RDPの特性利用）
# =========================================================
def reorder_curve(points):
    pts = np.array(points)
    N = len(pts)

    # --- 両端候補の算出 ---
    # 端点は点群内で最も遠い2点（幾何学的線形性が高い）
    dmat = np.linalg.norm(pts[:,None,:] - pts[None,:,:], axis=-1)
    i0, j0 = np.unravel_index(np.argmax(dmat), dmat.shape)

    def greedy_order(start_idx):
        used = np.zeros(N, dtype=bool)
        idx = start_idx
        used[idx] = True
        ordered = [pts[idx]]

        for _ in range(N - 1):
            d = np.linalg.norm(pts - ordered[-1], axis=1)
            d[used] = 1e18
            idx = np.argmin(d)
            used[idx] = True
            ordered.append(pts[idx])

        return np.array(ordered)

    # 始点を両端候補 A と B で試す
    seqA = greedy_order(i0)
    seqB = greedy_order(j0)

    def path_len(arr):
        return np.sum(np.linalg.norm(arr[1:] - arr[:-1], axis=1))

    # より滑らかな（短い）方を採用
    if path_len(seqA) <= path_len(seqB):
        return seqA.tolist()
    else:
        return seqB.tolist()




# =========================================================
# 2. 全曲線まとめて可視化（薄い→濃い）
# =========================================================
def visualize_curves(curve_list):
    plt.figure(figsize=(7, 9))
    ax = plt.gca()
    ax.set_aspect("equal")
    ax.axis("off")
    plt.title("Curve Internal Order (Light → Dark per Curve)")

    hue = 0.33  # 緑系色相

    for curve in curve_list:
        pts = np.array(curve["points"], dtype=float)
        pts[:,1] *= -1  # y反転

        N = len(pts)

        # 曲線内部の点を順番に描画（早い点→明るい）
        for i in range(N - 1):
            t = i / (N - 1)

            # t=0 → 明るい緑, t=1 → 濃い緑
            val = 0.3 + 0.7 * t
            sat = 0.9
            rgb = hsv_to_rgb([hue, sat, val])

            x0, y0 = pts[i]
            x1, y1 = pts[i+1]

            ax.plot([x0, x1], [y0, y1], '-', color=rgb, linewidth=2)

    plt.show()
