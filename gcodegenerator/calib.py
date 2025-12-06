import cv2
import numpy as np
import matplotlib.pyplot as plt
import csv

# ============================================================
# ArUco 設定
# ============================================================
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# ============================================================
# 1D クラスタリング（距離しきい値）
# ============================================================
def cluster_1d(values, thresh):
    if not values:
        return []

    values = sorted(values)
    clusters = [[values[0]]]

    for v in values[1:]:
        if abs(v - clusters[-1][-1]) <= thresh:
            clusters[-1].append(v)
        else:
            clusters.append([v])

    return [np.mean(c) for c in clusters]   # 中心は float で返す


# ============================================================
# ArUco によるワープ
# ============================================================
def warp_by_aruco(image_path, output_size=(1000, 1480)):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray, ARUCO_DICT)

    if ids is None or len(ids) < 4:
        raise RuntimeError("ArUco markers not detected")

    centers = []
    for c in corners:
        pts = c.reshape(-1, 2)
        centers.append(pts.mean(axis=0))
    centers = np.array(centers, np.float32)

    # 四隅のマーカーを TL, TR, BR, BL に自動割り当て
    s = centers.sum(axis=1)
    diff = centers[:, 0] - centers[:, 1]

    tl = centers[np.argmin(s)]
    br = centers[np.argmax(s)]
    tr = centers[np.argmax(diff)]
    bl = centers[np.argmin(diff)]

    src = np.array([tl, tr, br, bl], np.float32)
    w, h = output_size
    dst = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], np.float32)

    H = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, H, (w, h))

    return warped


# ============================================================
# 線分 → 点列
# ============================================================
def line_to_points(lines):
    """
    HoughLinesP の線分群を、線上の細かい点列に展開する
    """
    pts = []
    for x1, y1, x2, y2 in lines:
        length = int(max(2, np.hypot(x2-x1, y2-y1)))
        ts = np.linspace(0.0, 1.0, length)
        xs = x1 + ts * (x2 - x1)
        ys = y1 + ts * (y2 - y1)
        pts.extend(np.stack([xs, ys], axis=1))
    if len(pts) == 0:
        return np.zeros((0, 2), np.float32)
    return np.array(pts, np.float32)


# ============================================================
# 点群を 1D でクラスタ → (中心値, 点群) のリスト
# ============================================================
def cluster_points_1d(pts, axis, thresh):
    """
    axis=0: x でクラスタ（縦線）
    axis=1: y でクラスタ（横線）
    """
    if len(pts) == 0:
        return []

    key = pts[:, axis]
    centers = cluster_1d(key.tolist(), thresh)

    groups = []
    for c in centers:
        mask = np.abs(key - c) <= thresh
        grp = pts[mask]
        if len(grp) > 0:
            groups.append((c, grp))
    return groups


# ============================================================
# 曲線フィット
# ============================================================
def fit_vertical_curve(points):
    """
    縦線: x = f(y) を 2 次多項式でフィット
    """
    y = points[:, 1]
    x = points[:, 0]
    coef = np.polyfit(y, x, 2)   # x = a*y^2 + b*y + c
    return coef


def fit_horizontal_curve(points):
    """
    横線: y = f(x) を 2 次多項式でフィット
    """
    x = points[:, 0]
    y = points[:, 1]
    coef = np.polyfit(x, y, 2)   # y = a*x^2 + b*x + c
    return coef


# ============================================================
# 縦曲線 × 横曲線 の交点を数値的に求める
# ============================================================
def intersect_vertical_horizontal(coef_v, coef_h, y_min, y_max, n_sample=2000):
    """
    coef_v: x = f_v(y) の係数（np.poly1d 用）
    coef_h: y = f_h(x) の係数
    y_min, y_max: 探索する y 範囲（画像高さの中で有効範囲）
    """
    pv = np.poly1d(coef_v)
    ph = np.poly1d(coef_h)

    ys = np.linspace(y_min, y_max, n_sample)
    xs = pv(ys)
    ys_h = ph(xs)

    err = ys_h - ys
    idx = np.argmin(np.abs(err))

    y_int = float(ys[idx])
    x_int = float(xs[idx])
    return x_int, y_int


