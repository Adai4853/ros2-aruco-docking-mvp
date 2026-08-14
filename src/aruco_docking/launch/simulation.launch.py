import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("aruco_docking")
    turtlebot_share = get_package_share_directory("turtlebot3_gazebo")
    models_dir = os.path.join(package_share, "models")
    existing_model_path = os.environ.get("GAZEBO_MODEL_PATH", "")

    simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot_share, "launch", "empty_world.launch.py")
        ),
        launch_arguments={"x_pose": "-1.5", "y_pose": "0.0"}.items(),
    )
    marker_model = os.path.join(models_dir, "aruco_marker", "model.sdf")
    spawn_marker = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-entity",
            "aruco_marker",
            "-file",
            marker_model,
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.16",
        ],
        output="screen",
    )
    return LaunchDescription(
        [
            SetEnvironmentVariable("TURTLEBOT3_MODEL", "waffle_pi"),
            SetEnvironmentVariable(
                "GAZEBO_MODEL_PATH",
                models_dir + os.pathsep + existing_model_path,
            ),
            simulator,
            TimerAction(period=3.0, actions=[spawn_marker]),
        ]
    )
