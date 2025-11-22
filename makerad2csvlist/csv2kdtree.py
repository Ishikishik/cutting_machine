import numpy as np
import pickle
from scipy.spatial import cKDTree

# CSV を読み込んだ直後に以下を実行して KD-tree を作る
def generate_kdtree_from_csv(csv_path="rad2xy.csv", out_pkl="lut_tree.pkl"):

    theta_L = []
    theta_R = []
    X = []
    Y = []

    with open(csv_path, "r", encoding="utf-8") as f:
        next(f)  # ヘッダ行をスキップ
        for line in f:
            thL, thR, x, y = line.strip().split(",")
            theta_L.append(float(thL))
            theta_R.append(float(thR))
            X.append(float(x))
            Y.append(float(y))

    theta_L = np.array(theta_L)
    theta_R = np.array(theta_R)
    X = np.array(X)
    Y = np.array(Y)

    # KD-tree 生成
    xy = np.column_stack([X, Y])
    tree = cKDTree(xy)

    # pkl 保存
    with open(out_pkl, "wb") as f:
        pickle.dump((tree, theta_L, theta_R), f)

    print("KD-tree を保存しました →", out_pkl)


# 実行
generate_kdtree_from_csv("/Users/kawashimasatoshishin/cutting_machine/makerad2csvlist/angles_to_xy.csv", "lut_tree.pkl")
