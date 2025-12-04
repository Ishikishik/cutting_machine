from pathlib import Path
from list2gcode.processor import (
    export_curve_csv,
    genrad_kdtree,
    convert_result_to_steps,
    stepcsv2list
)
BASE_DIR = Path(__file__).resolve().parent   


final_curves = []        # 既存を完全に上書き
curve_id = 1

# x のリスト（-50 〜 +50, 間隔10）
x_list = list(range(-50, 51, 10))

# y のリスト（40 〜 90, 間隔10）
y_list = list(range(40, 91, 10))

for x in x_list:
    # 縦線：x固定、yだけ変化
    points = [(x, y) for y in y_list]

    final_curves.append({
        "curve_id": curve_id,
        "points": points
    })

    curve_id += 1

    result = genrad_kdtree(
    final_curves,
    lut_path=str(BASE_DIR / "1-16lut_tree.pkl")
)
    step_list = convert_result_to_steps(result, out_csv=str(BASE_DIR / "csvdata" /"steps_for_raspi.csv"))


    # CSV に保存
    export_curve_csv(result, str(BASE_DIR / "csvdata" /"output_curves.csv"))
    stepcsv2list(csv_path = str(BASE_DIR / "csvdata" /"steps_for_raspi.csv"), out_path = (BASE_DIR / ".." / "hard" / "software" / "cuttingsoft" / "carib.h").resolve())