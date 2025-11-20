from camera.processor import capture_and_extract_curve_list
from list2gcode.processor import (
    sort_curves_tsp,
    export_curve_csv,
)

curve_list = capture_and_extract_curve_list()

if curve_list is None:
    print("中断されました")
else:
    # --- 曲線内部順序済みの curve_list が来る前提 ---

    sorted_list = sort_curves_tsp(curve_list)

    # CSV に保存
    export_curve_csv(sorted_list, "output_curves.csv")
