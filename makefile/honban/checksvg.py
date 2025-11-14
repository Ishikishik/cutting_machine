#gcodeを解析する
import cv2
import xml.etree.ElementTree as ET
import csv
from pathlib import Path
import re

def parse_svg(svg_path):
    """
    SVGファイルを読み込んで、線分情報をリスト化して返す
    各要素は {'type': 'line'|'polyline'|'path', 'points': [(x,y),...]} の形式
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 名前空間（{http://www.w3.org/2000/svg} のような接頭辞）を取得
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    results = []

    # ---- 1. line要素 ----
    for elem in root.findall(f".//{ns}line"):
        x1 = float(elem.get("x1", 0))
        y1 = float(elem.get("y1", 0))
        x2 = float(elem.get("x2", 0))
        y2 = float(elem.get("y2", 0))
        results.append({"type": "line", "points": [(x1, y1), (x2, y2)]})

    # ---- 2. polyline要素 ----
    for elem in root.findall(f".//{ns}polyline"):
        pts_str = elem.get("points", "")
        pts = []
        for token in re.findall(r"[-+]?\d*\.?\d+", pts_str):
            pass  # ダミー（次で整列処理）
        # x,yのペアに変換
        nums = list(map(float, re.findall(r"[-+]?\d*\.?\d+", pts_str)))
        pts = [(nums[i], nums[i+1]) for i in range(0, len(nums), 2)]
        results.append({"type": "polyline", "points": pts})

    # ---- 3. path要素 ----
    for elem in root.findall(f".//{ns}path"):
        d = elem.get("d", "")
        pts = parse_path_data(d)
        results.append({"type": "path", "points": pts})

    return results


def parse_path_data(d):
    """
    pathのd属性を簡単に直線ベースでパースする関数
    （M,L,H,V,Zのみ対応）
    """
    tokens = re.findall(r"[MLHVZmlhvz]|[-+]?\d*\.?\d+", d)
    points = []
    cx, cy = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    cmd = None
    i = 0

    while i < len(tokens):
        t = tokens[i]
        i += 1
        if re.match(r"[MLHVZmlhvz]", t):
            cmd = t
            if cmd in "Zz":  # 閉じる
                points.append((start_x, start_y))
        else:
            if cmd in ("M", "L"):
                x = float(t)
                y = float(tokens[i]); i += 1
                cx, cy = x, y
                if cmd == "M":
                    start_x, start_y = cx, cy
                points.append((cx, cy))
            elif cmd in ("m", "l"):
                x = float(t)
                y = float(tokens[i]); i += 1
                cx += x; cy += y
                if cmd == "m":
                    start_x, start_y = cx, cy
                points.append((cx, cy))
            elif cmd in ("H", "h"):
                x = float(t)
                if cmd == "h": cx += x
                else: cx = x
                points.append((cx, cy))
            elif cmd in ("V", "v"):
                y = float(t)
                if cmd == "v": cy += y
                else: cy = y
                points.append((cx, cy))
    return points


def export_to_csv(data, output_csv):
    """パース結果をCSVに出力"""
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "x", "y"])
        for item in data:
            for (x, y) in item["points"]:
                writer.writerow([item["type"], x, y])
    print(f"✅ CSV出力完了 → {output_csv}")


def export_to_txt(data, output_txt):
    """パース結果を見やすいテキスト形式で出力"""
    with open(output_txt, "w", encoding="utf-8") as f:
        for item in data:
            f.write(f"[{item['type']}]\n")
            for (x, y) in item["points"]:
                f.write(f"  ({x:.2f}, {y:.2f})\n")
            f.write("\n")
    print(f"✅ TXT出力完了 → {output_txt}")


if __name__ == "__main__":
    svg_file = Path("line_raw.svg")
    output_csv = Path("svg_points.csv")
    output_txt = Path("svg_points.txt")

    parsed = parse_svg(svg_file)
    print(f"📊 SVG内の要素数: {len(parsed)}")
    export_to_csv(parsed, output_csv)
    export_to_txt(parsed, output_txt)
