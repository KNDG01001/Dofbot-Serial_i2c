#include <iostream>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <tf2/LinearMath/Quaternion.h>
#include <geometry_msgs/msg/pose.hpp>

using namespace std;
// 角度转弧度
const float DE2RA = M_PI / 180.0f;

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("dofbot_motion_plan_cpp");
    
    // Initialize the robotic arm motion planning group
    // 初始化机械臂运动规划组
    moveit::planning_interface::MoveGroupInterface dofbot(node, "dofbot");
    dofbot.allowReplanning(true);
    dofbot.setPlanningTime(5);
    dofbot.setNumPlanningAttempts(10);
    dofbot.setGoalPositionTolerance(0.01);
    dofbot.setGoalOrientationTolerance(0.01);
    dofbot.setMaxVelocityScalingFactor(1.0);
    dofbot.setMaxAccelerationScalingFactor(1.0);
    dofbot.setNamedTarget("down");
    dofbot.move();
    rclcpp::sleep_for(std::chrono::milliseconds(500));
    
    geometry_msgs::msg::Pose pose;
    pose.position.x = 0.0037618483876896;
    pose.position.y = 0.1128923321179022;
    pose.position.z =  0.3998656334826569;
    
    tf2::Quaternion quaternion;
    // RPY的单位是角度值  The unit of RPY is the angle value
    double Roll = -140;
    double Pitch = 0.0;
    double Yaw = 0.0;
    // RPY转四元数  RPY to Quaternion
    quaternion.setRPY(Roll * DE2RA, Pitch * DE2RA, Yaw * DE2RA);
    
    pose.orientation.x = -0.0042810851906468;
    pose.orientation.y = -0.0033330592972940;
    pose.orientation.z = 0.6827314913817025;
    pose.orientation.w = 0.7306492138509612;
    
    string link = dofbot.getEndEffectorLink();
    // 设置目标点  set target point
    dofbot.setPoseTarget(pose, link);
    int index = 0;
    // 多次执行,提高成功率  Execute multiple times to improve the success rate
    while (index <= 10) {
        moveit::planning_interface::MoveGroupInterface::Plan plan;
        // 运动规划  motion planning
        auto code = dofbot.plan(plan);
        if (code == moveit::core::MoveItErrorCode::SUCCESS) {
            RCLCPP_INFO_STREAM(node->get_logger(), "plan success");
            dofbot.execute(plan);
            break;
        } else {
            RCLCPP_INFO_STREAM(node->get_logger(), "plan error");
        }
        index++;
    }
    rclcpp::shutdown();
    return 0;
}

