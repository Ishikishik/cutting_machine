import csv

csv_path = "steps_for_raspi.csv"
out_path = "steps_cpp.txt"  # C++配列を出力するファイル

result_lines = []

with open(csv_path, newline='') as f:
    reader = csv.reader(f)
    for row in reader:

        # --- 空行はスキップ ---
        if not row:
            continue

        # --- 要素数が3未満ならスキップ ---
        if len(row) < 3:
            continue

        # --- 数字に変換できない行（ヘッダー等）はスキップ ---
        try:
            cid  = int(row[0])
            absL = int(row[1])
            absR = int(row[2])
        except ValueError:
            continue

        # C++ 配列形式に変換
        result_lines.append(f"{{{cid}, {absL}, {absR}}},")

# ---- 書き込み ----
with open(out_path, "w") as f:
    f.write("steps[][3] = {\n")
    for line in result_lines:
        f.write("    " + line + "\n")
    f.write("};\n")

print("完了！ 出力:", out_path)
