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
    convert_to_motor_coords,
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
    chaikin,
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

    #cheikin平滑化
    smoothed = []
    for curve in scaled:
        if isinstance(curve, dict):
            cid = curve["curve_id"]
            pts = curve["points"]
            new_pts = chaikin(pts, step=2)
            smoothed.append({"curve_id": cid, "points": new_pts})
        else:
            smoothed.append(chaikin(curve, step=2))


    # モーター座標に変換
    motor_ready = convert_to_motor_coords(smoothed, height=100)

    # ③ 平行移動（offset_x, offset_y mm）
    translated = translate_curve_list(motor_ready, offset_x, offset_y)

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
                  max_error_mm=2.0):

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

            # k=20個の候補を取る
            dists, idxs = tree.query([x, y], k=20)

            best = None
            best_score = 1e9

            for dist, idx in zip(dists, idxs):
                if dist > max_error_mm:
                    continue

                thL = thL_list[idx]
                thR = thR_list[idx]

                if not radcheck(thL, thR):
                    continue

                # 角度連続性評価
                if prev_L is not None:
                    score = abs(thL - prev_L) + abs(thR - prev_R)
                else:
                    score = 0

                if score < best_score:
                    best_score = score
                    best = (thL, thR)

            if best is None:
                new_pts.append((x, y, None, None))
            else:
                thL, thR = best
                new_pts.append((x, y, thL, thR))
                prev_L, prev_R = thL, thR  # update

        output.append({
            "curve_id": cid,
            "points": new_pts
        })

    return output




# =========================================
#  stepとして保存
# =========================================
import csv

STEP_DEG = 1.8  # 1ステップ = 1.8度

def convert_result_to_steps(result, out_csv="abs_steps.csv"):
    """
    result（genrad_kdtree の返り値）から角度を取り出し、
    絶対ステップへ変換し、前と同じ角度は削除して CSV に保存する。

    CSV形式: curve_id, abs_step_L, abs_step_R
    return: [(cid, abs_L, abs_R), ...]
    """

    rows = []
    out_list = []

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["curve_id", "abs_step_L", "abs_step_R"])

        for curve in result:
            cid = curve["curve_id"]
            pts = curve["points"]

            prev_L = None
            prev_R = None

            for p in pts:
                if len(p) < 4:
                    continue
                x, y, thL, thR = p

                # IK 失敗点は除外
                if thL is None or thR is None:
                    continue

                # 絶対ステップへ変換
                abs_L = round(thL / STEP_DEG)
                abs_R = round(thR / STEP_DEG)

                # 🚫 前回と同じステップならスキップ
                if prev_L is not None and abs_L == prev_L and abs_R == prev_R:
                    continue

                # 保存
                writer.writerow([cid, abs_L, abs_R])
                rows.append([cid, abs_L, abs_R])
                out_list.append((cid, abs_L, abs_R))

                prev_L = abs_L
                prev_R = abs_R

    print(f"絶対ステップ CSV 出力完了 → {out_csv}")
    return out_list
