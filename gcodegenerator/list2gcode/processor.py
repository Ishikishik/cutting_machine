# list2gcode/processor.py
import numpy as np

from .list2goodlist import (
    simplify_curve,
    reorder_curve,
    visualize_curves,
    reorder_curves_by_tsp,
    save_curve_list_to_csv,
    rotate_curve_list,
    scale_curve_list,
    round_curve_list,
)


def process_curve_list(curve_list):
    """
    main.py から呼ばれる
    1) approxPolyDP による簡略化
    2) RDP 特性を活かした並べ替え
    3) matplotlib による可視化
    """

    processed = []

    for curve in curve_list:
        # 1. approxPolyDP（50 点程度）
        simplified = simplify_curve(curve["points"], target_points=250)

        # 2. 並べ替え
        ordered = reorder_curve(simplified)

        processed.append({
            "curve_id": curve["curve_id"],
            "points": ordered
        })

    # 3. 可視化
    visualize_curves(processed)

    return processed


def sort_curves_tsp(curve_list):
    """
    TSP を使って曲線全体の描画順を決める。
    内部順序は既に正しいものとする。
    """
    sorted_list = reorder_curves_by_tsp(curve_list)
    return sorted_list


def export_curve_csv(curve_list, filename="curves.csv"):
    save_curve_list_to_csv(curve_list, filename)


from list2gcode.list2goodlist import (
    rotate_curve_list,
    scale_curve_list,
    translate_curve_list,
    round_curve_list,
)


def generate_rotandscale_curves(curve_list,
                                rotate_deg=0,
                                box_w=100,
                                box_h=148,
                                offset_x=0,
                                offset_y=0,
                                decimal_digits=3):
    """
    並べ替え済みの curve_list に対して
    回転 → 縮小 → 平行移動 → 小数点丸め
    """

    # ① 回転
    rotated = rotate_curve_list(curve_list, rotate_deg)

    # ② 縮小（ハガキ等）
    scaled = scale_curve_list(rotated, box_w, box_h)

    # ③ 平行移動（offset_x, offset_y mm）
    translated = translate_curve_list(scaled, offset_x, offset_y)

    # ④ 小数点以下 N 桁で丸め
    final_list = round_curve_list(translated, ndigits=decimal_digits)

    return final_list











"""
角度に変換
"""

# ================================
#   processor.py（新しい関数追加）
# ================================
from .makegcode import load_kdtree, radcheck

def genrad_kdtree(final_curves,
                  lut_path="lut_tree.pkl",
                  max_error_mm=1.0):

    print("KD-tree をロード中:", lut_path)
    tree, thL_list, thR_list = load_kdtree(lut_path)

    output = []

    for curve in final_curves:
        cid = curve["curve_id"]
        pts = curve["points"]

        new_pts = []
        prev_L = None
        prev_R = None

        for (x, y) in pts:

            # KD-tree 最近傍
            dist, idx = tree.query([x, y])

            if dist > max_error_mm:
                new_pts.append((x, y, None, None))
                continue

            thL = thL_list[idx]
            thR = thR_list[idx]

            # radcheck（干渉チェック）
            if not radcheck(thL, thR):
                new_pts.append((x, y, None, None))
                continue

            new_pts.append((x, y, thL, thR))

        output.append({
            "curve_id": cid,
            "points": new_pts
        })

    return output
