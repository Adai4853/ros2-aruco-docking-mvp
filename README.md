# ROS 2 ArUco 视觉停靠

这个项目为 TurtleBot3 Waffle Pi 提供 ArUco 视觉停靠控制。ROS 2 节点读取相机图像和激光雷达数据，发布 `geometry_msgs/Twist`，并把控制过程写入 CSV。

## 当前状态

| 项目 | 状态 |
|---|---|
| ROS 2 Python 包与 YAML 参数 | 已编写 |
| ArUco ID 选择、水平误差与距离估计 | 已编写 |
| SEARCH / TRACK / STOP 状态机 | 已编写 |
| 图像超时、目标丢失、前方障碍停车 | 已编写 |
| CSV 运行记录与统计脚本 | 已编写 |
| 纯 Python 控制器与 CSV 记录器测试 | 10 项测试已通过 |
| ROS 2 构建与 Gazebo 闭环 | 等待 Ubuntu 22.04 / ROS 2 Humble 环境验证 |
| 10 次实验与性能指标 | 等待仿真实验 |

当前电脑尚未安装 WSL、Ubuntu 和 ROS 2。仓库中的“已编写”表示代码文件已创建；运行效果与实验指标将在实际验证后更新。

## 控制流程

```text
/camera/image_raw + /camera/camera_info
                  ↓
          OpenCV ArUco 检测
                  ↓
       水平误差 + 标记距离估计
                  ↓
         SEARCH / TRACK / STOP ← /scan
                  ↓
               /cmd_vel
                  ↓
        TurtleBot3 对准、接近、停车
```

- `SEARCH`：启动后尚未发现标记时原地低速旋转。
- `TRACK`：发现指定标记后先对准，再按距离比例控制前进速度。
- `STOP`：到达目标距离、标记丢失、图像超时或前方障碍进入安全距离时发布零速度。

到达目标距离后，控制器锁定 `STOP`。重新启动节点或调用控制器重置后可开始下一次停靠。

控制器采用以下误差与限幅关系：

```text
horizontal_error = (marker_center_x - image_center_x) / image_center_x
distance_error   = marker_distance - target_distance
angular_z        = clamp(-yaw_kp × horizontal_error)
linear_x         = clamp(distance_kp × distance_error)
```

当 `abs(horizontal_error) > align_threshold` 时，线速度保持为零。

## 目录

```text
config/                         项目级配置预留目录
data/                           CSV 输出目录
docs/                           验收与实验记录
scripts/                        标记生成和 CSV 统计工具
src/aruco_docking/
  aruco_docking/                ROS 2 节点、检测器、控制器、记录器
  config/docking.yaml           控制与安全参数
  launch/                       仿真和节点启动文件
  models/aruco_marker/          Gazebo 标记模型
  test/                         控制器测试
```

## 开始运行

先完成 [Windows 与 ROS 2 环境安装](SETUP_WINDOWS.md)。进入 Ubuntu 终端后，在仓库根目录执行：

```bash
source /opt/ros/humble/setup.bash
python3 scripts/generate_marker.py
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

终端 A 启动 TurtleBot3、Gazebo 和 ArUco 标记：

```bash
ros2 launch aruco_docking simulation.launch.py
```

确认实际话题：

```bash
ros2 topic list | grep -E 'camera|cmd_vel|scan'
ros2 topic hz /camera/image_raw
```

终端 B 启动停靠节点：

```bash
cd /mnt/e/Adai/Project/ros2-aruco-docking-mvp
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch aruco_docking docking.launch.py
```

参数位于 [`src/aruco_docking/config/docking.yaml`](src/aruco_docking/config/docking.yaml)。若仿真发布的话题名称不同，请在该文件中修改 `image_topic`、`camera_info_topic`、`cmd_vel_topic` 和 `scan_topic`。

## 测试与实验

运行包测试：

```bash
colcon test --packages-select aruco_docking --event-handlers console_direct+
colcon test-result --verbose
```

节点默认把数据追加到 `data/docking_run.csv`。每次实验使用独立文件后，可统计成功率和停车误差：

```bash
python3 scripts/analyze_runs.py data/run_*.csv --target-distance 0.35
```

实验位置、命名方法和验收条件见 [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md)。

## 软件基线

- Windows + WSL 2
- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic 11
- TurtleBot3 Waffle Pi
- Python 3.10、OpenCV ArUco、NumPy

安装基线来自 [ROS 2 Humble Ubuntu 安装文档](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) 和 [TurtleBot3 Gazebo 仿真文档](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/)。
