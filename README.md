# DOFBOT-Serial_i2c: PC Control via Arduino Bridge

**Jetson Nano**나 **Raspberry Pi** 없이, **Windows PC**와 **Arduino**를 사용하여 Yahboom DOFBOT 로봇팔을 제어하는 프로젝트입니다.

DOFBOT 확장 보드(Expansion Board)는 기본적으로 I2C 통신을 사용하므로 일반 PC와 직접 연결이 불가능합니다. 이 프로젝트는 **Arduino를 USB-to-I2C 브릿지(Bridge)**로 사용하여, PC의 Python 환경에서 로봇팔을 직접 제어할 수 있게 해줍니다.

---

## 🚀 주요 기능 (Key Features)

- **PC 직접 제어**: 고가의 임베디드 보드 없이 노트북/데스크탑에서 로봇팔 제어 가능
- **브릿지 통신**: Arduino를 중계기로 사용하여 시리얼(USB) 통신을 I2C로 변환
- **다양한 제어 모드**:
  - 🖥️ **GUI 컨트롤러**: 슬라이더를 이용한 직관적인 관절 제어
  - ⌨️ **CLI 모드**: 터미널 명령어를 통한 정밀 제어
  - 🎯 **AI 트래킹**: Pi0 기반의 객체 추적 및 Visual Servoing (예정)
- **캘리브레이션 도구**: 물리적 조립 오차 보정을 위한 미세 조정 툴 제공

---

## 🛠 하드웨어 준비물 (Hardware Requirements)

- Yahboom DOFBOT (Expansion Board + Robotic Arm)
- Arduino Uno (또는 Nano, Mega)
- PC (Windows 10/11 권장)
- 12V 전원 어댑터 (DOFBOT 전원 공급용 **필수**)
- 점퍼 와이어 (Male-to-Female) 3가닥
- USB 케이블 (Arduino - PC 연결용)

---

## ⚡ 배선 연결 (Wiring Diagram)

**가장 중요한 단계입니다.** Arduino와 DOFBOT 확장 보드의 40핀 헤더를 아래와 같이 연결하세요.

(DOFBOT 40핀 헤더의 핀 번호는 보드 구석의 작은 숫자를 참고하세요.)

| Arduino Pin | DOFBOT Pin (40-Pin Header) | 기능 (Function)     | 비고                         |
|-------------|----------------------------|---------------------|------------------------------|
| A4          | Pin 3                      | SDA (Data)          | I2C 통신 데이터              |
| A5          | Pin 5                      | SCL (Clock)         | I2C 통신 클럭                |
| GND         | Pin 6                      | GND (Ground)        | 필수 연결 (신호 기준점)      |

> ⚠️ **주의**: DOFBOT의 5V 핀(Pin 2, 4)과 아두이노의 5V를 **연결하지 마세요**. 전원 충돌로 보드가 손상될 수 있습니다.

---

## 📦 설치 및 설정 (Installation)

### 1. Arduino (Firmware)

1. `Dofbot_Bridge.ino` 파일을 엽니다. (아두이노 코드)
2. Arduino IDE에서 보드와 포트를 선택합니다.
3. 코드를 업로드합니다.

> 참고: 업로드 시 USB 케이블을 뺐다 꽂아야 할 수 있습니다.

### 2. Python (Controller)

Python 3.8 이상 환경에서 필요한 라이브러리를 설치합니다.

### 3. 포트 설정

모든 Python 스크립트(`*.py`) 상단에 있는 `PORT` 변수를 본인의 아두이노 포트 번호로 수정하세요.

```python
# 예시
PORT = 'COM6'  # Windows 장치 관리자에서 확인한 포트 번호, Windows 외 환경에서는 lsusb를 활용, 포트 확인
BAUDRATE = 115200
```

---

## 🎮 사용 방법 (Usage)

### 1단계: 하드웨어 부팅

