import cv2
import numpy as np

# 顔検出器のパス（あなたの環境に合わせてあります）
face_cascade = cv2.CascadeClassifier("/Users/kawashimasatoshishin/cutting_machine/makefile/haarcascade_frontalface_default.xml")

def detect_face_once(smooth):
    faces = face_cascade.detectMultiScale(
        smooth,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )
    return faces

def line_drawing_image(img, face_strength, cloth_strength, faces):
    # グレースケール + ノイズ軽減
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # 服・背景の線の強さ
    edges = cv2.Canny(smooth, cloth_strength, cloth_strength * 2)

    # 顔だけ線を上書きする（強度独立）
    for (x, y, w, h) in faces:
        roi = smooth[y:y+h, x:x+w]
        face_edges = cv2.Canny(roi, face_strength, face_strength * 2)
        edges[y:y+h, x:x+w] = face_edges

    # 線を太らせる
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # 白背景 / 黒線
    return cv2.bitwise_not(edges)

# ==== 入力画像 ====
input_file = "test.jpg"
img = cv2.imread(input_file)

if img is None:
    print("画像が読み込めませんでした。")
    exit()

# ==== 顔検出は最初の一回だけ ====
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
smooth = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
faces = detect_face_once(smooth)
print(f"🔍 検出された顔の数: {len(faces)}")

# ==== パラメータ（後で可変抵抗に置き換える部分） ====
face_strength = 40      # 顔の線の強さ
cloth_strength = 120    # 服・背景の線の強さ

WINDOW_NAME = "Line Adjustment (Face Highlighted)"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)

print("""
==== 操作 ====
z: 服を薄く（cloth_strength ↓）
x: 服を濃く（cloth_strength ↑）
a: 顔を薄く（face_strength ↓）
s: 顔を濃く（face_strength ↑）
Enter: 決定して保存
q / Esc: 終了（保存なし）
================
""")

while True:
    line_img = line_drawing_image(img, face_strength, cloth_strength, faces)

    # 表示用 — 緑枠表示（保存に影響なし）
    display_img = line_img.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(display_img, (x, y), (x+w, y+h), (0,255,0), 2)

    cv2.imshow(WINDOW_NAME, display_img)

    key = cv2.waitKey(30) & 0xFF

    if key == ord('z'):
        cloth_strength = max(5, cloth_strength - 5)
        print(f"[服 弱く] cloth_strength = {cloth_strength}")

    elif key == ord('x'):
        cloth_strength = min(300, cloth_strength + 5)
        print(f"[服 強く] cloth_strength = {cloth_strength}")

    elif key == ord('a'):
        face_strength = max(5, face_strength - 5)
        print(f"[顔 弱く] face_strength = {face_strength}")

    elif key == ord('s'):
        face_strength = min(200, face_strength + 5)
        print(f"[顔 強く] face_strength = {face_strength}")

    elif key == 13:  # Enter
        print("✅ 確定して保存します")
        break

    elif key in [ord('q'), 27]:
        print("❌ 中断しました")
        cv2.destroyAllWindows()
        exit()

cv2.destroyAllWindows()

output_file = "line_output_dualcontrol.jpg"
cv2.imwrite(output_file, line_img)
print(f"✅ 保存完了 → {output_file}")
