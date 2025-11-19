from PIL import Image

def get_aspect_ratio(image_path):
    """
    指定した画像の縦横比 (width, height, ratio) を返す
    ratio は width / height の値
    """
    with Image.open(image_path) as img:
        width, height = img.size

    ratio = width / height
    return width, height, ratio


# 使い方
img_path = "/Users/kawashimasatoshishin/cutting_machine/test/test(camera)/test(makelistdontusesvg)/captured.jpg"
w, h, r = get_aspect_ratio(img_path)

print(f"幅: {w}px")
print(f"高さ: {h}px")
print(f"縦横比 (幅/高さ): {r:.4f}")
print(f"比率表記: {w}:{h}")
