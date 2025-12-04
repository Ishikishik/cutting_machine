import cv2
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

def generate_aruco_png(size_mm=15, marker_id=0, dpi=300, dict_name=cv2.aruco.DICT_4X4_50):
    # mm→px変換
    inch = size_mm / 25.4
    px = int(inch * dpi)

    dictionary = cv2.aruco.getPredefinedDictionary(dict_name)
    marker = cv2.aruco.generateImageMarker(dictionary, marker_id, px)

    filename = f"aruco_{marker_id}.png"
    cv2.imwrite(filename, marker)
    return filename, px

def make_pdf_with_markers():

    # A4サイズ
    width, height = A4  # 595 x 842 pt

    c = canvas.Canvas("aruco_15mm_4markers.pdf", pagesize=A4)

    # 15mm角 = 約 42.5pt
    mm_to_pt = 72 / 25.4
    marker_pt = 15 * mm_to_pt

    # 4つ生成（IDは0〜3でOK）
    filenames = []
    for i in range(4):
        fname, px = generate_aruco_png(size_mm=15, marker_id=i)
        filenames.append(fname)

    # A4 にレイアウト（四隅）
    margin = 40  # 40pt くらい空ける
    positions = [
        (margin, height - margin - marker_pt),              # 左上
        (width - margin - marker_pt, height - margin - marker_pt),  # 右上
        (margin, margin),                                   # 左下
        (width - margin - marker_pt, margin)                # 右下
    ]

    # PDF に貼り付け
    for (x, y), fname in zip(positions, filenames):
        img = ImageReader(fname)
        c.drawImage(img, x, y, width=marker_pt, height=marker_pt)

    c.showPage()
    c.save()
    print("PDF 作成 → aruco_15mm_4markers.pdf")

make_pdf_with_markers()
