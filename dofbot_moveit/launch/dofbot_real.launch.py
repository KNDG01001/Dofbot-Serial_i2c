from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "port",
            default_value="/dev/ttyUSB0",
            description="Serial port for Arduino communication",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "baudrate",
            default_value="115200",
            description="Baudrate for Arduino communication",
        )
    )

    port = LaunchConfiguration("port")
    baudrate = LaunchConfiguration("baudrate")

    # Include MoveIt demo launch (brings up move_group, RViz, robot_state_publisher, etc.)
    demo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("dofbot_moveit_config"),
                "launch",
                "demo.launch.py"
            ])
        )
    )

    # Real Robot Controller Node
    real_controller_node = Node(
        package="dofbot_control",
        executable="real_dofbot_controller",
        name="real_dofbot_controller",
        output="screen",
        parameters=[
            {"port": port},
            {"baudrate": baudrate}
        ]
    )

    return LaunchDescription(
        declared_arguments + 
        [
            demo_launch,
            real_controller_node,
        ]
    )
