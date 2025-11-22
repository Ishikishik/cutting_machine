from camera.processor import capture_and_extract_curve_list
from list2gcode.processor import (
    sort_curves_tsp,
    export_curve_csv,
    generate_rotandscale_curves,
    genrad_kdtree,
    convert_result_to_steps
)
"""
curve_list = capture_and_extract_curve_list(source="camera")
"""
curve_list = capture_and_extract_curve_list(
    source="image",
    image_path="/Users/kawashimasatoshishin/cutting_machine/gcodegenerator/qiita.png"
)

if curve_list is None:
    print("中断されました")
else:
    # --- 曲線内部順序済みの curve_list が来る前提 ---

    sorted_list = sort_curves_tsp(curve_list)

    final_curves = generate_rotandscale_curves(
        sorted_list,
        rotate_deg = 90,      # 90°回転
        box_w = 148,          # ハガキ短辺
        box_h = 100,          # ハガキ長辺
        offset_x = -148/2,        # →方向に 10mm 移動
        offset_y = 40,        # ↓方向に -5mm 移動
        decimal_digits = 3    # 小数点以下3桁
)
    result = genrad_kdtree(
    final_curves,
    lut_path="/Users/kawashimasatoshishin/cutting_machine/gcodegenerator/list2gcode/lut_tree.pkl"
)
    step_list = convert_result_to_steps(result, out_csv="steps_for_raspi.csv")


    # CSV に保存
    export_curve_csv(result, "output_curves.csv")
    print(final_curves)