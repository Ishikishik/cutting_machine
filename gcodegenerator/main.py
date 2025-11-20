from camera.processor import capture_and_extract_curve_list
from list2gcode.processor import (
    sort_curves_tsp,
    export_curve_csv,
    generate_rotandscale_curves
)

curve_list = capture_and_extract_curve_list()

if curve_list is None:
    print("中断されました")
else:
    # --- 曲線内部順序済みの curve_list が来る前提 ---

    sorted_list = sort_curves_tsp(curve_list)

    final_curves = generate_rotandscale_curves(
    sorted_list,
    rotate_deg = 90,    # ← 時計回り 90° 回す（例）
    box_w = 100,        # ← ハガキ短辺 mm
    box_h = 148,         # ← ハガキ長辺 mm
    decimal_digits = 3
)


    # CSV に保存
    export_curve_csv(final_curves, "output_curves.csv")
