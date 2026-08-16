#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "错误：没有找到 ROS 2 Humble。"
  exit 1
fi

if [[ ! -f install/setup.bash ]]; then
  echo "错误：没有找到项目编译环境 install/setup.bash。"
  echo "请先运行：colcon build --packages-select aruco_docking"
  exit 1
fi

set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u

if ! ros2 service list 2>/dev/null | grep -qx '/spawn_entity'; then
  echo "错误：Gazebo 的模型入口 /spawn_entity 尚未准备好。"
  echo "请先运行：bash scripts/start_docking_demo.sh"
  exit 1
fi

MODEL_FILE="$WORKSPACE_DIR/install/aruco_docking/share/aruco_docking/models/safety_obstacle/model.sdf"
if [[ ! -f "$MODEL_FILE" ]]; then
  echo "错误：没有找到测试障碍物模型。"
  echo "请先运行：colcon build --packages-select aruco_docking"
  exit 1
fi

echo "正在把红色安全测试柱放到机器人行驶路线右侧……"
ros2 run gazebo_ros spawn_entity.py \
  -entity safety_obstacle \
  -file "$MODEL_FILE" \
  -x -0.75 -y 0.07 -z 0.125

echo "红色安全测试柱已放入场景。"
echo "机器人接近测试柱时，激光雷达应触发 STOP / obstacle。"
