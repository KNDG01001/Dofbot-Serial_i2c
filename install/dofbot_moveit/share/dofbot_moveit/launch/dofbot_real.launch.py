from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "model",
            default_value="dofbot.urdf",
            description="URDF/Xacro description file with the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="false",
            description="Start Rviz2 and Joint State Publisher GUI automatically with this launch file.",
        )
    )
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

    model = LaunchConfiguration("model")
    gui = LaunchConfiguration("gui")
    port = LaunchConfiguration("port")
    baudrate = LaunchConfiguration("baudrate")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("dofbot_moveit"), "urdf", model]
            ),
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    # Joint State Publisher (GUI or non-GUI based on argument? 
    # Actually, for real robot, we might want to use the real joint states if we had feedback.
    # But the current controller is open-loop (sends commands, doesn't read back).
    # So we still need joint_state_publisher to publish 'fake' states or 
    # we rely on MoveIt's fake controller if we don't have real feedback.
    # However, the user's request is just to bridge the commands.
    # Let's keep the structure similar to dofbot_moveit.launch.py but add the real controller.
    # Note: If we run real controller, we might not want joint_state_publisher_gui interfering 
    # if we want to see the plan execution. 
    # But usually MoveIt execution updates the joint states in the move_group.
    # Let's keep it simple: Run MoveIt (demo) + Real Controller (listener).
    
    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        condition=LaunchConfiguration("gui"), # Only if gui is true? Or always?
        # Original launch had it always. Let's keep it.
    )
    
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("dofbot_moveit"), "rviz", "dofbot.rviz"]
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
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
            joint_state_publisher_node,
            robot_state_publisher_node,
            rviz_node,
            real_controller_node,
        ]
    )
