import numpy as np
import cv2

# ---- 前処理 ----
def preprocess(gray):
    blur = cv2.bilateralFilter(gray, 7, 50, 50)
    kernel = np.ones((3,3), np.uint8)
    morph = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    edges = cv2.Canny(morph, 80, 150)
    return edges

# ---- 連続線追跡 ----
def trace_strokes(binary):
    h, w = binary.shape
    visited = np.zeros_like(binary, bool)
    strokes = []
    neigh = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

    for y in range(h):
        for x in range(w):
            if binary[y,x]==0 or visited[y,x]: continue
            stack=[(x,y)]
            stroke=[]
            while stack:
                cx,cy=stack.pop()
                if visited[cy,cx]: continue
                visited[cy,cx]=True
                stroke.append([cx,cy])
                for dx,dy in neigh:
                    nx,ny=cx+dx,cy+dy
                    if 0<=nx<w and 0<=ny<h and binary[ny,nx]>0 and not visited[ny,nx]:
                        stack.append((nx,ny))
            if len(stroke)>10:
                strokes.append(np.array(stroke,float))
    return strokes

# ---- 距離結合 ----
def merge_strokes(strokes, th=10):
    out=[]
    used=[False]*len(strokes)
    for i in range(len(strokes)):
        if used[i]: continue
        base=strokes[i].copy()
        end=base[-1]
        for j in range(len(strokes)):
            if used[j] or i==j: continue
            if np.linalg.norm(end-strokes[j][0])<th:
                base=np.vstack([base,strokes[j]])
                used[j]=True
                end=base[-1]
        out.append(base)
        used[i]=True
    return out

# ---- 中心マージ ----
def merge_by_center(strokes, dist=25):
    centers=[np.mean(s,0) for s in strokes]
    used=[False]*len(strokes)
    merged=[]
    for i in range(len(strokes)):
        if used[i]: continue
        big=strokes[i].copy()
        for j in range(len(strokes)):
            if used[j] or i==j: continue
            if np.linalg.norm(centers[i]-centers[j])<dist:
                big=np.vstack([big,strokes[j]])
                used[j]=True
        used[i]=True
        merged.append(big)
    return merged

# ---- パイプライン ----
def extract_strokes_pipeline(linejpg):
    gray=cv2.imread(linejpg,0)
    edges=preprocess(gray)
    s=trace_strokes(edges)
    s=[x for x in s if len(x)>40]
    s=merge_strokes(s, th=15)
    s=merge_by_center(s, dist=30)
    return s
