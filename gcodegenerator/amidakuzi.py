import random
from PIL import Image, ImageDraw


def generate_amida(
    output_path="amida.png",
    width=910,
    height=550,
    num_lines=24,
    margin_x=80,
    margin_top=100,
    margin_bottom=100,
    num_rows=10,
    seed=None
):
    if seed is not None:
        random.seed(seed)

    if num_lines < 2:
        raise ValueError("num_lines は2以上必要です。")

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # 縦線位置
    xs = [
        margin_x + i * (width - 2 * margin_x) / (num_lines - 1)
        for i in range(num_lines)
    ]

    top_y = margin_top
    bottom_y = height - margin_bottom

    # 横線候補
    ys = [
        top_y + (k + 1) * (bottom_y - top_y) / (num_rows + 1)
        for k in range(num_rows)
    ]

    # 横線生成
    rungs = []
    for y in ys:
        i = 0
        while i < num_lines - 1:
            if random.random() < 0.4:
                rungs.append((i, y))
                i += 2
            else:
                i += 1

    # 最低1本保証
    if len(rungs) == 0:
        forced_i = random.randint(0, num_lines - 2)
        forced_y = random.choice(ys)
        rungs.append((forced_i, forced_y))

    # ===== 描画 =====

    # 縦線
    for x in xs:
        draw.line((x, top_y, x, bottom_y), fill="black", width=5)

    # 横線
    for i, y in rungs:
        draw.line((xs[i], y, xs[i + 1], y), fill="black", width=5)

    # 上の丸（1つだけ）
    start_index = random.randint(0, num_lines - 1)
    x = int(xs[start_index])
    y = top_y - 30
    r = 20
    draw.line((x - r, y - r, x + r, y + r), fill="black", width=3)
    draw.line((x - r, y + r, x + r, y - r), fill="black", width=3)

    # ===== 回転 =====
    img = img.rotate(-90, expand=True)

    img.save(output_path)

    print("saved:", output_path)
    print("lines:", num_lines)
    print("horizontal lines:", len(rungs))


if __name__ == "__main__":
    generate_amida(num_lines=10, seed=998244353)