# ============================================================
# 格子検出（Hough → 曲線 → 交点）
# ============================================================
def detect_grid(warped,
                shrink,
                canny_lo, canny_hi,
                hough_thresh,
                min_len, max_gap,
                cluster_thresh):

    h, w = warped.shape[:2]

    # --- マスク ---
    mask = np.ones((h, w), np.uint8)
    mask[:shrink, :] = 0
    mask[h-shrink:, :] = 0
    mask[:, :shrink] = 0
    mask[:, w-shrink:] = 0

    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, canny_lo, canny_hi)
    edges = cv2.bitwise_and(edges, edges, mask=mask)

    # --- Hough 線分検出 ---
    lines = cv2.HoughLinesP(
        edges, 1, np.pi/180,
        threshold=hough_thresh,
        minLineLength=min_len,
        maxLineGap=max_gap
    )

    vis = warped.copy()
    v_lines, h_lines = [], []

    if lines is not None:
        for x1, y1, x2, y2 in lines[:, 0]:
            # 可視化
            cv2.line(vis, (x1, y1), (x2, y2), (0, 255, 0), 1)

            # 縦／横分類（まだ「線分」のまま）
            if abs(x2 - x1) < abs(y2 - y1):      # 縦
                v_lines.append((x1, y1, x2, y2))
            else:                                # 横
                h_lines.append((x1, y1, x2, y2))

    # --- 線分 → 点群 ---
    v_pts = line_to_points(v_lines)
    h_pts = line_to_points(h_lines)

    # --- x / y でクラスタ（線ごとに分ける） ---
    v_groups = cluster_points_1d(v_pts, axis=0, thresh=cluster_thresh)
    h_groups = cluster_points_1d(h_pts, axis=1, thresh=cluster_thresh)

    # --- 各クラスタを 2次曲線としてフィット ---
    v_curves = []
    for cx, pts in v_groups:
        if len(pts) < 30:
            continue
        coef = fit_vertical_curve(pts)
        v_curves.append((cx, coef))

    h_curves = []
    for cy, pts in h_groups:
        if len(pts) < 30:
            continue
        coef = fit_horizontal_curve(pts)
        h_curves.append((cy, coef))

    # 並び順を安定させるために中心座標でソート
    v_curves.sort(key=lambda t: t[0])  # 左から右
    h_curves.sort(key=lambda t: t[0])  # 上から下

    # --- 曲線同士の交点を求める ---
    grid = []
    for _, cv_v in v_curves:
        for _, cv_h in h_curves:
            x_int, y_int = intersect_vertical_horizontal(
                cv_v, cv_h,
                y_min=shrink,
                y_max=h - shrink,
                n_sample=1500
            )
            xi, yi = int(round(x_int)), int(round(y_int))
            # 画像内か一応チェック
            if 0 <= xi < w and 0 <= yi < h:
                grid.append((xi, yi))

    # --- 交点を可視化 ---
    for x, y in grid:
        cv2.circle(vis, (x, y), 4, (0, 255, 255), -1)

    return vis, grid


# ============================================================
# px → mm 変換
# ============================================================
def px_to_mm(points_px, img_size_px, size_mm, invert_y=True):
    w_px, h_px = img_size_px
    w_mm, h_mm = size_mm

    result = []
    for x, y in points_px:
        mx = x * w_mm / w_px
        my = y * h_mm / h_px
        if invert_y:
            my = h_mm - my
        result.append((mx, my))
    return result


# ============================================================
# GUI
# ============================================================
def interactive(image_path):

    warped = warp_by_aruco(image_path)
    cv2.namedWindow("grid", cv2.WINDOW_NORMAL)

    def tb(name, val, maxv):
        cv2.createTrackbar(name, "grid", val, maxv, lambda x: None)

    tb("shrink",    80, 300)
    tb("canny_lo",  50, 200)
    tb("canny_hi", 120, 300)
    tb("hough",     40, 200)
    tb("minlen",    80, 300)
    tb("maxgap",    10,  50)
    tb("cluster",   15,  80)   # クラスタしきい値（px）

    last = []

    while True:
        v = lambda n: cv2.getTrackbarPos(n, "grid")

        vis, grid = detect_grid(
            warped,
            v("shrink"),
            v("canny_lo"), v("canny_hi"),
            v("hough"),
            v("minlen"), v("maxgap"),
            v("cluster")
        )

        last = grid
        cv2.imshow("grid", vis)

        k = cv2.waitKey(30) & 0xFF
        if k == ord("q"):
            last = []
            break
        if k == ord("s"):
            break

    cv2.destroyAllWindows()
    return warped, last


# ============================================================
# プロット
# ============================================================
def plot_mm(mm):
    x, y = zip(*mm)
    plt.figure(figsize=(5, 7))
    plt.scatter(x, y, s=10, c="red")
    plt.gca().set_aspect("equal")
    plt.grid(True)
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.show()


# ============================================================
# 回転と移動（mm座標上）
# ============================================================
def rotate_translate(points_mm, theta_deg, tx, ty):
    """
    points_mm : [(x, y), ...]   すでに mm に変換済みの点
    theta_deg : 回転角[deg]（反時計回りが正）
    tx, ty    : 平行移動量
    """
    theta = np.deg2rad(theta_deg)
    c, s = np.cos(theta), np.sin(theta)

    out = []
    for x, y in points_mm:
        xr =  c * x - s * y + tx
        yr =  s * x + c * y + ty
        out.append((float(xr), float(yr)))
    return out


