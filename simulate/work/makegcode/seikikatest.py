from svg2list import parse_svg, export_to_numpy, normalize_segments_mm
import matplotlib.pyplot as plt
import numpy as np

svg_data = parse_svg("makegcode/line_raw.svg")
arr = export_to_numpy(svg_data, debug_txt_path="debug_points.txt")

print(arr)

# arr = export_to_numpy(...) の想定

plt.figure(figsize=(6, 10))

for seg in arr:
    seg = np.array(seg)
    plt.plot(seg[:, 0], seg[:, 1], linewidth=0.7)

plt.gca().invert_yaxis()  # SVG座標はy軸が下に向くので揃える
plt.axis("equal")
plt.show()
