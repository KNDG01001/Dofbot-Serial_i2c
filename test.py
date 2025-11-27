import serial
import time
import tkinter as tk
from tkinter import ttk

# ==========================================
# [설정] 본인의 포트 번호로 수정하세요
PORT = 'COM6'
BAUDRATE = 115200
# ==========================================

class DofbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DOFBOT Controller")
        self.root.geometry("400x500")
        
        # 시리얼 연결
        try:
            print(f"Connecting to {PORT}...")
            self.ser = serial.Serial(PORT, BAUDRATE, timeout=1)
            time.sleep(2) # 아두이노 리셋 대기
            print("Connected!")
        except Exception as e:
            print(f"Error: {e}")
            root.destroy()
            return

        # 제목
        tk.Label(root, text="DOFBOT Joint Control", font=("Arial", 16, "bold")).pack(pady=10)

        # 슬라이더 생성 (1~6번 모터)
        self.sliders = []
        joint_names = ["1. Base (바닥)", "2. Shoulder (어깨)", "3. Elbow (팔꿈치)", 
                       "4. Wrist 1 (손목1)", "5. Wrist 2 (손목2)", "6. Gripper (집게)"]
        
        # 초기 각도 설정 (안전한 자세)
        initial_angles = [90, 90, 90, 90, 90, 90]

        for i in range(6):
            frame = tk.Frame(root)
            frame.pack(pady=5, fill='x', padx=20)
            
            # 라벨
            tk.Label(frame, text=joint_names[i], width=15, anchor='w').pack(side='left')
            
            # 슬라이더 (Scale)
            # from_=0, to=180: 각도 범위
            # command: 값이 바뀔 때 실행할 함수 (마우스 놓을 때 전송하려면 bind 사용해야 함)
            slider = tk.Scale(frame, from_=0, to=180, orient='horizontal', length=200)
            slider.set(initial_angles[i]) # 초기값
            slider.pack(side='right')
            
            # 슬라이더를 놓았을 때(ButtonRelease) 명령 전송하도록 바인딩
            # (실시간으로 보내면 아두이노가 체할 수 있음)
            slider.bind("<ButtonRelease-1>", lambda event, id=i+1: self.send_command(id))
            
            self.sliders.append(slider)

        # 리셋 버튼
        btn_reset = tk.Button(root, text="RESET (초기화)", command=self.reset_robot, bg="orange", height=2)
        btn_reset.pack(pady=20, fill='x', padx=50)

        # 종료 시 시리얼 닫기
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send_command(self, servo_id):
        # 슬라이더의 현재 값 읽기 (인덱스는 ID-1)
        angle = self.sliders[servo_id-1].get()
        time_ms = 500 # 이동 시간 0.5초 고정
        
        # 명령 문자열 생성: "ID,Angle,Time\n"
        cmd = f"{servo_id},{angle},{time_ms}\n"
        self.ser.write(cmd.encode())
        print(f"Sent: {cmd.strip()}")

    def reset_robot(self):
        print("Resetting Robot...")
        # 모든 슬라이더와 로봇을 90도로
        for i, slider in enumerate(self.sliders):
            slider.set(90)
            # 약간의 시차를 두고 전송
            cmd = f"{i+1},90,1000\n"
            self.ser.write(cmd.encode())
            time.sleep(0.05)

    def on_closing(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DofbotGUI(root)
    root.mainloop()