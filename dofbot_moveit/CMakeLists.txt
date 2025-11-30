cmake_minimum_required(VERSION 3.8)
project(dofbot_moveit)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
# find_package(moveit_visual_tools REQUIRED)
# KDL
find_package(orocos_kdl REQUIRED)
find_package(kdl_parser REQUIRED)
find_package(urdf REQUIRED)

include_directories(
  include
  ${orocos_kdl_INCLUDE_DIRS}
)

# Library for kinematics
add_library(dofbot_kinematics
  src/dofbot_kinematics.cpp
)
target_link_libraries(dofbot_kinematics
  ${orocos_kdl_LIBRARIES}
)
ament_target_dependencies(dofbot_kinematics
  kdl_parser
  urdf
)
# In ROS 2, we usually don't link against catkin_LIBRARIES, but we might need to link against ament packages if we used ament_target_dependencies.
# However, for KDL it's often a system lib.

# Executables
add_executable(01_random_move src/01_random_move.cpp)
ament_target_dependencies(01_random_move rclcpp moveit_ros_planning_interface moveit_msgs geometry_msgs)

add_executable(02_motion_plan src/02_motion_plan.cpp)
ament_target_dependencies(02_motion_plan rclcpp moveit_ros_planning_interface moveit_msgs geometry_msgs)

add_executable(03_attached_object src/03_attached_object.cpp)
ament_target_dependencies(03_attached_object rclcpp moveit_ros_planning_interface moveit_msgs geometry_msgs)

add_executable(04_cartesian src/04_cartesian.cpp)
ament_target_dependencies(04_cartesian rclcpp moveit_ros_planning_interface moveit_msgs geometry_msgs)

add_executable(06_multi_track_motion src/06_multi_track_motion.cpp)
ament_target_dependencies(06_multi_track_motion rclcpp moveit_ros_planning_interface moveit_msgs geometry_msgs)

# Kinematics executables using the library
add_executable(dofbot_kinematics_fk_node src/dofbot_kinematics_fk.cpp)
target_link_libraries(dofbot_kinematics_fk_node dofbot_kinematics)
ament_target_dependencies(dofbot_kinematics_fk_node rclcpp ament_index_cpp)

add_executable(dofbot_kinematics_ik_node src/dofbot_kinematics_ik.cpp)
target_link_libraries(dofbot_kinematics_ik_node dofbot_kinematics)
ament_target_dependencies(dofbot_kinematics_ik_node rclcpp ament_index_cpp)


install(TARGETS
  dofbot_kinematics
  dofbot_kinematics_fk_node
  dofbot_kinematics_ik_node
  01_random_move
  02_motion_plan
  03_attached_object
  04_cartesian
  06_multi_track_motion
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY meshes/
  DESTINATION share/${PROJECT_NAME}/meshes
)

install(DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

install(DIRECTORY launch urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
