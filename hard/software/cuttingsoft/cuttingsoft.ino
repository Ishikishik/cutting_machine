#include "steps.h"   // ← 配列を最初に読み込む

// ==== A4988 PIN ==== 
#define STEP_L 4
#define DIR_L  5

#define STEP_R 2
#define DIR_R  3

#define STEP_DELAY_US 2000
#define DIR_STABLE_US 20

// ==== 安全スイッチ ==== 
#define SAFETY_PIN 16   // GND=ON, HIGH=OFF

// ==== 現在位置（絶対ステップ）====
int curL = 40000;    // 初期角度 45° = 25step
int curR = 40000;


// ==== 1ステップ動かす関数 ====
void stepMotor(int stepPin, int dirPin, bool dir)
{
  digitalWrite(dirPin, dir);
  delayMicroseconds(DIR_STABLE_US);

  digitalWrite(stepPin, HIGH);
  delayMicroseconds(STEP_DELAY_US);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(STEP_DELAY_US);
}

// ==== 安全スイッチ ====
bool safetyOff() {
  return digitalRead(SAFETY_PIN) == HIGH;
}

void setup() {
  pinMode(STEP_L, OUTPUT);
  pinMode(DIR_L, OUTPUT);

  pinMode(STEP_R, OUTPUT);
  pinMode(DIR_R, OUTPUT);

  pinMode(SAFETY_PIN, INPUT_PULLUP);
}

void loop() {

  // 安全スイッチ
  while (safetyOff()) delay(10);

  // ★ ここで毎回リセット
  curL = 25;
  curR = 25;

  for (int i = 0; i < total_steps; i++) {

    if (safetyOff()) return;

    int targetL = steps[i][1];
    int targetR = steps[i][2];

    int diffL = targetL - curL;
    int diffR = targetR - curR;

    int moveMax = max(abs(diffL), abs(diffR));

    for (int s = 0; s < moveMax; s++) {

      if (safetyOff()) return;

      if (s < abs(diffL)) {
        bool dirL = diffL > 0;
        stepMotor(STEP_L, DIR_L, dirL);
        curL += (dirL ? 1 : -1);
      }

      if (s < abs(diffR)) {
        bool dirR = diffR > 0;
        stepMotor(STEP_R, DIR_R, dirR);
        curR += (dirR ? 1 : -1);
      }
    }
  }

  // 動作終了
  while (1);
}