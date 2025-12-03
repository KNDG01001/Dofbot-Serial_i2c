#include <Wire.h>

#define DOFBOT_ADDR 0x15

// 현재 서보 위치 저장 (추정값)
int current_positions[6] = {90, 90, 90, 90, 90, 90};
unsigned long last_feedback_time = 0;
const unsigned long FEEDBACK_INTERVAL = 100; // 100ms마다 피드백 전송

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
    char first = Serial.peek();
    
    // 명령 요청인지 확인 ('F' = Feedback 요청)
    if (first == 'F') {
      Serial.read(); // 'F' 제거
      sendFeedback(); // 즉시 피드백 전송
    } else {
      // 일반 위치 명령
      int id = Serial.parseInt();
      int angle = Serial.parseInt();
      int time_ms = Serial.parseInt();

      // 줄바꿈 문자(\n)를 만나면 명령 실행
      if (Serial.read() == '\n') {
        moveServo(id, angle, time_ms);
        
        // 위치 업데이트 (추정)
        if (id >= 1 && id <= 6) {
          current_positions[id - 1] = angle;
        } else if (id == 0) {
          // 전체 서보에 같은 각도
          for (int i = 0; i < 6; i++) {
            current_positions[i] = angle;
          }
        }
        
        Serial.print("CMD OK: ID="); Serial.print(id);
        Serial.print(" Ang="); Serial.println(angle);
      }
    }
  }
  
  // 주기적으로 피드백 전송 (100ms마다)
  unsigned long now = millis();
  if (now - last_feedback_time >= FEEDBACK_INTERVAL) {
    sendFeedback();
    last_feedback_time = now;
  }
}

// 피드백 전송 함수
void sendFeedback() {
  Serial.print("FB:");
  for (int i = 0; i < 6; i++) {
    Serial.print(current_positions[i]);
    if (i < 5) Serial.print(",");
  }
  Serial.println();
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
