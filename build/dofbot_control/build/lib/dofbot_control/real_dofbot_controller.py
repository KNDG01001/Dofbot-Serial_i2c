import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from moveit_msgs.msg import DisplayTrajectory
import serial
import time
import math

# ==========================================
# [설정] WSL2 내부 포트 이름 (보통 /dev/ttyUSB0)
# PORT and BAUDRATE are now ROS parameters
# ==========================================

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

        # 2. MoveIt의 계획된 경로를 엿듣는 구독자 (Subscriber)
        # RViz에서 'Execute'를 누르면 이 토픽으로 경로가 발행됨
        self.subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.path_callback,
            10)
            
        self.get_logger().info("Ready! Move the robot in RViz and click 'Execute'.")

    def path_callback(self, msg):
        self.get_logger().info("Received Trajectory! Moving Real Robot...")
        
        # MoveIt이 계산한 경로 (여러 개의 점으로 구성됨)
        trajectory = msg.trajectory[0].joint_trajectory
        points = trajectory.points
        joint_names = trajectory.joint_names # ['joint1', 'joint2'...]
        
        # 각 포인트(시간대별 각도)를 순서대로 실행
        for i, point in enumerate(points):
            positions = point.positions # 라디안 값 리스트
            
            # 6개 모터에 명령 전송
            # (속도를 위해 모든 관절 명령을 빠르게 전송)
            for j, angle_rad in enumerate(positions):
                # 1. 라디안 -> 도(Degree) 변환
                angle_deg = int(math.degrees(angle_rad))
                
                # 2. DOFBOT 하드웨어 매핑 (0~180도 제한)
                # MoveIt은 0도가 수직일 수 있지만, DOFBOT은 90도가 수직일 수 있음
                # (URDF 설정에 따라 오프셋 보정 필요할 수 있음. 일단 그대로 전송)
                angle_deg = max(0, min(180, angle_deg))
                
                # 3. 모터 ID 매핑 (joint1 -> ID 1)
                # joint_names 리스트 순서와 실제 ID 순서가 같다고 가정
                servo_id = j + 1 
                
                # 4. 아두이노로 전송 ("ID,Angle,Time\n")
                # Time은 점과 점 사이의 시간 간격인데, 여기선 100ms로 고정해봄
                cmd = f"{servo_id},{angle_deg},100\n"
                self.ser.write(cmd.encode())
                
            # 다음 점까지 대기 (너무 빠르면 모터가 못 따라감)
            # time_from_start를 이용해 정확한 타이밍 계산 가능하지만, 
            # 일단 단순하게 0.1초씩 딜레이
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