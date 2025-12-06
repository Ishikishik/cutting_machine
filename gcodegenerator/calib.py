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
# 回転と移動
# ============================================================
def rotate_translate(points, theta_deg, tx, ty):
    """
    points : [(x, y), ...]   mm座標
    theta_deg : 回転角 [deg]（反時計回り＋）
    tx, ty : 平行移動量
    """
    theta = np.deg2rad(theta_deg)
    c, s = np.cos(theta), np.sin(theta)

    out = []
    for x, y in points:
        xr =  c * x - s * y + tx
        yr =  s * x + c * y + ty
        out.append((float(xr), float(yr)))

    return out



# ============================================================
# 元と見比べる
# ============================================================

def plot_compare(before, after, title=""):
    bx, by = zip(*before)
    ax, ay = zip(*after)

    plt.figure(figsize=(5,7))
    plt.scatter(bx, by, c="gray", s=20, label="before")
    plt.scatter(ax, ay, c="red",  s=30, label="after")
    plt.legend()
    plt.gca().set_aspect("equal")
    plt.grid(True)
    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()

# ============================================================
# 行列割り当て
# ============================================================
def assign_grid_indices_from_mm(points_mm, x_thresh=5.0, y_thresh=5.0):
    """
    すでにプロッター座標系(mm)にある点集合に対して、
    X, Y をそれぞれクラスタリングし、(row, col) を振る。

    x_thresh, y_thresh : 同じ列/行とみなす許容誤差 [mm]
    """
    xs = np.array([p[0] for p in points_mm])
    ys = np.array([p[1] for p in points_mm])

    # 既存の cluster_1d を再利用（中心値のリストが返る）
    cx = sorted(cluster_1d(xs.tolist(), x_thresh))
    cy = sorted(cluster_1d(ys.tolist(), y_thresh))

    n_cols = len(cx)
    n_rows = len(cy)

    indexed = []
    for x, y in points_mm:
        # 一番近い列・行を探す
        col = int(np.argmin([abs(x - v) for v in cx]))
        row = int(np.argmin([abs(y - v) for v in cy]))
        indexed.append({
            "row": row,
            "col": col,
            "x": float(x),
            "y": float(y),
        })

    return indexed, n_cols, n_rows


# ============================================================
# 理想グリッド生成
# ============================================================
def ideal_coord(row, col, x0=-50.0, y0=40.0, step=10.0):
    """
    row, col から理想的な格子点の座標を返す。

    - x は -50, -40, ..., 50
    - y は  40,  50, ..., 90
    という前提で作っています（必要ならここを変える）。
    """
    x = x0 + col * step
    y = y0 + row * step
    return x, y

# ============================================================
# 理想と現実の対応csvを書く
# ============================================================
def export_calibration_csv(indexed_points,
                           csv_path,
                           x0=-50.0, y0=40.0, step=10.0):
    """
    indexed_points: assign_grid_indices_from_mm の結果
    csv_path: 出力先

    出力形式:
    row, col, x_meas, y_meas, x_ideal, y_ideal
    """
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "col", "x_meas", "y_meas", "x_ideal", "y_ideal"])
        for p in indexed_points:
            ix, iy = ideal_coord(p["row"], p["col"], x0, y0, step)
            w.writerow([
                p["row"], p["col"],
                f"{p['x']:.6f}", f"{p['y']:.6f}",
                f"{ix:.6f}",    f"{iy:.6f}",
            ])


# ============================================================
# 確認plot
# ============================================================


def plot_measured_vs_ideal(indexed_points,
                           x0=-50.0, y0=40.0, step=10.0):
    meas_x = [p["x"] for p in indexed_points]
    meas_y = [p["y"] for p in indexed_points]

    ideal_x = []
    ideal_y = []
    for p in indexed_points:
        ix, iy = ideal_coord(p["row"], p["col"], x0, y0, step)
        ideal_x.append(ix)
        ideal_y.append(iy)

    plt.figure(figsize=(5,7))
    plt.scatter(meas_x,  meas_y,  c="red",  s=25, label="measured")
    plt.scatter(ideal_x, ideal_y, c="blue", s=15, label="ideal")
    plt.gca().set_aspect("equal")
    plt.grid(True)
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.legend()
    plt.title("Measured vs Ideal grid")
    plt.show()


# ============================================================
# main
# ============================================================
if __name__ == "__main__":
    image = "/Users/kawashimasatoshishin/cutting_machine/IMG_5339.JPG"

    warped, grid_px = interactive(image)

    if not grid_px:
        print("grid not detected")
        exit()

    h, w = warped.shape[:2]
    mm = px_to_mm(
        grid_px,
        (w, h),
        (100, 148),
        invert_y=True
    )

    # -----------------------------
    # ★ 回転・移動（仮パラメータ）
    # -----------------------------
    theta_deg = 90     # ← とりあえず回転なし
    tx = 81.5            # ← とりあえず移動なし
    ty = 36

    mm_rt = rotate_translate(mm, theta_deg, tx, ty)

    # 比較表示
    plot_compare(mm, mm_rt, title="Rotation + Translation test")

