from pathlib import Path
import cv2
import numpy as np
from .library import (
    detect_face_once,
    line_drawing_image,
    resize_with_aspect,
    crop_to_aspect,
    preview_curve_groups
)

BASE_DIR = Path(__file__).resolve().parent

# -------------------------------------------------------
# 色決定（固定色アルゴリズム）
# -------------------------------------------------------
def id_to_color(i):
    hue = int((i * 37) % 180)
    hsv = np.uint8([[[hue, 200, 255]]])
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


# -------------------------------------------------------
# 輪郭抽出 → 曲線データ返す
# -------------------------------------------------------
def extract_curve_list(line_img, max_curves=70, min_points=5):
    if len(line_img.shape) == 3:
        gray = cv2.cvtColor(line_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = line_img

    _, th = cv2.threshold(gray, 0, 255,
                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = 255 - th

    contours, _ = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours = [c for c in contours if len(c) >= min_points]

    contours = sorted(
        contours,
        key=lambda c: cv2.arcLength(c, closed=False),
        reverse=True
    )[:max_curves]

    curve_list = []

    for idx, cnt in enumerate(contours, start=1):
        pts = cnt.reshape(-1, 2)
        pts_list = [(int(x), int(y)) for (x, y) in pts]
        curve_list.append({"curve_id": idx, "points": pts_list})

    return curve_list


# -------------------------------------------------------
# 親ディレクトリの main から呼び出す関数
# -------------------------------------------------------
def capture_and_extract_curve_list():
    print("カメラを起動します... (Space: 撮影 / q: 終了)")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("❌ カメラが開けません")

    PREVIEW_W = 2000
    PREVIEW_H = 2960

    cv2.namedWindow("Camera Preview", cv2.WINDOW_NORMAL)

    # --------------------
    # 撮影フェーズ
    # --------------------
    img = None  # ← 必ず初期化

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("❌ フレーム取得失敗")
            continue

        # ---- プレビュー用にクロップ ----
        preview = crop_to_aspect(frame, PREVIEW_W, PREVIEW_H)

        # ---- 顔検出（プレビューに対して）----
        faces_live = detect_face_once(preview)

        # ---- プレビュー描画 ----
        preview_display = preview.copy()
        for (x, y, w, h) in faces_live:
            cv2.rectangle(preview_display, (x, y, w, h), (0, 255, 0), 2)
            cv2.putText(preview_display, "FACE", (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Camera Preview", preview_display)

        key = cv2.waitKey(10) & 0xFF  # macOS は 10 の方が安定

        if key == ord(' '):  # 撮影
            img = frame.copy()
            captured_path = BASE_DIR / "captured.jpg"
            cv2.imwrite(str(captured_path), img)
            print(f"📷 撮影 → {captured_path}")
            break

        elif key in [ord('q'), 27]:
            cap.release()
            cv2.destroyAllWindows()
            return None

    cap.release()
    cv2.destroyAllWindows()

    # ---- imgがNoneなら撮影失敗 ----
    if img is None:
        print("❌ 撮影された画像がありません（img が None）")
        return None

    # --------------------
    # 縦横比補正
    # --------------------
    TARGET_W = 1000
    TARGET_H = 1480
    img = resize_with_aspect(img, TARGET_W, TARGET_H)

    # --------------------
    # 顔検出（本番画像）
    # --------------------
    faces = detect_face_once(img)

    # --------------------
    # 調整ウィンドウ
    # --------------------
    face_strength = 40
    cloth_strength = 120

    WINDOW_NAME = "Line Adjustment"
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)

    curve_count = 70
    cv2.namedWindow("Curve Preview", cv2.WINDOW_AUTOSIZE)

    while True:
        # 線画化
        line_img = line_drawing_image(img, face_strength, cloth_strength, faces)

        # プレビュー1
        display_img = cv2.cvtColor(line_img, cv2.COLOR_GRAY2BGR)
        for (x, y, w, h) in faces:
            cv2.rectangle(display_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imshow(WINDOW_NAME, display_img)

        # プレビュー2（曲線）
        curve_preview = preview_curve_groups(line_img, curve_count)
        cv2.rectangle(curve_preview, (0, curve_preview.shape[0] - 25),
                      (curve_preview.shape[1], curve_preview.shape[0]),
                      (0, 0, 0), -1)
        cv2.putText(curve_preview,
                    f"Curve Count: {curve_count}",
                    (10, curve_preview.shape[0] - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1)
        cv2.imshow("Curve Preview", curve_preview)

        key = cv2.waitKey(30) & 0xFF

        # 線の本数調整
        if key == ord('p'):
            curve_count = max(5, curve_count - 5)
        elif key == ord('o'):
            curve_count = min(200, curve_count + 5)

        # 顔・服の強さ調整
        elif key == ord('l'):
            face_strength = max(5, face_strength - 5)
        elif key == ord('k'):
            face_strength = min(200, face_strength + 5)
        elif key == ord('m'):
            cloth_strength = max(5, cloth_strength - 5)
        elif key == ord('n'):
            cloth_strength = min(300, cloth_strength + 5)

        elif key == 13:   # ENTER
            break
        elif key in [27]:
            cv2.destroyAllWindows()
            return None

    cv2.destroyAllWindows()

    # ------------------------------------------------
    # 最終 result（曲線データリスト）を返す
    # ------------------------------------------------
    return extract_curve_list(line_img, max_curves=curve_count)
