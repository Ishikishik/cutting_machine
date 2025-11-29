from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent




import cv2
import numpy as np
import subprocess


# 縦横比を調節
def resize_with_aspect(img, target_w, target_h):
    th = target_h
    tw = target_w
    h, w = img.shape[:2]

    # すでに同じ比率ならそのまま
    if abs((w / h) - (tw / th)) < 1e-3:
        return cv2.resize(img, (tw, th))

    # 画像の方が横長 → 横を切る
    if w / h > tw / th:
        new_w = int(h * tw / th)
        x1 = (w - new_w) // 2
        img_cropped = img[:, x1:x1+new_w]
    
    # 画像の方が縦長 → 縦を切る
    else:
        new_h = int(w * th / tw)
        y1 = (h - new_h) // 2
        img_cropped = img[y1:y1+new_h, :]

    return cv2.resize(img_cropped, (tw, th))


#フレームの縦横比を変更
def crop_to_aspect(img, target_w, target_h):
    """
    入力画像 img を target_w:target_h の縦横比に中央でクロップする
    """
    h, w = img.shape[:2]
    target_ratio = target_w / target_h
    src_ratio = w / h

    # 横が余る場合 → 横をクロップ
    if src_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x1 = (w - new_w) // 2
        img_cropped = img[:, x1:x1 + new_w]
    else:
        # 縦が余る場合 → 縦をクロップ
        new_h = int(w / target_ratio)
        y1 = (h - new_h) // 2
        img_cropped = img[y1:y1 + new_h, :]

    # 目的サイズに縮小（引き伸ばしではなく比率は維持済み）
    return cv2.resize(img_cropped, (target_w, target_h))

# === 顔検出器 ===
face_cascade = cv2.CascadeClassifier(str(BASE_DIR / "haarcascade_frontalface_default.xml"))

# === 顔検出（1回のみ） ===
def detect_face_once(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    faces = face_cascade.detectMultiScale(
        smooth,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )
    return faces

# === 線画生成 (顔と服/背景で独立調整) ===
def line_drawing_image(img, face_strength, cloth_strength, faces):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    edges = cv2.Canny(smooth, cloth_strength, cloth_strength * 2)

    for (x, y, w, h) in faces:
        roi = smooth[y:y+h, x:x+w]
        face_edges = cv2.Canny(roi, face_strength, face_strength * 2)
        edges[y:y+h, x:x+w] = face_edges

    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    return cv2.bitwise_not(edges)

# === SVG 変換用処理 ===
def save_debug_image(line_img, debug_jpg):
    cv2.imwrite(debug_jpg, line_img)
    print(f"📝 デバッグ画像保存 → {debug_jpg}")

def save_pgm_for_potrace(line_img, bitmap_pgm):
    line_inv = cv2.bitwise_not(line_img)
    cv2.imwrite(bitmap_pgm, line_inv)


def preview_curve_groups(line_img, max_curves):
    if len(line_img.shape) == 3:
        gray = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = line_img

    _, th = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    th = 255 - th

    contours, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours = [c for c in contours if len(c) > 5]

    contours = sorted(
        contours,
        key=lambda c: cv2.arcLength(c, closed=False),
        reverse=True
    )[:max_curves]

    debug = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    for idx, cnt in enumerate(contours):
        color = id_to_color(idx)  # ← 色が固定される！
        for p in cnt.reshape(-1, 2):
            cv2.circle(debug, (p[0], p[1]), 1, color, -1)

    return debug



def id_to_color(i):
    """
    curve_id → 一意の色を返す（OpenCV BGR形式）
    Hue を i に応じて変えることで安定した色分けを実現
    """
    hue = int((i * 37) % 180)  # 180色中、37刻みで色を分散
    saturation = 200
    value = 255

    hsv = np.uint8([[[hue, saturation, value]]])
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])
