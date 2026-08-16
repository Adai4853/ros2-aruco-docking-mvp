#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "错误：没有找到 ROS 2 Humble。"
  exit 1
fi

echo "[1/5] 正在编译 aruco_docking……"
set +u
source /opt/ros/humble/setup.bash
set -u
colcon build --packages-select aruco_docking

echo "[2/5] 正在运行项目测试……"
set +u
source install/setup.bash
set -u
python3 -m pytest -q src/aruco_docking/test

echo "[3/5] 正在校验 Gazebo 模型……"
gz sdf -k install/aruco_docking/share/aruco_docking/models/aruco_marker/model.sdf
gz sdf -k install/aruco_docking/share/aruco_docking/models/safety_obstacle/model.sdf

echo "[4/5] 正在核对 10 份实验数据……"
mapfile -t RUN_FILES < <(
  find data -maxdepth 1 -type f \
    \( -name 'run_center_*.csv' -o -name 'run_left_*.csv' -o -name 'run_right_*.csv' \) \
    | sort
)
if [[ ${#RUN_FILES[@]} -ne 10 ]]; then
  echo "错误：应有 10 份实验 CSV，当前找到 ${#RUN_FILES[@]} 份。"
  exit 1
fi

echo "[5/5] 正在复算成功率与停车误差……"
python3 scripts/analyze_runs.py "${RUN_FILES[@]}" --target-distance 0.35

echo "交付复核通过：构建、测试、模型和 10 份实验数据均已验证。"
