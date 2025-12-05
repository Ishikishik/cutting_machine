from pathlib import Path
from list2gcode.processor import (
    export_curve_csv,
    genrad_kdtree,
    convert_result_to_steps,
    stepcsv2list
)
BASE_DIR = Path(__file__).resolve().parent   

final_curves = []
curve_id = 1

# -----------------------------
# X と Y の範囲定義
# -----------------------------
x_list = list(range(-50, 51, 10))   # -50 ～ +50
start = 40 + 57/2                   # 68.5
end   = 91 + 57/2                   # 119.5
step  = 10

y_list = [start + i*step for i in range(int((end - start)/step) + 1)]


# -----------------------------
# ★ 縦線を追加
# -----------------------------
for x in x_list:
    points = [(x, y) for y in y_list]      # y方向に伸びる縦線
    final_curves.append({
        "curve_id": curve_id,
        "points": points
    })
    curve_id += 1


# -----------------------------
# ★ 横線を追加
# -----------------------------
for y in y_list:
    points = [(x, y) for x in x_list]      # x方向に伸びる横線
    final_curves.append({
        "curve_id": curve_id,
        "points": points
    })
    curve_id += 1


# -----------------------------
# IK変換 & 書き出し（ここで1回のみ）
# -----------------------------
result = genrad_kdtree(
    final_curves,
    lut_path=str(BASE_DIR / "1-16lut_tree.pkl")
)

step_list = convert_result_to_steps(
    result,
    out_csv=str(BASE_DIR / "csvdata" / "steps_for_raspi.csv")
)

export_curve_csv(
    result,
    str(BASE_DIR / "csvdata" / "output_curves.csv")
)

stepcsv2list(
    csv_path=str(BASE_DIR / "csvdata" / "steps_for_raspi.csv"),
    out_path=(BASE_DIR / ".." / "hard" / "software" / "cuttingsoft" / "carib.h").resolve()
)

print("★ 格子状（縦線 + 横線）のデータ生成が完了しました。")
