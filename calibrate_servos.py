#!/usr/bin/env python3
"""
DOFBOT Servo Calibration Tool
==============================
Linux용 서보 캘리브레이션 도구

사용법:
1. 각 관절의 슬라이더를 움직여서 실제 로봇을 원하는 위치로 이동
2. MoveIt에서 보이는 각도와 실제 필요한 서보 각도를 비교
3. "Save Offsets" 버튼을 눌러 오프셋 저장
4. 저장된 오프셋은 servo_offsets.yaml에 기록됨
"""

import serial
import time
import tkinter as tk
from tkinter import ttk, messagebox
import yaml

# ==========================================
# 설정
DEFAULT_PORT = '/dev/ttyUSB0'
DEFAULT_BAUDRATE = 115200
OFFSET_FILE = 'servo_offsets.yaml'
# ==========================================

class DofbotCalibrationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("DOFBOT Servo Calibration Tool")
        self.root.geometry("600x700")
        
        # 시리얼 포트 설정 프레임
        self.setup_connection_frame()
        
        # 연결 상태
        self.ser = None
        self.connected = False
        
        # 오프셋 저장용
        self.offsets = {f'joint{i}': 0 for i in range(1, 7)}
        self.invert = {f'joint{i}': False for i in range(1, 7)}
        
        # 기존 오프셋 로드 시도
        self.load_offsets()
        
        # 제목
        tk.Label(root, text="DOFBOT Servo Calibration", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        # 설명
        info_text = ("각 서보를 개별적으로 테스트하고 오프셋을 확인하세요.\n"
                    "MoveIt의 제로 포지션과 실제 서보 제로 포지션의 차이를 기록합니다.")
        tk.Label(root, text=info_text, fg="blue").pack(pady=5)
        
        # 슬라이더 프레임
        self.slider_frame = tk.Frame(root)
        self.slider_frame.pack(pady=10, fill='both', expand=True)
        
        # 슬라이더 생성
        self.sliders = []
        self.value_labels = []
        self.offset_entries = []
        self.invert_vars = []
        
        joint_names = [
            "Joint 1: Base (회전)",
            "Joint 2: Shoulder (어깨)", 
            "Joint 3: Elbow (팔꿈치)",
            "Joint 4: Wrist 1 (손목1)", 
            "Joint 5: Wrist 2 (손목2)",
            "Joint 6: Gripper (그리퍼)"
        ]
        
        # 헤더
        header_frame = tk.Frame(self.slider_frame)
        header_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(header_frame, text="Joint", width=20, anchor='w', font=('Arial', 10, 'bold')).grid(row=0, column=0)
        tk.Label(header_frame, text="Servo Angle", width=15, font=('Arial', 10, 'bold')).grid(row=0, column=1)
        tk.Label(header_frame, text="Offset", width=10, font=('Arial', 10, 'bold')).grid(row=0, column=2)
        tk.Label(header_frame, text="Invert", width=8, font=('Arial', 10, 'bold')).grid(row=0, column=3)
        
        for i in range(6):
            frame = tk.Frame(self.slider_frame)
            frame.pack(pady=8, fill='x', padx=10)
            
            # 관절 이름
            tk.Label(frame, text=joint_names[i], width=20, anchor='w').grid(row=0, column=0, sticky='w')
            
            # 슬라이더
            slider = tk.Scale(frame, from_=0, to=180, orient='horizontal', 
                            length=200, command=lambda val, id=i+1: self.slider_changed(id, val))
            slider.set(90)  # 초기값
            slider.grid(row=0, column=1, padx=5)
            self.sliders.append(slider)
            
            # 현재 값 표시
            val_label = tk.Label(frame, text="90°", width=5)
            val_label.grid(row=0, column=2, padx=5)
            self.value_labels.append(val_label)
            
            # 오프셋 입력
            offset_entry = tk.Entry(frame, width=8)
            offset_entry.insert(0, str(self.offsets[f'joint{i+1}']))
            offset_entry.grid(row=0, column=3, padx=5)
            self.offset_entries.append(offset_entry)
            
            # 반전 체크박스
            invert_var = tk.BooleanVar(value=self.invert[f'joint{i+1}'])
            invert_check = tk.Checkbutton(frame, variable=invert_var)
            invert_check.grid(row=0, column=4, padx=5)
            self.invert_vars.append(invert_var)
        
        # 버튼 프레임
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Reset to 90°", command=self.reset_all, 
                 bg="orange", width=15, height=2).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Save Offsets", command=self.save_offsets, 
                 bg="green", fg="white", width=15, height=2).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Test Trajectory", command=self.test_trajectory, 
                 bg="blue", fg="white", width=15, height=2).grid(row=0, column=2, padx=5)
        
        # 상태 표시
        self.status_label = tk.Label(root, text="Not Connected", fg="red", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)
        
        # 종료 시 연결 닫기
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_connection_frame(self):
        """연결 설정 UI"""
        frame = tk.LabelFrame(self.root, text="Serial Connection", padx=10, pady=10)
        frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(frame, text="Port:").grid(row=0, column=0, sticky='e')
        self.port_entry = tk.Entry(frame, width=20)
        self.port_entry.insert(0, DEFAULT_PORT)
        self.port_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(frame, text="Baudrate:").grid(row=0, column=2, sticky='e', padx=(20, 0))
        self.baudrate_entry = tk.Entry(frame, width=10)
        self.baudrate_entry.insert(0, str(DEFAULT_BAUDRATE))
        self.baudrate_entry.grid(row=0, column=3, padx=5)
        
        self.connect_btn = tk.Button(frame, text="Connect", command=self.toggle_connection, 
                                     bg="green", fg="white", width=12)
        self.connect_btn.grid(row=0, column=4, padx=10)
    
    def toggle_connection(self):
        """시리얼 연결 토글"""
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        """시리얼 포트 연결"""
        port = self.port_entry.get()
        baudrate = int(self.baudrate_entry.get())
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # 아두이노 리셋 대기
            self.connected = True
            self.status_label.config(text=f"Connected to {port}", fg="green")
            self.connect_btn.config(text="Disconnect", bg="red")
            messagebox.showinfo("Success", f"Connected to {port}")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect:\n{e}")
            self.status_label.config(text="Connection Failed", fg="red")
    
    def disconnect(self):
        """시리얼 포트 연결 해제"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False
        self.status_label.config(text="Disconnected", fg="red")
        self.connect_btn.config(text="Connect", bg="green")
    
    def slider_changed(self, servo_id, value):
        """슬라이더 값 변경 시 실시간 전송"""
        angle = int(float(value))
        self.value_labels[servo_id-1].config(text=f"{angle}°")
        self.send_servo_command(servo_id, angle)
    
    def send_servo_command(self, servo_id, angle, time_ms=500):
        """서보 명령 전송"""
        if not self.connected or not self.ser:
            return
        
        cmd = f"{servo_id},{angle},{time_ms}\n"
        try:
            self.ser.write(cmd.encode())
            print(f"Sent: {cmd.strip()}")
        except Exception as e:
            print(f"Send error: {e}")
            self.status_label.config(text="Send Error", fg="red")
    
    def reset_all(self):
        """모든 서보를 90도로 리셋"""
        print("Resetting all servos to 90°...")
        for i, slider in enumerate(self.sliders):
            slider.set(90)
            time.sleep(0.05)
    
    def load_offsets(self):
        """저장된 오프셋 로드"""
        try:
            with open(OFFSET_FILE, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    self.offsets = data.get('offsets', self.offsets)
                    self.invert = data.get('invert', self.invert)
                    print(f"Loaded offsets from {OFFSET_FILE}")
        except FileNotFoundError:
            print(f"{OFFSET_FILE} not found, using default offsets")
        except Exception as e:
            print(f"Error loading offsets: {e}")
    
    def save_offsets(self):
        """오프셋을 YAML 파일로 저장"""
        # UI에서 오프셋 읽기
        for i in range(6):
            try:
                offset = int(self.offset_entries[i].get())
                self.offsets[f'joint{i+1}'] = offset
            except ValueError:
                self.offsets[f'joint{i+1}'] = 0
            
            self.invert[f'joint{i+1}'] = self.invert_vars[i].get()
        
        # YAML로 저장
        data = {
            'offsets': self.offsets,
            'invert': self.invert,
            'description': 'Servo offset calibration for DOFBOT. offset = servo_angle - moveit_angle'
        }
        
        try:
            with open(OFFSET_FILE, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            messagebox.showinfo("Success", f"Offsets saved to {OFFSET_FILE}")
            print(f"Saved offsets: {self.offsets}")
            print(f"Saved invert flags: {self.invert}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save offsets:\n{e}")
    
    def test_trajectory(self):
        """간단한 테스트 궤적 실행"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to serial port first")
            return
        
        print("Running test trajectory...")
        test_positions = [
            [90, 90, 90, 90, 90, 90],   # Home
            [45, 90, 90, 90, 90, 90],   # Base left
            [135, 90, 90, 90, 90, 90],  # Base right
            [90, 120, 60, 90, 90, 90],  # Shoulder forward
            [90, 90, 90, 90, 90, 90],   # Home
        ]
        
        for positions in test_positions:
            for i, angle in enumerate(positions):
                self.sliders[i].set(angle)
            time.sleep(1.5)
        
        messagebox.showinfo("Test Complete", "Test trajectory finished")
    
    def on_closing(self):
        """창 닫을 때"""
        self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DofbotCalibrationTool(root)
    root.mainloop()
