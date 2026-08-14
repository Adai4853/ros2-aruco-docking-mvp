from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory("aruco_docking"),
        "config",
        "docking.yaml",
    )
    config = LaunchConfiguration("config")
    return LaunchDescription(
        [
            DeclareLaunchArgument("config", default_value=default_config),
            Node(
                package="aruco_docking",
                executable="aruco_docking_node",
                name="aruco_docking_node",
                output="screen",
                parameters=[config, {"use_sim_time": True}],
            ),
        ]
    )
