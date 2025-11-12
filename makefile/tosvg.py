import cv2
import subprocess
import os

# ====== 入力と出力 ======
input_file = "line_output_dualcontrol.jpg"   # ここはあなたが生成した線画
debug_jpg  = "line_debug_original.jpg"       # ↓ デバッグ用そのまま保存
bitmap_pgm = "line_bitmap.pgm"               # potrace入力用（1bitではなくPGM）
raw_svg    = "line_raw.svg"                  # potrace直後
final_svg  = "line_final.svg"                # vpype後＝プロッター用

# ====== 線画を読み込み ======
line_img = cv2.imread(input_file, cv2.IMREAD_GRAYSCALE)
if line_img is None:
    print("❌ 画像が読み込めませんでした。ファイル名を確認してください。")
    exit()

# ✅ デバッグ用に「線画そのまま」を保存（重要）
cv2.imwrite(debug_jpg, line_img)
print(f"📝 デバッグ画像（元の線画そのまま）を保存 → {debug_jpg}")

# ====== PGM形式に反転して保存（ここが重要） ======
# 黒線 + 白背景 が potrace にとって最も良い
line_inv = cv2.bitwise_not(line_img)
cv2.imwrite(bitmap_pgm, line_inv)

# ====== ① potrace による SVG ベクトル化 ======
subprocess.run([
    "potrace",
    bitmap_pgm,
    "--svg",
    "-t", "4",       # 細かいノイズ抑制
    "-a", "1.2",     # 曲線スムージング
    "-O", "0.25",    # 角を自然に丸める
    "-o", raw_svg
])
print(f"✅ potrace により SVG 生成 → {raw_svg}")

# ====== ② vpype を使って線を最適化（プロッター描画速度が劇的に向上） ======
subprocess.run([
    "vpype",
    "read", raw_svg,
    "linemerge",     # つながる線を結合 → ペンの上下回数が減る
    "linesort",      # 描画順を最適化 → 無駄な移動が減る
    "simplify",      # 細かいガタガタを除去
    "write", final_svg
])
print(f"🎨 vpype により描画用に最適化 → {final_svg}")

print("\n✅ 完了しました！ このファイルをプロッターに送ってください ✨")
