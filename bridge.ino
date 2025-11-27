#include <Wire.h>

#define DOFBOT_ADDR 0x15

void setup() {
  Wire.begin();         // I2C 시작 (SDA:A4, SCL:A5)
  Serial.begin(115200); // PC 통신 속도 (빠르게)

  // 1. 초기화: 액션 그룹 정지 & 토크 ON (필수!)
  initDofbot();
  
  // 2. 준비 완료 신호 (LED 초록색)
  setRGB(0, 255, 0); 
  Serial.println("DOFBOT BRIDGE READY");
}

void loop() {
  // PC로부터 데이터가 들어오면 처리
  // 프로토콜 형식: "ID, 각도, 시간" (예: "1,90,500")
  if (Serial.available() > 0) {
    int id = Serial.parseInt();
    int angle = Serial.parseInt();
    int time_ms = Serial.parseInt();

    // 줄바꿈 문자(\n)를 만나면 명령 실행
    if (Serial.read() == '\n') {
      moveServo(id, angle, time_ms);
      Serial.print("CMD OK: ID="); Serial.print(id);
      Serial.print(" Ang="); Serial.println(angle);
    }
  }
}

// 초기화 함수 (잠금 해제)
void initDofbot() {
  // Action Stop
  Wire.beginTransmission(DOFBOT_ADDR);
  Wire.write(0x23); Wire.write(0x01);
  Wire.endTransmission();
  delay(50);
  
  // Torque ON
  Wire.beginTransmission(DOFBOT_ADDR);
  Wire.write(0x1A); Wire.write(0x01);
  Wire.endTransmission();
  delay(50);
}

// 서보 이동 함수 (I2C 전송)
void moveServo(int id, int angle, int time_ms) {
  // 각도 제한
  if (angle < 0) angle = 0;
  if (angle > 180) angle = 180;

  // 펄스 변환 (0~180 -> 900~3100)
  long pulse = map(angle, 0, 180, 900, 3100);
  
  uint8_t p_h = (pulse >> 8) & 0xFF;
  uint8_t p_l = pulse & 0xFF;
  uint8_t t_h = (time_ms >> 8) & 0xFF;
  uint8_t t_l = time_ms & 0xFF;

  Wire.beginTransmission(DOFBOT_ADDR);
  if (id == 0) {
    Wire.write(0x19); // 전체 방송
    Wire.write(0x00); // ID 0
  } else {
    Wire.write(0x10 + id); // 개별 제어 (0x11 ~ 0x16)
  }
  Wire.write(p_h);
  Wire.write(p_l);
  Wire.write(t_h);
  Wire.write(t_l);
  Wire.endTransmission();
}

// RGB 제어 함수
void setRGB(uint8_t r, uint8_t g, uint8_t b) {
  Wire.beginTransmission(DOFBOT_ADDR);
  Wire.write(0x02); 
  Wire.write(r); Wire.write(g); Wire.write(b);
  Wire.endTransmission();
}
//야붐의 제어 코드는 byte code 형태로 제어, 현 브릿지 코드의 기댓값은 1, 90, 100과 같은 문자열 형태
