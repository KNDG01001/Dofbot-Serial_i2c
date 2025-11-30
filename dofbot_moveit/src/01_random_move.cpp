#include <iostream>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>

using namespace std;

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("dofbot_random_move_cpp");
    
    // Initialize the robotic arm motion planning group
    // 初始化机械臂运动规划组
    // MoveGroupInterface requires a node in ROS 2
    moveit::planning_interface::MoveGroupInterface dofbot(node, "dofbot");

    while (rclcpp::ok()){
        // 设置随机目标点 Set random target points
        dofbot.setRandomTarget();
        // 开始移动 start moving
        dofbot.move();
        // sleep(0.5); // Use rclcpp::sleep_for or std::this_thread::sleep_for
        rclcpp::sleep_for(std::chrono::milliseconds(500));
    }
    // 阻塞进程 blocking process
    rclcpp::shutdown();
    return 0;
}
