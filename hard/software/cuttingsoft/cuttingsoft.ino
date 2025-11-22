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
    long diffA = targetA - curA;
    long diffB = targetB - curB;

    int dirA = (diffA >= 0);
    int dirB = (diffB >= 0);

    long stepsA = abs(diffA);
    long stepsB = abs(diffB);

    long maxSteps = max(stepsA, stepsB);

    // DIR設定（あなたの定義に合わせて）
    set_dir_A(dirA);
    set_dir_B(dirB);

    for (long i = 0; i < maxSteps; i++) {

        if (i < stepsA) digitalWrite(STEP_A, HIGH);
        if (i < stepsB) digitalWrite(STEP_B, HIGH);

        delayMicroseconds(1000);

        digitalWrite(STEP_A, LOW);
        digitalWrite(STEP_B, LOW);

        delayMicroseconds(1000);
    }

    // 位置更新
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

    // fullstep で行ける分だけ動かす
    long fullA = diffA / 16;   // ← 1フルステップ = 16マイクロステップ
    long fullB = diffB / 16;

    long fullTargetA = curA + fullA * 16;
    long fullTargetB = curB + fullB * 16;

    // ---- fullstep ----
    digitalWrite(MS_A, LOW);
    digitalWrite(MS_B, LOW);
    move_to(fullTargetA, fullTargetB, 1);

    // ---- microstep で残りを補正 ----
    digitalWrite(MS_A, HIGH);
    digitalWrite(MS_B, HIGH);
    move_to(targetA, targetB, 16);
}

// ---------------------------------------------
void setup() {
    pinMode(DIR_A, OUTPUT);
    pinMode(STEP_A, OUTPUT);
    pinMode(MS_A, OUTPUT);

    pinMode(DIR_B, OUTPUT);
    pinMode(STEP_B, OUTPUT);
    pinMode(MS_B, OUTPUT);
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
            // curve切替 → fullstep高速→micro補正
            go_with_full_and_micro(targetA, targetB);
        } else {
            // 同じcurve → microstepで通常移動
            digitalWrite(MS_A, HIGH);
            digitalWrite(MS_B, HIGH);
            move_to(targetA, targetB, 16);
        }

        prevCurve = curve;
    }


    while(1);
}
