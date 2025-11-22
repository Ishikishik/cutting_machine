```
project-root/
├── camera/                       # 写真撮影 → SVG 生成までを行う
│   ├── main.py                   # 実行すると撮影〜SVG生成まで自動で実施
│   ├── library.py                # main.py で使用する処理まとめ
│   └── haarcascade_frontalface_default.xml  # 顔認識用データ（library.py が使用）
│
├── makegcode/                    # SVG → 回転角リスト(G-code相当)生成（未着手）
│
├── test/
│   └── test(camera)/             # camera モジュールのテスト用コード
│   └── test(makelistdontusesvg)/             # svgにせずに線として区別するアルゴリズムを作成
│
├── simulate/                     # 方針：simulate でコードを作り、本番へ移植する
│   ├── docker-compose.yml
│   ├── dockerfile                # simulate/work を動かすための環境設定
│   └── work/
│        ├── testkadoiki/         # 可動域確認コード（Fail：良い結果が得られず）
│        ├── gyakuunndo/          # 順運動学・逆運動学のコード（ipynbで動作）
│        └── makegcode(test)/     # SVG→角度指示ファイル生成（作りかけ）
│        └── makegcode/           # SVG→角度指示ファイル生成(うん本物)
│
├── hard/
│   ├── software/                 # モーター・ソレノイド制御（未着手）
│   └── hardware/                 # 筐体の 3D データ（Fusion360）
│       ├── fusion                # 筐体のfusionデータ(.f3df)
|       └── 3mf                   #筐体の3dプリンター用データ(.3mfもしくは.stl)
|
└── README.md                     # このファイル



├── gcodegenerator/               # 写真撮影 → Gcode 生成までを行う
│   │── main.py                   # gcodegeneratorを回すメインループ
│   ├── camera/                   # 実行すると撮影〜SVG生成まで自動で実施
│   │    ├── prosessor.py               # main.py で使用する処理まとめ(カメラ系)
│   │    ├── library.py            # prosessor.py で使用する処理まとめ
│   │    ├──haarcascade_frontalface_default.xml  # 顔認識用データ（library.py が使用）
│   │    └── __init__.py           # お守り
│   │
│   ├── list2gcode/                # 実行すると撮影〜SVG生成まで自動で実施
│   │    ├── processor.py          # 画像リスト受け取りからgcode作成までを担当する
│   │    ├── list2goodlist.py      # 画像リスト受け取り、回転、位置調整、圧縮、書く順番極めまでを担当
│   │    ├── __init__.py           # お守り
│   │    └── haarcascade_frontalface_default.xml  # 顔認識用データ（library.py が使用）
│   │
```


私が使っているステッピングモーターは1step1.8度なのですが、abs_step_Lは左側のモーターが初期位置から時計回りに何ステップ目のところに点があるか、abs_step_Rは右側のモーターが反時計回り何ステップ目のところに点があるかです。いわば絶対ステップです。大体1500行あります。
これを辿るようなコードを書いて欲しいです。ただし、初期位置は本来ならばモーターの真横の線とするのですが、腕が回らないので、両方とも+45度のところにセットします
curve_id,abs_step_L,abs_step_R
1,60,4
1,59,4
1,59,5
1,59,6
1,58,6
1,58,7
1,57,7
1,57,8
1,57,9
1,56,9
1,55,9
1,55,10
1,55,11
1,54,11
1,54,12
1,54,13
1,53,13
1,52,13
1,52,14
1,51,14
1,50,14
1,50,15
