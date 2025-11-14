from pathlib import Path
import cv2
from library import detect_face_once, line_drawing_image, convert_to_svg

BASE_DIR = Path(__file__).resolve().parent

# =========================
#   📷 カメラで撮影
# =========================
print("カメラを起動します... (Space: 撮影 / q: 終了)")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ カメラが開けません")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ フレーム取得失敗")
        break

    cv2.imshow("Camera Preview", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord(' '):  # Space → シャッター
        captured_path = BASE_DIR / "captured.jpg"
        cv2.imwrite(str(captured_path), frame)
        print(f"📷 撮影 → {captured_path}")
        break

    elif key in [ord('q'), 27]:
        cap.release()
        cv2.destroyAllWindows()
        exit()

cap.release()
cv2.destroyAllWindows()

# =========================
#   🖼️ 撮影画像を読み込む
# =========================
input_file = BASE_DIR / "captured.jpg"
img = cv2.imread(str(input_file))
if img is None:
    print("画像読み込み失敗:", input_file)
    exit()

# =========================
#   👤 顔検出 (1回のみ)
# =========================
faces = detect_face_once(img)
print(f"🔍 検出された顔の数: {len(faces)}")

face_strength = 40
cloth_strength = 120

WINDOW_NAME = "Line Adjustment"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)

print("""
==== 操作 ====
z: 服を薄く / x: 服を濃く
a: 顔を薄く / s: 顔を濃く
Enter: 保存 → SVG化へ進む
q / Esc: 中断
================
""")

while True:
    line_img = line_drawing_image(img, face_strength, cloth_strength, faces)

    display_img = cv2.cvtColor(line_img, cv2.COLOR_GRAY2BGR)
    for (x,y,w,h) in faces:
        cv2.rectangle(display_img, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.imshow(WINDOW_NAME, display_img)
    key = cv2.waitKey(30) & 0xFF

    if key == ord('z'): cloth_strength = max(5, cloth_strength - 5)
    elif key == ord('x'): cloth_strength = min(300, cloth_strength + 5)
    elif key == ord('a'): face_strength = max(5, face_strength - 5)
    elif key == ord('s'): face_strength = min(200, face_strength + 5)
    elif key == 13:
        print("✅ 保存します")
        break
    elif key in [ord('q'), 27]:
        cv2.destroyAllWindows()
        exit()

cv2.destroyAllWindows()

output_line = BASE_DIR / "line_output_dualcontrol.jpg"
cv2.imwrite(str(output_line), line_img)
print(f"✅ 線画保存 → {output_line}")

# =========================
#   ✒️ SVG 変換 + vpype 最適化
# =========================
convert_to_svg(
    line_jpg=output_line,
    debug_jpg=BASE_DIR / "line_debug.jpg",
    bitmap_pgm=BASE_DIR / "line_bitmap.pgm",
    raw_svg=BASE_DIR / "line_raw.svg",
    final_svg=BASE_DIR / "line_final.svg"
)
