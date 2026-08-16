#!/usr/bin/env bash
set -euo pipefail

# 找到脚本所在项目目录，无论你从哪个目录执行它都可以。
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "错误：没有找到 ROS 2 Humble。"
  exit 1
fi

if [[ ! -f install/setup.bash ]]; then
  echo "错误：没有找到 install/setup.bash。"
  echo "请先在项目根目录运行：colcon build --packages-select aruco_docking"
  exit 1
fi

# 让当前终端认识 ROS 2 和本项目编译出来的包。
# ROS 2 的环境脚本会读取一些允许为空的变量，因此加载期间暂时关闭
# “未定义变量即报错”；加载完成后再恢复严格检查。
set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u

# 告诉 TurtleBot3 和 Gazebo 使用哪种机器人、去哪里寻找本项目模型。
export TURTLEBOT3_MODEL=waffle_pi
export GAZEBO_MODEL_PATH="$WORKSPACE_DIR/install/aruco_docking/share/aruco_docking/models:${GAZEBO_MODEL_PATH:-}"

# 避免重复启动两个 Gazebo；两个仿真世界会互相干扰。
if ros2 service list 2>/dev/null | grep -qx '/spawn_entity'; then
  echo "检测到 Gazebo 已经在运行。"
  echo "请先在原来启动 Gazebo 的终端按 Ctrl+C，再重新执行本脚本。"
  exit 1
fi

cleanup() {
  if [[ -n "${GAZEBO_PID:-}" ]] && kill -0 "$GAZEBO_PID" 2>/dev/null; then
    kill -INT "$GAZEBO_PID" 2>/dev/null || true
    wait "$GAZEBO_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "[1/4] 正在启动 Gazebo 空世界……"
ros2 launch gazebo_ros gazebo.launch.py verbose:=false &
GAZEBO_PID=$!

echo "[2/4] 正在等待 Gazebo 准备好模型入口 /spawn_entity……"
for _ in $(seq 1 45); do
  if ros2 service list 2>/dev/null | grep -qx '/spawn_entity'; then
    break
  fi
  if ! kill -0 "$GAZEBO_PID" 2>/dev/null; then
    echo "错误：Gazebo 提前退出，请查看上面的报错。"
    exit 1
  fi
  sleep 1
done

if ! ros2 service list 2>/dev/null | grep -qx '/spawn_entity'; then
  echo "错误：等待 45 秒后，Gazebo 仍未准备好。"
  exit 1
fi

echo "[3/4] 正在放入 ArUco 标记……"
ros2 run gazebo_ros spawn_entity.py \
  -entity aruco_marker \
  -file "$WORKSPACE_DIR/install/aruco_docking/share/aruco_docking/models/aruco_marker/model.sdf" \
  -x 0.0 -y 0.0 -z 0.16

TB3_PREFIX="$(ros2 pkg prefix turtlebot3_gazebo)"
echo "[4/4] 正在放入 TurtleBot3 waffle_pi……"
ros2 run gazebo_ros spawn_entity.py \
  -entity waffle_pi \
  -file "$TB3_PREFIX/share/turtlebot3_gazebo/models/turtlebot3_waffle_pi/model.sdf" \
  -x -1.5 -y 0.0 -z 0.01

echo
echo "启动完成。Gazebo 左侧 Models 中应看到："
echo "  ground_plane、aruco_marker、waffle_pi"
echo "本脚本没有启动自动停靠控制，机器人不会自行运动。"
echo "需要结束时，请回到这个终端按 Ctrl+C。"

wait "$GAZEBO_PID"