1. **배선**(SDA, SCL, GND)이 올바른지 확인합니다.
2. **12V 어댑터**를 DOFBOT에 연결하고 전원 스위치를 켭니다. (보드 LED 점등 확인)
3. **Arduino**를 PC에 USB로 연결합니다.

### 2단계: 프로그램 실행

#### 1. GUI 컨트롤러 (추천)
마우스로 슬라이더를 움직여 로봇을 제어합니다.

```bash
python dofbot_gui.py
```

#### 2. CLI 모드 (명령어)
터미널에서 직접 각도를 입력합니다. (예: `1 90`)

```bash
python dofbot_cli.py
```

#### 3. 캘리브레이션 도구
조립 오차를 맞추기 위한 영점 조절 도구입니다.

```bash
python dofbot_calib.py
```

---

## 🔧 트러블슈팅 (Troubleshooting)

### Q. 코드를 실행했는데 모터가 움직이지 않아요.

✅ **노란색 점퍼 캡 확인**: DOFBOT 보드 위의 Servo Power Jumper가 꽂혀 있어야 모터에 전기가 공급됩니다.

✅ **전원 확인**: 12V 어댑터가 연결되어 있고 스위치가 켜져 있는지 확인하세요. (Arduino 전원만으로는 모터가 돌지 않습니다.)

✅ **배선 확인**: SDA(Pin3)와 SCL(Pin5)이 바뀌지 않았는지, GND(Pin6)가 연결되었는지 확인하세요.

### Q. Access Denied 또는 포트 에러가 떠요.

Arduino IDE의 시리얼 모니터가 켜져 있다면 끄고 다시 실행하세요. 포트를 독점하기 때문입니다.

### Q. 모터가 덜덜 떨리거나 엉뚱한 각도로 가요.

`dofbot_calib.py`를 실행하여 90도 정렬을 맞추고, 필요하다면 서보 혼(Horn) 나사를 풀어서 물리적으로 다시 조립하세요.

---

## 📜 라이선스 (License)

- This project is open source.
- Original Hardware by **Yahboom**.
- Bridge Code & Implementation by **KNDG01001**.

---

## 🤖 ROS 2 Humble Port (MoveIt 2)

이 리포지토리는 DOFBOT 매니퓰레이터의 ROS 2 Humble 포팅 버전을 포함하고 있습니다. 로봇 모델(URDF)과 MoveIt 2 모션 플래닝 구성을 제공합니다.

### 패키지 구성

*   **`dofbot_moveit`**: 로봇 설명 파일(URDF, Meshes) 및 기본 실행 파일 포함
*   **`dofbot_moveit_config`**: MoveIt Setup Assistant로 생성된 MoveIt 2 설정 패키지

### 설치 방법 (ROS 2)

1.  **워크스페이스 생성 및 클론:**
    ```bash
    mkdir -p ~/dofbot_ws/src
    cd ~/dofbot_ws/src
    git clone https://github.com/KNDG01001/Dofbot-Serial_i2c.git .
    ```

2.  **의존성 설치:**
    ```bash
    cd ~/dofbot_ws
    rosdep update
    rosdep install --from-paths src --ignore-src -r -y
    ```

3.  **빌드:**
    ```bash
    colcon build
    source install/setup.bash
    ```

### 사용 방법 (ROS 2)

#### 1. 로봇 모델 시각화
MoveIt 없이 RViz에서 로봇 모델만 확인하려면:

```bash
ros2 launch dofbot_moveit dofbot_moveit.launch.py
```

#### 2. MoveIt 2 데모 실행
MoveIt 2를 실행하여 RViz에서 모션 플래닝을 테스트하려면:

```bash
ros2 launch dofbot_moveit_config demo.launch.py
```

### 업데이트 내역
*   **URDF 수정**: 메쉬 파일 경로 및 좌표계 수정으로 "폭발하는" 로봇 모델 문제 해결
*   **ROS 2 마이그레이션**: CMakeLists.txt 및 package.xml을 ROS 2 Humble 표준으로 포팅
*   **MoveIt 설정**: ROS 2 호환 MoveIt 구성 패키지 생성
