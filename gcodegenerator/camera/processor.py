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
# JPG から画像を読み込む
# -------------------------------------------------------
def load_image_from_file(image_path):
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"❌ 画像読み込み失敗: {image_path}")
    print(f"🖼 画像ファイルを読み込みました: {image_path}")
    return img


# -------------------------------------------------------
# findContours → 曲線抽出
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
# カメラ撮影で画像を取得
# -------------------------------------------------------
def capture_image_from_camera():

    print("カメラを起動します... (Space: 撮影 / q: 終了)")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("❌ カメラが開けません")

    PREVIEW_W = 2000
    PREVIEW_H = 2960

    cv2.namedWindow("Camera Preview", cv2.WINDOW_NORMAL)

    img = None

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("❌ フレーム取得失敗")
            continue

        preview = crop_to_aspect(frame, PREVIEW_W, PREVIEW_H)
        faces_live = detect_face_once(preview)

        preview_display = preview.copy()
        for (x, y, w, h) in faces_live:
            cv2.rectangle(preview_display, (x, y, w, h), (0, 255, 0), 2)
            cv2.putText(preview_display, "FACE", (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Camera Preview", preview_display)

        key = cv2.waitKey(10) & 0xFF

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

    return img


# -------------------------------------------------------
# 親 main から呼び出す統合関数（camera / image）
# -------------------------------------------------------
def capture_and_extract_curve_list(
        source="camera",
        image_path=None
    ):
    """
    source="camera" → カメラ撮影
    source="image"  → JPEGから読み込み
    """

    # -------------------------
    # 画像入力
    # -------------------------
    if source == "camera":
        img = capture_image_from_camera()
        if img is None:
            print("中断されました")
            return None

    elif source == "image":
        if image_path is None:
            raise ValueError("❌ source='image' では image_path が必要です")
        img = load_image_from_file(image_path)

    else:
        raise ValueError(f"❌ 不明な source 指定: {source}")

    # -------------------------
    # 縦横比補正
    # -------------------------
    TARGET_W = 1000
    TARGET_H = 1480
    img = resize_with_aspect(img, TARGET_W, TARGET_H)

    # -------------------------
    # 顔検出
    # -------------------------
    faces = detect_face_once(img)

    # -------------------------
    # 調整ウィンドウ
    # -------------------------
    face_strength = 40
    cloth_strength = 120
    curve_count = 70

    cv2.namedWindow("Line Adjustment", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("Curve Preview", cv2.WINDOW_AUTOSIZE)

    while True:
        line_img = line_drawing_image(img, face_strength, cloth_strength, faces)

        disp = cv2.cvtColor(line_img, cv2.COLOR_GRAY2BGR)
        for (x, y, w, h) in faces:
            cv2.rectangle(disp, (x, y, w, h), (0, 255, 0), 2)
        cv2.imshow("Line Adjustment", disp)

        curve_preview = preview_curve_groups(line_img, curve_count)
        cv2.imshow("Curve Preview", curve_preview)

        key = cv2.waitKey(30) & 0xFF

        # 曲線数変更
        if key == ord('p'):
            curve_count = max(5, curve_count - 5)
        elif key == ord('o'):
            curve_count = min(200, curve_count + 5)

        # 閾値調整
        elif key == ord('l'):
            face_strength = max(5, face_strength - 5)
        elif key == ord('k'):
            face_strength = min(200, face_strength + 5)
        elif key == ord('m'):
            cloth_strength = max(5, cloth_strength - 5)
        elif key == ord('n'):
            cloth_strength = min(300, cloth_strength + 5)

        elif key == 13:  # ENTER
            break

        elif key in [27]:  # ESC
            cv2.destroyAllWindows()
            return None

    cv2.destroyAllWindows()

    # -------------------------
    # 曲線リスト抽出
    # -------------------------
    return extract_curve_list(line_img, max_curves=curve_count)




