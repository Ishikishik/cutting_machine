# list2gcode/processor.py

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


def generate_rotandscale_curves(curve_list,
                          rotate_deg=0,
                          box_w=100,
                          box_h=148,
                          decimal_digits=3):
    """
    並べ替え済みの curve_list に対して
    回転 → 縮小 → 小数点桁数丸め
    """

    # ① 回転
    rotated = rotate_curve_list(curve_list, rotate_deg)

    # ② 縮小（ハガキ 100×148mm）
    scaled = scale_curve_list(rotated, box_w, box_h)

    # ③ 小数点以下 decimal_digits 桁で丸め
    rounded = round_curve_list(scaled, ndigits=decimal_digits)

    return rounded