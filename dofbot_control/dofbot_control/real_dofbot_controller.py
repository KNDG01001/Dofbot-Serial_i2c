import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from moveit_msgs.msg import DisplayTrajectory
import serial
import time
import math
import yaml
import os
import threading

class RealDofbotController(Node):
    def __init__(self):
        super().__init__('real_dofbot_controller')
        
        # Declare parameters
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        
        # Get parameters
        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        
        # 1. 아두이노 연결
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2) # 리셋 대기
            self.get_logger().info(f"Connected to Arduino at {port} with baudrate {baudrate}")
        except Exception as e:
            self.get_logger().error(f"Failed to connect: {e}")
            exit()

        # 2. 캘리브레이션 오프셋 로드
        self.offsets = {}
        self.invert = {}
        self.load_calibration_offsets()

        # 3. 현재 joint 상태 저장
        self.current_joint_positions = [0.0] * 6  # arm_joint1~5 + grip_joint
        
        # 4. Joint State Publisher
        self.joint_state_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.joint_names = ['arm_joint1', 'arm_joint2', 'arm_joint3', 'arm_joint4', 'arm_joint5', 'grip_joint']
        
        # 5. MoveIt 경로 구독
        self.subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.path_callback,
            10)
        
        # 6. 피드백 읽기 쓰레드 시작
        self.feedback_thread = threading.Thread(target=self.feedback_loop, daemon=True)
        self.feedback_thread.start()
        
        self.get_logger().info("Ready! Move the robot in RViz and click 'Plan'.")

    def load_calibration_offsets(self):
        """Load servo calibration offsets from YAML file"""
        offset_file = os.path.expanduser('~/Manipulator/servo_offsets.yaml')
        try:
            with open(offset_file, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    self.offsets = data.get('offsets', {})
                    self.invert = data.get('invert', {})
                    self.get_logger().info(f"Loaded calibration offsets from {offset_file}")
                    self.get_logger().info(f"Offsets: {self.offsets}")
                    self.get_logger().info(f"Invert flags: {self.invert}")
        except FileNotFoundError:
            self.get_logger().warn(f"Calibration file {offset_file} not found. Using zero offsets.")
            for i in range(1, 7):
                self.offsets[f'joint{i}'] = 0
                self.invert[f'joint{i}'] = False
        except Exception as e:
            self.get_logger().error(f"Error loading calibration: {e}")
            for i in range(1, 7):
                self.offsets[f'joint{i}'] = 0
                self.invert[f'joint{i}'] = False

    def feedback_loop(self):
        """Read feedback from Arduino and publish joint states"""
        while rclpy.ok():
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    # 피드백 메시지 파싱: "FB:90,90,90,90,90,90"
                    if line.startswith("FB:"):
                        positions_str = line[3:].split(',')
                        if len(positions_str) >= 6:  # 6개 관절 모두 필요
                            # 서보 각도 -> MoveIt 각도로 역변환
                            for i in range(6):  # arm_joint1~5 + grip_joint
                                try:
                                    servo_angle = int(positions_str[i])
                                    
                                    # 역변환: 서보 각도 -> MoveIt 각도
                                    joint_name = f'joint{i+1}'
                                    offset = self.offsets.get(joint_name, 0)
                                    invert = self.invert.get(joint_name, False)
                                    
                                    # 서보 중립(90도) -> MoveIt 제로(0도) 변환 및 오프셋 제거
                                    moveit_angle = servo_angle - 90 - offset
                                    
                                    if invert:
                                        moveit_angle = -moveit_angle
                                    
                                    # 도 -> 라디안
                                    self.current_joint_positions[i] = math.radians(moveit_angle)
                                    
                                except ValueError:
                                    pass
                            
                            # Joint State 발행
                            self.publish_joint_states()
                            
            except Exception as e:
                self.get_logger().error(f"Feedback error: {e}")
            
            time.sleep(0.05)  # 20Hz

    def publish_joint_states(self):
        """Publish current joint states to /joint_states topic"""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = self.current_joint_positions
        msg.velocity = [0.0] * 6
        msg.effort = [0.0] * 6
        
        self.joint_state_pub.publish(msg)

    def path_callback(self, msg):
        self.get_logger().info("Received Trajectory! Moving Real Robot...")
        
        # MoveIt이 계산한 경로 (여러 개의 점으로 구성됨)
        trajectory = msg.trajectory[0].joint_trajectory
        points = trajectory.points
        joint_names = trajectory.joint_names # ['arm_joint1', 'arm_joint2'...]
        
        # Joint 이름 -> Servo ID 매핑
        joint_to_servo = {}
        for idx, name in enumerate(joint_names):
            if 'joint' in name:
                joint_num = int(name.split('joint')[-1])
                joint_to_servo[idx] = joint_num
        
        # 각 포인트(시간대별 각도)를 순서대로 실행
        for i, point in enumerate(points):
            positions = point.positions # 라디안 값 리스트
            
            # 6개 모터에 명령 전송
            for j, angle_rad in enumerate(positions):
                if j not in joint_to_servo:
                    continue
                
                servo_id = joint_to_servo[j]
                if servo_id > 6:
                    continue
                
                # 1. 라디안 -> 도(Degree) 변환
                angle_deg = math.degrees(angle_rad)
                
                # 2. 캘리브레이션 오프셋 적용
                joint_name = f'joint{servo_id}'
                offset = self.offsets.get(joint_name, 0)
                invert = self.invert.get(joint_name, False)
                
                # 반전 적용 (필요한 경우)
                if invert:
                    angle_deg = -angle_deg
                
                # MoveIt 제로(0도) = 서보 중립(90도) 변환 + 오프셋 추가
                angle_deg = angle_deg + 90 + offset
                
                # 3. DOFBOT 하드웨어 매핑 (0~180도 제한)
                angle_deg = int(max(0, min(180, angle_deg)))
                
                # 디버그: 실제 전송되는 각도 출력
                self.get_logger().info(f"Joint {servo_id}: MoveIt={math.degrees(angle_rad):.1f}° → Servo={angle_deg}°")
                
                # 4. 아두이노로 전송 ("ID,Angle,Time\n")
                cmd = f"{servo_id},{angle_deg},100\n"
                self.get_logger().info(f"Sending: {cmd.strip()}")  # 전송 명령 로깅
                self.ser.write(cmd.encode())
                
            # 다음 점까지 대기
            time.sleep(0.1) 
            
        self.get_logger().info("Movement Complete.")

def main(args=None):
    rclpy.init(args=args)
    node = RealDofbotController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()