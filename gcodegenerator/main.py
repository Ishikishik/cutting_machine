# main.py

from camera.processor import capture_and_extract_curve_list
from list2gcode.processor import process_curve_list

curve_list = capture_and_extract_curve_list()

if curve_list is None:
    print("中断されました")
else:
    print("抽出された曲線数:", len(curve_list))
    print("サンプル:", curve_list[0])

    # 近似 → 並べ替え → 可視化
    good_list = process_curve_list(curve_list)

    print("処理後の曲線数:", len(good_list))
