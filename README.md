```
.
├── gcodegenerator
│   ├── camera
│   │   ├── captured.jpg                            #cameraでとった画像
│   │   ├── haarcascade_frontalface_default.xml     #顔検知のための.xml
│   │   ├── library.py                              #cameraで使うlibrary
│   │   └── processor.py                            #写真を撮って(画像から)リストを作る、
│   ├── list2gcode
│   │   ├── list2goodlist.py                        #選んだ点を曲線に分割、順番を決定
│   │   ├── makegcode.py                            #ソートされた曲線を角度に変換
│   │   └── processor.py                            #上二つの.pyを統合
│   ├── output_curves.csv                           #順番、カーブ、角度の対応
│   ├── qiita.png                                   #ベンチマーク
│   ├── csvcheck(rad).py                            #角度からペンプロッターをシミュレーション
│   ├── csvcheck(xy).py                             #ソートしたxyをシミュレーション
│   ├── main.py                                     #画像からgcodeを作る(これを実行する)
│   └── caribrate                                   #キャリブレーションに関するコード群 
│   │   ├── carib.py                                #歪ませるためのcsvを生成
│   │   ├── caribgcode.py                           #キャリブレーションに必要な.hを生成する。(一回作っておけばいらないかも)
│   │   ├── aruco_0~3.py                            #arucoマーカー
│   │   ├── drowcarib.py                                #キャリブレーションに必要な.hを生成する。(一回作っておけばいらないかも)
│   │   ├── drowcarib.py                                #キャリブレーションに必要な.hを生成する。(一回作っておけばいらないかも)
│   │   ├── drowcarib.py                                #キャリブレーションに必要な.hを生成する。(一回作っておけばいらないかも)
│   │   └── calib.py                                    #キャリブレーション用の補正点を画像から生成する。
│
│   ├── drowcarib.py                                #キャリブレーションに必要な.hを生成する。(一回作っておけばいらないかも)
│   └── calib.py                                    #キャリブレーション用の補正点を画像から生成する。



│
├── hard
│   ├── hardware                                    #ハードウェアの設計データ
│   │   ├── 3mf                                     #ハードウェアの3mfとかstl
│   │   └── fusion                                  #fusion360のデータ
│   └── software                                    #ハードウェアのソフトウェアデータ
│       └── cuttingsoft                             #cuttingsoft
│           ├── cuttingsoft.ino                     #ラズピコの.ino
│           └── steps.h                             #角度の制御データ
├── makerad2csvlist                                 #xyから角度に変換する決定木を作る
│   ├── 1-16angles_to_xy.csv                        #xyから角度に変換する.csv
│   ├── csv2kdtree.py                               #csvをkdtreeに変換する
│   └── rad2csv.py                                  #シミュレーションしてcsvの変換表を作る
├── README.md                                       #このリポジトリの説明
│
│
├── simulate(test)                                  #これから下はテスト(特に解説はしない)
└── test

```

