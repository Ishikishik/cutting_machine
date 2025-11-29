#include "steps.h"
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
#define pulse   1500


//sorenoid
#define SOL 15

// motor step angle
const float motor_step_deg = 1.8;

// 現在ステップ位置（1/16単位）
long curA = 400;
long curB = 400;

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

// ---------------------------------------------
void loop() {

    int prevCurve = steps[0][0];

    // 初期位置は手動で (400,400) に合わせている前提

    for (int i = 0; i < sizeof(steps)/sizeof(steps[0]); i++) {

        int curve = steps[i][0];
        int targetA = steps[i][1];
        int targetB = steps[i][2];

    if (curve != prevCurve) {
        // curveが変わった時 → ペンを一度確実に上げる
        if (digitalRead(SOL) == HIGH) {
            digitalWrite(SOL, LOW);   // ペン上昇
            delay(20);
        }
        // 必要ならここで HIGH にして描き始める
        digitalWrite(SOL, LOW);      // ペン下降
        delay(20);

        digitalWrite(MS_A, HIGH);
        digitalWrite(MS_B, HIGH);
        move_to(targetA, targetB, 1);
    }
    else {
        // curve継続 → 描画を続ける
        digitalWrite(SOL, HIGH);  // ペンを下げたまま
        digitalWrite(MS_A, HIGH);
        digitalWrite(MS_B, HIGH);
        move_to(targetA, targetB, 1);
    }


        prevCurve = curve;
    }
    digitalWrite(SOL, LOW);      // ペン上げる
    delay(25);
    move_to(400, 400, 1);
    while(1);

}