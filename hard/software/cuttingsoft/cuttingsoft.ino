#include "steps.h"
//#include "carib.h"
// ===============================
// Pin assignments
// ===============================

// Motor A (LEFT)
#define DIR_A   16
#define STEP_A  17
#define MS_A    18

// Motor B (RIGHT)
#define DIR_B   19
#define STEP_B  20
#define MS_B    21
#define pulse   1000


//sorenoid
#define SOL 15

// motor step angle
const float motor_step_deg = 1.8;

// 現在ステップ位置（1/16単位）
long curA = 0;
long curB = 800;

// ---------------------------------------------
// DIR設定（あなたのモーター方向に完全対応）
// left(A)：CW=正方向 → false
// right(B)：CCW=正方向 → true
// ---------------------------------------------
void set_dir_A(bool positive) {
    digitalWrite(DIR_A, positive ? LOW  : HIGH); 
}

void set_dir_B(bool positive) {
    digitalWrite(DIR_B, positive ? HIGH : LOW);
}

// ---------------------------------------------
// 2モーター同時ステップ（micro=1 or 16）
// ---------------------------------------------
void move_to(long targetA, long targetB, int micro)
{
    // diff：絶対座標の差分（microstep単位）
    long diffA = targetA - curA;
    long diffB = targetB - curB;

    // microstep → 1パルスで進む量 micro=1→1, micro=16→16 microstep
    long stepsA = abs(diffA) / micro;
    long stepsB = abs(diffB) / micro;

    long maxSteps = max(stepsA, stepsB);
    if (maxSteps == 0) return;

    bool dirA = (diffA >= 0);
    bool dirB = (diffB >= 0);

    set_dir_A(dirA);
    set_dir_B(dirB);

    long cntA = 0;
    long cntB = 0;

    for (long i = 0; i < maxSteps; i++) {

        bool pulseA = false;
        bool pulseB = false;

        cntA += stepsA;
        if (cntA >= maxSteps) {
            cntA -= maxSteps;
            pulseA = true;
        }

        cntB += stepsB;
        if (cntB >= maxSteps) {
            cntB -= maxSteps;
            pulseB = true;
        }

        // ---- HIGH（同時） ----
        if (pulseA) digitalWrite(STEP_A, HIGH);
        if (pulseB) digitalWrite(STEP_B, HIGH);

        delayMicroseconds(pulse);

        // ---- LOW（同時） ----
        if (pulseA) digitalWrite(STEP_A, LOW);
        if (pulseB) digitalWrite(STEP_B, LOW);

        delayMicroseconds(pulse);
    }

    // microstep単位の絶対座標で更新
    curA = targetA;
    curB = targetB;
}


// ---------------------------------------------
// Fullstep高速 → microstep補正モード移動
// ---------------------------------------------
void go_with_full_and_micro(long targetA, long targetB)
{
    long diffA = targetA - curA;
    long diffB = targetB - curB;

    long fullA = diffA / 16;
    long fullB = diffB / 16;

    long fullTargetA = curA + fullA * 16;
    long fullTargetB = curB + fullB * 16;

    // ---- fullstep ----
    digitalWrite(MS_A, LOW);
    digitalWrite(MS_B, LOW);
    delayMicroseconds(pulse);
    move_to(fullTargetA, fullTargetB, 16);

    // ---- microstep補正 ----
    digitalWrite(MS_A, HIGH);
    digitalWrite(MS_B, HIGH);
    delayMicroseconds(pulse);
    move_to(targetA, targetB, 1);
}


// ---------------------------------------------
void setup() {
    pinMode(DIR_A, OUTPUT);
    pinMode(STEP_A, OUTPUT);
    pinMode(MS_A, OUTPUT);

    pinMode(DIR_B, OUTPUT);
    pinMode(STEP_B, OUTPUT);
    pinMode(MS_B, OUTPUT);
    pinMode(SOL, OUTPUT);
    digitalWrite(SOL, LOW);  // 初期はペンUP
}

void loop() {

    int prevCurve = -1;  

    for (int i = 0; i < sizeof(steps)/sizeof(steps[0]); i++) {

        int curve   = steps[i][0];
        int targetA = steps[i][1];
        int targetB = steps[i][2];

        if (curve != prevCurve) {
            // ---- 曲線グループが変化したとき（新しい線のスタート） ----

            // ① まずペンを上げる（移動用）
            digitalWrite(SOL, LOW);   // LOW = ペンUP（前提）
            delay(20);

            // ② ペンを上げた状態で開始点まで移動
            digitalWrite(MS_A, HIGH);
            digitalWrite(MS_B, HIGH);
            move_to(targetA, targetB, 1);

            // ③ 開始点に着いてからペンを下げて描画開始
            digitalWrite(SOL, HIGH);  // HIGH = ペンDOWN
            delay(20);
        }
        else {
            // ---- 同じ曲線を継続して描画 ----
            // すでにペンは下りている前提で、そのまま移動
            digitalWrite(SOL, HIGH);  // 念のためDOWNを維持
            digitalWrite(MS_A, HIGH);
            digitalWrite(MS_B, HIGH);
            move_to(targetA, targetB, 1);
        }

        prevCurve = curve;
    }

    // ---- 終了処理 ----
    digitalWrite(SOL, LOW);  // ペン上げ
    delay(25);
    move_to(0, 800, 1);      // お好みの待避位置

    while(1);
}
