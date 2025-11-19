# svgを解析する(svg→numpy & debug txt)
# ハガキサイズに正規化する。

from svg.path import parse_path
from xml.dom import minidom
import cv2
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
import re


def sample_segment(seg, max_step=3.0):
    """
    1セグメントを「長さ max_step(px) ごと」に分割してサンプリングする。
    長いほど細かく、多いほど粗くなる。
    """
    length = seg.length()
    num = max(2, int(length / max_step))  # 最低2点
    pts = []
    for i in range(num + 1):
        p = seg.point(i / num)
        pts.append((p.real, p.imag))
    return pts

def parse_svg(svg_path):
    """
    SVG → line/polyline/path を以下の形式で返す：
    [
        {"type": "path", "points": [(x,y),...]},
        ...
    ]
    ※ path はベジエ、直線を含む複合パス → 適応サンプリングで細かく点列化
    """

    results = []

    # -----------------------------------
    # line / polyline は既存コードを再利用
    # -----------------------------------
    tree = ET.parse(svg_path)
    root = tree.getroot()

    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # line
    for elem in root.findall(f".//{ns}line"):
        x1 = float(elem.get("x1", 0))
        y1 = float(elem.get("y1", 0))
        x2 = float(elem.get("x2", 0))
        y2 = float(elem.get("y2", 0))
        results.append({
            "type": "line",
            "points": [(x1, y1), (x2, y2)]
        })

    # polyline
    for elem in root.findall(f".//{ns}polyline"):
        pts_str = elem.get("points", "")
        nums = list(map(float, re.findall(r"[-+]?\d*\.?\d+", pts_str)))
        pts = [(nums[i], nums[i+1]) for i in range(0, len(nums), 2)]
        results.append({
            "type": "polyline",
            "points": pts
        })

    # -----------------------------------
    # path は svg.path を使って完全分解してサンプリング
    # -----------------------------------
    dom = minidom.parse(svg_path)
    path_elems = dom.getElementsByTagName("path")

    for elem in path_elems:
        d = elem.getAttribute("d")
        if not d:
            continue

        path = parse_path(d)

        pts = []
        for seg in path:  # path は複数セグメントの集合
            pts.extend(sample_segment(seg, max_step=3.0))

        results.append({
            "type": "path",
            "points": pts
        })

    dom.unlink()
    return results





# ★★★★★ デバッグ用 txt 出力に対応した NumPy 変換関数 ★★★★★
def export_to_numpy(data, debug_txt_path=None):
    """
    SVG解析結果（リスト）を path/polyline/line ごとに
    numpy 配列で保持したリストに変換して返す。

    返り値:
        segments = [ np.ndarray(shape=(N_i, 2)), ... ]
           N_i は各 path のポイント数
    """
    segments = []

    if debug_txt_path is not None:
        f = open(debug_txt_path, "w", encoding="utf-8")

    for item in data:
        pts = item["points"]
        t   = item["type"]

        # numpy化（まとまり）
        seg_np = np.array(pts, dtype=float)
        segments.append(seg_np)

        # txt 出力
        if debug_txt_path is not None:
            f.write(f"[{t}]\n")
            for (x, y) in pts:
                f.write(f"  ({x:.2f}, {y:.2f})\n")
            f.write("\n")

    if debug_txt_path is not None:
        f.close()

    return segments   # ← ここ重要！（list of numpy arrays）


def normalize_segments_mm(
        segments,
        target_w_mm=100.0,
        target_h_mm=148.0,
        offset_x_mm=0.0,
        offset_y_mm=0.0,
        rotate_deg=90,
        debug_txt_path=None,
        debug_img_path=None
    ):

    # ----------------------
    # 0) bounding box
    # ----------------------
    all_pts = np.vstack(segments)
    min_x, min_y = all_pts.min(axis=0)
    max_x, max_y = all_pts.max(axis=0)
    width  = max_x - min_x
    height = max_y - min_y

    # ----------------------
    # 1) mm正規化
    # ----------------------
    scale_x = target_w_mm / width
    scale_y = target_h_mm / height

    normalized = []
    for seg in segments:
        s = seg.copy().astype(float)
        s[:,0] = (s[:,0] - min_x) * scale_x
        s[:,1] = (s[:,1] - min_y) * scale_y
        normalized.append(s)

    # ----------------------
    # ★ 2) 中心を計算（回転の pivot）
    # ----------------------
    all_norm_pts = np.vstack(normalized)
    cx = (all_norm_pts[:,0].min() + all_norm_pts[:,0].max()) / 2
    cy = (all_norm_pts[:,1].min() + all_norm_pts[:,1].max()) / 2

    # ----------------------
    # ★ 3) pivot 基準で回転
    # ----------------------
    rad = np.deg2rad(rotate_deg)
    R = np.array([
        [np.cos(rad), -np.sin(rad)],
        [np.sin(rad),  np.cos(rad)]
    ])

    rotated = []
    for seg in normalized:
        s = seg.copy()
        s[:,0] -= cx
        s[:,1] -= cy
        s = s @ R.T
        s[:,0] += cx
        s[:,1] += cy
        rotated.append(s)

    # ----------------------
    # 4) 平行移動
    # ----------------------
    translated = []
    for seg in rotated:
        s = seg.copy()
        s[:,0] += offset_x_mm
        s[:,1] += offset_y_mm
        translated.append(s)

    # ----------------------
    # 5) debug txt
    # ----------------------
    if debug_txt_path is not None:
        with open(debug_txt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(translated):
                f.write(f"[path {i}]\n")
                for x, y in seg:
                    f.write(f"  ({x:.2f}, {y:.2f})\n")
                f.write("\n")

    # ----------------------
    # 6) debug plot
    # ----------------------
    if debug_img_path is not None:
        plt.figure(figsize=(6, 10))
        for seg in translated:
            plt.plot(seg[:,0], seg[:,1], linewidth=0.7)
        plt.gca().invert_yaxis()
        plt.axis("equal")
        plt.savefig(debug_img_path, dpi=300)
        plt.close()

    return translated
