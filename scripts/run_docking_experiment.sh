#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$WORKSPACE_DIR"

usage() {
  echo "用法：bash scripts/run_docking_experiment.sh <center|left|right> <两位编号>"
  echo "示例：bash scripts/run_docking_experiment.sh center 01"
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

PROFILE="$1"
RUN_NUMBER="$2"
if [[ ! "$RUN_NUMBER" =~ ^[0-9]{2}$ ]]; then
  echo "错误：实验编号需要使用两位数字，例如 01。"
  exit 2
fi

case "$PROFILE" in
  center)
    START_Y="0.00"
    PROFILE_LABEL="正前方"
    ;;
  left)
    START_Y="0.35"
    PROFILE_LABEL="左偏 0.35 米"
    ;;
  right)
    START_Y="-0.35"
    PROFILE_LABEL="右偏 0.35 米"
    ;;
  *)
    echo "错误：起点类型需要填写 center、left 或 right。"
    usage
    exit 2
    ;;
esac

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

if ! ros2 service list 2>/dev/null | grep -qx '/spawn_entity' || \
   ! ros2 service list 2>/dev/null | grep -qx '/delete_entity'; then
  echo "错误：Gazebo 场景尚未准备好。"
  echo "请先运行：bash scripts/start_docking_demo.sh"
  exit 1
fi

if ros2 node list 2>/dev/null | grep -qx '/aruco_docking_node'; then
  echo "错误：自动停靠节点正在运行。"
  echo "请在该节点的终端按 Ctrl+C，然后重新执行本命令。"
  exit 1
fi

CSV_PATH="$WORKSPACE_DIR/data/run_${PROFILE}_${RUN_NUMBER}.csv"
if [[ -e "$CSV_PATH" ]]; then
  echo "错误：实验文件已经存在：$CSV_PATH"
  echo "请使用新的实验编号，现有记录会继续保留。"
  exit 1
fi

DOCKING_PID=""
cleanup() {
  if [[ -n "$DOCKING_PID" ]] && kill -0 "$DOCKING_PID" 2>/dev/null; then
    CHILD_PIDS="$(pgrep -P "$DOCKING_PID" 2>/dev/null || true)"
    while IFS= read -r CHILD_PID; do
      if [[ -n "$CHILD_PID" ]]; then
        kill -TERM "$CHILD_PID" 2>/dev/null || true
      fi
    done <<< "$CHILD_PIDS"

    # Background jobs inherit SIGINT as ignored. SIGTERM terminates the
    # launch parent after its node children have received the same signal.
    kill -TERM "$DOCKING_PID" 2>/dev/null || true
    wait "$DOCKING_PID" 2>/dev/null || true

    while IFS= read -r CHILD_PID; do
      if [[ -n "$CHILD_PID" ]] && kill -0 "$CHILD_PID" 2>/dev/null; then
        kill -KILL "$CHILD_PID" 2>/dev/null || true
      fi
    done <<< "$CHILD_PIDS"
  fi
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}' >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

echo "实验：${PROFILE_LABEL}，编号 ${RUN_NUMBER}。"
echo "正在重建机器人并设置起点 x=-1.50、y=${START_Y} 米……"
ros2 service call /delete_entity gazebo_msgs/srv/DeleteEntity \
  "{name: waffle_pi}" >/dev/null
sleep 1

TB3_PREFIX="$(ros2 pkg prefix turtlebot3_gazebo)"
TB3_MODEL_FILE="$TB3_PREFIX/share/turtlebot3_gazebo/models/turtlebot3_waffle_pi/model.sdf"
if [[ ! -f "$TB3_MODEL_FILE" ]]; then
  echo "错误：没有找到 TurtleBot3 waffle_pi 模型。"
  exit 1
fi

ros2 run gazebo_ros spawn_entity.py \
  -entity waffle_pi \
  -file "$TB3_MODEL_FILE" \
  -x -1.5 -y "$START_Y" -z 0.01
sleep 2

echo "正在启动自动停靠，记录文件：data/run_${PROFILE}_${RUN_NUMBER}.csv"
ros2 launch aruco_docking docking.launch.py csv_path:="$CSV_PATH" &
DOCKING_PID=$!

HAS_TRACKED=false
RESULT="timeout"
MAX_RUNTIME_SEC=90
START_REAL_SEC=$SECONDS

while (( SECONDS - START_REAL_SEC < MAX_RUNTIME_SEC )); do
  if ! kill -0 "$DOCKING_PID" 2>/dev/null; then
    RESULT="node_exited"
    break
  fi

  if [[ -s "$CSV_PATH" ]]; then
    LAST_ROW="$(tail -n 1 "$CSV_PATH")"
    IFS=',' read -r TIMESTAMP STATE MARKER_FOUND MARKER_ID HORIZONTAL_ERROR \
      DISTANCE_M FRONT_OBSTACLE_M LINEAR_X ANGULAR_Z STOP_REASON <<< "$LAST_ROW"
    # Python's CSV writer uses CRLF rows. Remove the trailing carriage return
    # before comparing the final stop_reason field.
    STOP_REASON="${STOP_REASON%$'\r'}"

    if [[ "$STATE" == "TRACK" ]]; then
      HAS_TRACKED=true
    fi

    if [[ "$STOP_REASON" == "reached" ]]; then
      RESULT="reached"
      break
    fi

    if [[ "$HAS_TRACKED" == true ]] && \
       [[ "$STOP_REASON" == "target_lost" || "$STOP_REASON" == "obstacle" || "$STOP_REASON" == "image_timeout" ]]; then
      RESULT="$STOP_REASON"
      break
    fi
  fi
  sleep 0.2
done

if [[ "$RESULT" == "reached" ]]; then
  echo "实验通过：机器人到达目标距离并停车。"
  EXIT_CODE=0
else
  echo "实验未通过：结束原因 ${RESULT}。"
  EXIT_CODE=1
fi

if [[ -f "$CSV_PATH" ]]; then
  python3 scripts/analyze_runs.py "$CSV_PATH" --target-distance 0.35
fi

exit "$EXIT_CODE"
