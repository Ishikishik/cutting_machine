from svg2list import parse_svg, export_to_numpy, normalize_segments_mm

svg_data = parse_svg("makegcode/line_raw.svg")
arr = export_to_numpy(svg_data, debug_txt_path="debug_points.txt")

print(arr)

# 正規化
norm_segments = normalize_segments_mm(
    arr,
    target_w_mm=100,
    target_h_mm=148,
    offset_x_mm=10,
    offset_y_mm=5,
    rotate_deg=90,
    debug_txt_path="debug_norm.txt",
    debug_img_path="debug_norm2.png"
)