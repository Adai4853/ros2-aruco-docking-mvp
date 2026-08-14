from glob import glob
import os

from setuptools import find_packages, setup


package_name = "aruco_docking"

data_files = [
    (
        "share/ament_index/resource_index/packages",
        ["resource/" + package_name],
    ),
    ("share/" + package_name, ["package.xml"]),
    (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
]
for path in glob("models/**/*", recursive=True):
    if os.path.isfile(path):
        data_files.append(
            (os.path.join("share", package_name, os.path.dirname(path)), [path])
        )

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=data_files,
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Adai",
    maintainer_email="adai@example.com",
    description="ArUco-guided visual docking and safety control for TurtleBot3.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "aruco_docking_node = aruco_docking.aruco_docking_node:main",
        ],
    },
)
