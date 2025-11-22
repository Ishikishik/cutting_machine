// ==== A4988 PIN ==== 
#define STEP_L 4
#define DIR_L  5

#define STEP_R 2
#define DIR_R  3

#define STEP_DELAY_US 2000
#define DIR_STABLE_US 20

// ==== 安全スイッチ ==== 
#define SAFETY_PIN 16   // GND=ON, HIGH=OFF

// ===== CSVの内容 =====
int steps[][3] = {
  {1, 60,  4},
  {1, 59,  4},
  {1, 59,  5},
  {1, 59,  6},
  {1, 58,  6},
  {1, 58,  7},
  {1, 57,  7},
  {1, 57,  8},
  {1, 57,  9},
  {1, 56,  9},
  {1, 55,  9},
  {1, 55, 10},
  {1, 55, 11},
  {1, 54, 11},
  {1, 54, 12},
};

int total_steps = sizeof(steps) / sizeof(steps[0]);

// ==== 現在位置（絶対ステップ）====
int curL = 25;    // 初期角度 45° = 25step
int curR = 25;


// ==== 1ステップ動かす関数 ====
void stepMotor(int stepPin, int dirPin, bool dir)
{
  // DIR = HIGH → 時計
  // DIR = LOW  → 反時計
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

  // ---- ON（=LOW）になるまで待つ ----
  while (safetyOff())
    delay(10);

  // ---- CSV を順番に実行 ----
  for (int i = 0; i < total_steps; i++) {

    if (safetyOff()) return;

    int curve_id = steps[i][0];
    int targetL  = steps[i][1];
    int targetR  = steps[i][2];

    int diffL = targetL - curL;
    int diffR = targetR - curR;

    int moveMax = max(abs(diffL), abs(diffR));

    for (int s = 0; s < moveMax; s++) {

      if (safetyOff()) return;

      // ---- 左 ----
      if (s < abs(diffL)) {
        bool dirL = (diffL > 0 ? HIGH : LOW);
        stepMotor(STEP_L, DIR_L, dirL);
        curL += (diffL > 0 ? 1 : -1);
      }

      // ---- 右 ----
      if (s < abs(diffR)) {
        bool dirR = (diffR > 0 ? HIGH : LOW);
        stepMotor(STEP_R, DIR_R, dirR);
        curR += (diffR > 0 ? 1 : -1);
      }
    }
  }

  while (1); // 完了
}
