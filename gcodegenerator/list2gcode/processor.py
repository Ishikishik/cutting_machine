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
from .makegcode import (
    load_lut,
    radcheck,
    plot_full_arm
)
import numpy as np


def ik_from_lut_all(x, y, lut):
    """
    LUTの全候補を返す。
    戻り値は err が小さい順のリスト:
       [(err, theta_L, theta_R), ...]
    """
    results = []
    for (thL, thR, lx, ly) in lut:
        err = np.hypot(lx - x, ly - y)
        results.append((err, thL, thR))

    results.sort(key=lambda v: v[0])
    return results   # 近い順になっている


def genrad_lut(final_curves,
               lut_path="lut_angles_to_xy.csv",
               max_err_mm=1.0,
               l1=65, l2=85, d=50, offset=25):
    """
    LUT方式の角度変換関数（完全版）
    radcheck=false の場合は次の候補を探索する
    """

    lut = load_lut(lut_path)
    output = []

    for curve in final_curves:

        cid = curve["curve_id"]
        pts = curve["points"]

        new_pts = []

        prev_L = None
        prev_R = None

        for idx, (x, y) in enumerate(pts):

            # ----① LUTを距離順に候補化 ----
            cand_list = ik_from_lut_all(x, y, lut)

            chosen = None

            # ----② 候補を順に試す ----
            for err_lut, thL_raw, thR_raw in cand_list:

                if err_lut > max_err_mm:
                    break  # これ以上は遠すぎる

                thL = thL_raw
                thR = thR_raw

                # ---- radcheck: NG なら次候補へ ----
                if not radcheck(thL, thR):
                    continue

                # ---- 順運動で最終チェック ----
                result = plot_full_arm(
                    thL, thR,
                    l1=l1, l2=l2, d=d, offset=offset,
                    plot=False
                )

                if result is None:
                    continue

                P_tip, _, _, _ = result
                err_fk = np.hypot(P_tip[0] - x, P_tip[1] - y)

                if err_fk > max_err_mm:
                    continue

                # ---- 前回角度に最も近いものを優先 ----
                if prev_L is not None:
                    angle_cost = (
                        abs(thL - prev_L) +
                        abs(thR - prev_R)
                    )
                else:
                    angle_cost = 0  # 1点目は無条件に採用可

                chosen = (angle_cost, thL, thR)
                break

            # ----③ 候補なし ----
            if chosen is None:
                new_pts.append((x, y, None, None))
                continue

            _, thL_sel, thR_sel = chosen
            prev_L, prev_R       = thL_sel, thR_sel

            # ----④ 保存 ----
            new_pts.append((x, y, thL_sel, thR_sel))

        output.append({
            "curve_id": cid,
            "points": new_pts
        })

    return output
