# Windows、WSL 2 与 ROS 2 Humble 环境安装

本项目使用 Ubuntu 22.04 和 ROS 2 Humble。Gazebo 图形窗口通过 Windows 11 的 WSLg 显示。

## 1. 安装 WSL 2

以管理员身份打开 PowerShell：

```powershell
wsl --install -d Ubuntu-22.04
```

重启 Windows，打开 Ubuntu 22.04，并创建 Linux 用户名和密码。随后在 PowerShell 验证：

```powershell
wsl --list --verbose
```

预期结果包含 `Ubuntu-22.04`，`VERSION` 为 `2`。

## 2. 安装 ROS 2 Humble

在 Ubuntu 终端按照 ROS 官方的 [Ubuntu deb packages 安装步骤](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) 安装 `ros-humble-desktop`。

安装完成后执行：

```bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
source ~/.bashrc
ros2 --help
```

## 3. 安装项目依赖

```bash
sudo apt update
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-opencv \
  python3-rosdep \
  ros-humble-cv-bridge \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-turtlebot3-gazebo
```

若系统中尚未初始化 rosdep：

```bash
sudo rosdep init
rosdep update
```

TurtleBot3 官方也提供[从源码安装仿真包的步骤](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/)。

## 4. 验证图形与 TurtleBot3 仿真

```bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot3_gazebo empty_world.launch.py
```

Gazebo 窗口打开并显示 Waffle Pi 后，关闭该进程，再回到 README 的构建步骤。

## 5. 访问 E 盘仓库

WSL 中的项目路径为：

```bash
cd /mnt/e/Adai/Project/ros2-aruco-docking-mvp
```

项目构建会在仓库根目录生成 `build/`、`install/` 和 `log/`。这些目录已加入 `.gitignore`。

## 常见检查

```bash
echo "$ROS_DISTRO"
printenv TURTLEBOT3_MODEL
ros2 pkg prefix turtlebot3_gazebo
python3 -c "import cv2; print(cv2.__version__, hasattr(cv2, 'aruco'))"
```

四项输出应分别显示 `humble`、`waffle_pi`、包安装路径，以及包含 ArUco 模块的 OpenCV 版本。
