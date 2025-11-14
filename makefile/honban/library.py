from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent




import cv2
import numpy as np
import subprocess

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

def potrace_to_svg(bitmap_pgm, raw_svg):
    subprocess.run([
        "potrace",
        str(bitmap_pgm),
        "--svg",
        "--longcurve",
        "-t", str(turdsize),
        "-a", str(alphamax),
        "-O", str(opttolerance),
        "-o", str(raw_svg)
    ], check=True)
    print(f"✅ potrace → {raw_svg}")

def optimize_svg_with_vpype(raw_svg, final_svg):
    subprocess.run([
        "vpype",
        "read", raw_svg,
        "linemerge",
        "linesort",
        "simplify",
        "write", final_svg
    ])
    print(f"🎨 vpype最適化 → {final_svg}")

# === 線画 → SVG まで一発処理 ===
def convert_to_svg(line_jpg, debug_jpg, bitmap_pgm, raw_svg, final_svg):
    line_img = cv2.imread(line_jpg, cv2.IMREAD_GRAYSCALE)
    save_debug_image(line_img, debug_jpg)
    save_pgm_for_potrace(line_img, bitmap_pgm)
    potrace_to_svg(bitmap_pgm, raw_svg)
    optimize_svg_with_vpype(raw_svg, final_svg)
    print("\n✅ SVG 作成完了 →", final_svg)
