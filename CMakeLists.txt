cmake_minimum_required(VERSION 3.0.2)
project(teleop_fetch)

find_package(catkin REQUIRED COMPONENTS
  rospy
  geometry_msgs
  sensor_msgs
  std_msgs
  std_srvs
  message_generation
  ainex_interfaces
  ros_robot_controller
)

add_service_files(
  FILES
  ReceiveGrant.srv
  EndSession.srv
)

catkin_python_setup()

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy geometry_msgs sensor_msgs std_msgs std_srvs message_runtime ainex_interfaces ros_robot_controller
)

include_directories(${catkin_INCLUDE_DIRS})

catkin_install_python(PROGRAMS
  scripts/teleop_node.py
  scripts/pose_source_node.py
  scripts/calibration_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY config/ launch/ web/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

if(CATKIN_ENABLE_TESTING)
  catkin_add_nosetests(tests/test_teleop_state_contract.py)
  catkin_add_nosetests(tests/test_operator_buttons.py)
endif()