# ============================================================
# グリッド順に (row, col) を振る
#   1. y でソートして 6 行に分ける
#   2. 各行の中を x でソートして 11 列を割り当て
# ============================================================
def index_grid(points_mm, n_rows=6, n_cols=11):
    """
    points_mm : [(x, y), ...]  回転・平行移動後の mm 座標

    戻り値:
      indexed_points : [{row, col, x, y}, ...]
    """
    pts = np.array(points_mm, dtype=float)
    if pts.shape[0] != n_rows * n_cols:
        raise ValueError(
            f"点の数が {pts.shape[0]} 個ですが、"
            f"{n_rows}×{n_cols}={n_rows*n_cols} 個必要です"
        )

    xs = pts[:, 0]
    ys = pts[:, 1]

    # 1) y でソート（下から上 or 上から下に単調になる）
    order_y = np.argsort(ys)

    indexed = []

    for row in range(n_rows):
        # この行に属する n_cols 個のインデックスを取り出す
        start = row * n_cols
        end   = (row + 1) * n_cols
        idx_row = order_y[start:end]

        # 2) 行の中を x でソート → 左から右に col を振る
        xs_row = xs[idx_row]
        order_x_in_row = np.argsort(xs_row)

        for col, k in enumerate(idx_row[order_x_in_row]):
            x = float(xs[k])
            y = float(ys[k])
            indexed.append({
                "row": row,
                "col": col,
                "x": x,
                "y": y,
            })

    return indexed


# ============================================================
# 理想グリッド（計算式だが 6×11 に限定して使う）
# ============================================================
def ideal_coord(row, col, x0=-50.0, y0=40.0, step=10.0):
    """
    row, col から理想格子点の座標を返す。

    row: 0..5 (y = 40..90)
    col: 0..10 (x = -50..50)
    """
    x = x0 + col * step
    y = y0 + row * step
    return x, y


# ============================================================
# 理想と現実の対応 csv を書く
# ============================================================
def export_calibration_csv(indexed_points,
                           csv_path,
                           x0=-50.0, y0=40.0, step=10.0):
    """
    indexed_points : index_grid() の結果
    出力形式:
      row, col, x_meas, y_meas, x_ideal, y_ideal, dx, dy
    """
    # 行・列順で並べ直す
    indexed_points = sorted(indexed_points, key=lambda p: (p["row"], p["col"]))

    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "row", "col",
            "x_meas", "y_meas",
            "x_ideal", "y_ideal",
            "dx", "dy"
        ])

        for p in indexed_points:
            ix, iy = ideal_coord(p["row"], p["col"], x0, y0, step)
            mx, my = p["x"], p["y"]
            dx = mx - ix
            dy = my - iy

            w.writerow([
                p["row"], p["col"],
                f"{mx:.6f}", f"{my:.6f}",
                f"{ix:.6f}", f"{iy:.6f}",
                f"{dx:.6f}", f"{dy:.6f}",
            ])


# ============================================================
# measured vs ideal の確認プロット
# ============================================================
def plot_measured_vs_ideal(indexed_points,
                           x0=-50.0, y0=40.0, step=10.0):
    indexed_points = sorted(indexed_points, key=lambda p: (p["row"], p["col"]))

    plt.figure(figsize=(8,4))

    for p in indexed_points:
        mx, my = p["x"], p["y"]
        ix, iy = ideal_coord(p["row"], p["col"], x0, y0, step)

        # 理想 → 実測への矢印
        plt.plot([ix, mx], [iy, my], "-", color="0.6", alpha=0.5)
        plt.scatter(ix, iy, c="blue", s=20)
        plt.scatter(mx, my, c="red",  s=30)

    plt.gca().set_aspect("equal")
    plt.grid(True)
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.title("Ideal (blue) ↔ Measured (red)")
    plt.show()


# ============================================================
# main
# ============================================================
if __name__ == "__main__":
    image = "/Users/kawashimasatoshishin/cutting_machine/IMG_5339.JPG"
    calib_csv = "/Users/kawashimasatoshishin/cutting_machine/grid_calib.csv"

    # 1) 画像から格子を検出（GUIで 's' 決定）
    warped, grid_px = interactive(image)
    if not grid_px:
        print("grid not detected")
        exit()

    # 2) px → mm
    h, w = warped.shape[:2]
    mm = px_to_mm(
        grid_px,
        (w, h),
        (100+30, 148+30),
        invert_y=True
    )

    # 3) 回転 + 平行移動（ここはあなたが決めた値を入れる）
    theta_deg = 90      # 例
    tx = 92           # 例
    ty = 36             # 例
    mm_rt = rotate_translate(mm, theta_deg, tx, ty)

    # 4) グリッドの行・列を確定させる（最近傍は使わない）
    indexed = index_grid(mm_rt, n_rows=6, n_cols=11)

    # 5) CSV 出力
    export_calibration_csv(
        indexed,
        calib_csv,
        x0=-50.0,
        y0=40.0+57/2,
        step=10.0
    )
    print("saved:", calib_csv)

    # 6) 確認プロット
    plot_measured_vs_ideal(
        indexed,
        x0=-50.0,
        y0=40.0+57/2,
        step=10.0
    )
