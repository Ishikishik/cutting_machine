import cv2
import subprocess
import os

def line_drawing_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.adaptiveThreshold(gray_blurred, 255,
                                  cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 11, 7)
    return edges

input_file = "line_output_dualcontrol.jpg"
bitmap_file = "line_bitmap.pbm"
initial_svg = "line_raw.svg"
optimized_svg = "line_optimized.svg"
debug_save = "line_debug_original.png"

# 画像読み込み
img = cv2.imread(input_file)
line_img = line_drawing_image(img)

# デバッグ用保存
cv2.imwrite(debug_save, line_img)
print(f"📝 元の線画を保存 → {debug_save}")

# 反転（黒線・白背景）
line_for_trace = cv2.bitwise_not(line_img)

# PBM で保存
cv2.imwrite(bitmap_file, line_for_trace)

# ✅ ポトレース（ノイズ除去 & スムーズ化オプション付き）
subprocess.run([
    "potrace",
    bitmap_file,
    "--svg",
    "-t", "8",       # 小さい線を無視（大事）
    "-a", "1.0",     # スムース化強
    "-O", "0.3",     # 角丸め（汚れ除去）
    "-o", initial_svg
])

print(f"✅ SVG（一次変換）→ {initial_svg}")

# ✅ vpype による線の整理（描画を劇的に速く）
subprocess.run([
    "vpype",
    "read", initial_svg,
    "linemerge",      # つながる線は繋げる → ペン上下が減る
    "linesort",       # 描画順最適化 → 無駄な移動が減る
    "simplify",       # 細かいガタガタを整理 → 綺麗な線になる
    "write", optimized_svg
])

print(f"🎨 最適化済み SVG → {optimized_svg}")

print("\n✅ 完了しました！ この SVG をプロッターに送ると描画が綺麗 & 速いです ✨")
