from pathlib import Path
from camera.processor import capture_and_extract_curve_list
from list2gcode.processor import (
    sort_curves_tsp,
    export_curve_csv,
    generate_rotandscale_curves,
    genrad_kdtree,
    convert_result_to_steps,
    stepcsv2list,
    apply_grid_calibration
)
BASE_DIR = Path(__file__).resolve().parent   

"""
curve_list = capture_and_extract_curve_list(source="camera")
"""
curve_list = capture_and_extract_curve_list(
    source="image",
    image_path=str(BASE_DIR / "qiita.png" ),
    TARGET_W = 700,
    TARGET_H = 1200
)

if curve_list is None:
    print("中断されました")
else:
    # --- 曲線内部順序済みの curve_list が来る前提 ---

    sorted_list = sort_curves_tsp(curve_list)

    final_curves = generate_rotandscale_curves(
        sorted_list,
        rotate_deg = 270,      # 90°回転
        box_w = 120,          # ハガキ短辺
        box_h = 70,          # ハガキ長辺
        offset_x = -91/2,        # →方向に 10mm 移動
        offset_y = -120/2 + 110,        # ↓方向に -5mm 移動//70:近すぎる
        decimal_digits = 3,    # 小数点以下3桁
        mode = "postcard"
)
    
    corrected_curves = apply_grid_calibration(
     final_curves,
     str(BASE_DIR /"grid_calib.csv")
    )



    result = genrad_kdtree(
    corrected_curves,
    lut_path=str(BASE_DIR / "1-16lut_tree.pkl")
)
    step_list = convert_result_to_steps(result, out_csv=str(BASE_DIR / "csvdata" /"steps_for_raspi.csv"))


    # CSV に保存
    export_curve_csv(result, str(BASE_DIR / "csvdata" /"output_curves.csv"))
    stepcsv2list(csv_path = str(BASE_DIR / "csvdata" /"steps_for_raspi.csv"), out_path = (BASE_DIR / ".." / "hard" / "software" / "cuttingsoft" / "steps.h").resolve())