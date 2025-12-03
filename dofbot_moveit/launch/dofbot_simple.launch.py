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

    model = LaunchConfiguration("model")

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

    # Joint State Publisher (기본 상태 발행)
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
    )
    
    # Robot State Publisher
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    # RViz 설정
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
    
    # Real Robot Controller (Arm_Lib 사용)
    real_controller_node = Node(
        package="dofbot_control",
        executable="real_dofbot_controller",
        name="real_dofbot_controller",
        output="screen",
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
