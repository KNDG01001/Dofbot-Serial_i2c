#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <moveit/trajectory_processing/iterative_time_parameterization.h>
#include <moveit_msgs/msg/orientation_constraint.hpp>
// #include <moveit_visual_tools/moveit_visual_tools.h>

using namespace std;


void multi_trajectory(
        moveit::planning_interface::MoveGroupInterface &dofbot,
        const vector<double> &pose,
        moveit_msgs::msg::RobotTrajectory &trajectory) {
    moveit::planning_interface::MoveGroupInterface::Plan plan;
    const moveit::core::JointModelGroup *joint_model_group;
    // 获取机器人的起始位置
    moveit::core::RobotStatePtr start_state(dofbot.getCurrentState());
    joint_model_group = start_state->getJointModelGroup(dofbot.getName());
    dofbot.setJointValueTarget(pose);
    dofbot.plan(plan);
    start_state->setJointGroupPositions(joint_model_group, pose);
    dofbot.setStartState(*start_state);
    trajectory.joint_trajectory.joint_names = plan.trajectory_.joint_trajectory.joint_names;
    for (size_t j = 0; j < plan.trajectory_.joint_trajectory.points.size(); j++) {
        trajectory.joint_trajectory.points.push_back(plan.trajectory_.joint_trajectory.points[j]);
    }
}

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("moveit_revise_trajectory_demo");
    
    moveit_msgs::msg::RobotTrajectory trajectory;
    moveit::planning_interface::MoveGroupInterface dofbot(node, "dofbot");
    // moveit_visual_tools::MoveItVisualTools tool(node, dofbot.getPlanningFrame(), "moveit_visual_tools_marker", dofbot.getRobotModel());
    // tool.deleteAllMarkers();

    dofbot.allowReplanning(true);
    // 规划的时间(单位：秒)
    dofbot.setPlanningTime(5);
    dofbot.setNumPlanningAttempts(10);
    // 设置允许目标角度误差
    dofbot.setGoalJointTolerance(0.01);
    dofbot.setGoalPositionTolerance(0.01);
    dofbot.setGoalOrientationTolerance(0.01);
    dofbot.setGoalTolerance(0.01);
    // 设置允许的最大速度和加速度
    dofbot.setMaxVelocityScalingFactor(1.0);
    dofbot.setMaxAccelerationScalingFactor(1.0);

    // 控制机械臂先回到初始化位置
    dofbot.setNamedTarget("down");
    dofbot.move();

    vector<vector<double>> poses{
            {1.34,  -1.0,  -0.61, 0.2,   0},
            {0,     0,     0,     0,     0},
            {-1.16, -0.97, -0.81, -0.79, 3.14}
    };
    for (int i = 0; i < poses.size(); ++i) {
        multi_trajectory(dofbot, poses.at(i), trajectory);
    }

    moveit::planning_interface::MoveGroupInterface::Plan joinedPlan;
    robot_trajectory::RobotTrajectory rt(dofbot.getCurrentState()->getRobotModel(), "dofbot");
    rt.setRobotTrajectoryMsg(*dofbot.getCurrentState(), trajectory);
    trajectory_processing::IterativeParabolicTimeParameterization iptp;
    iptp.computeTimeStamps(rt, 1, 1);
    rt.getRobotTrajectoryMsg(trajectory);
    joinedPlan.trajectory_ = trajectory;

    // 显示轨迹
    // tool.publishTrajectoryLine(joinedPlan.trajectory_, dofbot.getCurrentState()->getJointModelGroup("dofbot"));
    // tool.trigger();

    if (dofbot.execute(joinedPlan) != moveit::core::MoveItErrorCode::SUCCESS) {
        RCLCPP_ERROR(node->get_logger(), "Failed to execute plan");
        return false;
    }
    rclcpp::sleep_for(std::chrono::seconds(1));
    RCLCPP_INFO(node->get_logger(), "Finished");
    rclcpp::shutdown();
    return 0;
}

