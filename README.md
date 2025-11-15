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
│
├── simulate/                     # 方針：simulate でコードを作り、本番へ移植する
│   ├── docker-compose.yml
│   ├── dockerfile                # simulate/work を動かすための環境設定
│   └── work/
│        ├── testkadoiki/         # 可動域確認コード（Fail：良い結果が得られず）
│        ├── gyakuunndo/          # 順運動学・逆運動学のコード（ipynbで動作）
│        └── makegcode/           # SVG→角度指示ファイル生成（作りかけ）
│
├── hard/
│   ├── software/                 # モーター・ソレノイド制御（未着手）
│   └── hardware/                 # 筐体の 3D データ（Fusion360）
│       ├── fusion                # 筐体のfusionデータ(.f3df)
|       └── 3mf                   #筐体の3dプリンター用データ(.3mf)
|
└── README.md                     # このファイル
```