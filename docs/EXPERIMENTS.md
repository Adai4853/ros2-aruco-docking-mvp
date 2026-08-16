# 停靠实验与验收记录

## MVP 验收

一次有效试验需要满足以下条件：

1. `/camera/image_raw` 持续发布图像，`/camera/camera_info` 提供内参。
2. 节点检测 ID 0 的 `DICT_4X4_50` 标记。
3. 机器人从初始位置完成角度对准并向标记接近。
4. 机器人在配置目标距离附近发布零速度，CSV 的 `stop_reason` 为 `reached`。
5. 遮挡或移走标记后，节点发布零速度，CSV 的 `stop_reason` 为 `target_lost`。
6. 在机器人前方放置近距离障碍物后，节点发布零速度，CSV 的 `stop_reason` 为 `obstacle`。

## 10 次实验设计

每次启动节点前，为 `csv_path` 设置独立文件名。建议分组：

| 初始位置 | 次数 | 建议文件名 |
|---|---:|---|
| 正前方 | 4 | `run_center_01.csv` 至 `run_center_04.csv` |
| 左偏 | 3 | `run_left_01.csv` 至 `run_left_03.csv` |
| 右偏 | 3 | `run_right_01.csv` 至 `run_right_03.csv` |

记录每次实验的初始纵向距离、横向偏移和偏航角。保持标记尺寸、相机参数、目标距离和控制参数一致。

### 单次实验工具

先启动一次干净的基础场景，并让 Gazebo 保持运行：

```bash
cd /mnt/e/Adai/Project/ros2-aruco-docking-mvp
bash scripts/start_docking_demo.sh
```

另开一个 Ubuntu 终端执行单次实验。脚本会设置机器人起点、启动停靠节点、生成独立
CSV，并在实验结束后停止控制节点。Gazebo 会继续运行，供下一次实验复用。

```bash
bash scripts/run_docking_experiment.sh center 01
```

完整 10 次实验命令：

```bash
bash scripts/run_docking_experiment.sh center 01
bash scripts/run_docking_experiment.sh center 02
bash scripts/run_docking_experiment.sh center 03
bash scripts/run_docking_experiment.sh center 04
bash scripts/run_docking_experiment.sh left 01
bash scripts/run_docking_experiment.sh left 02
bash scripts/run_docking_experiment.sh left 03
bash scripts/run_docking_experiment.sh right 01
bash scripts/run_docking_experiment.sh right 02
bash scripts/run_docking_experiment.sh right 03
```

起点坐标为：`center: y=0.00 m`、`left: y=0.35 m`、
`right: y=-0.35 m`，三组的纵向起点均为 `x=-1.50 m`。实验文件写入
`data/run_<位置>_<编号>.csv`。脚本会保留已有文件，并要求新实验使用新编号。

10 次实验完成后运行统计：

```bash
python3 scripts/analyze_runs.py data/run_*.csv --target-distance 0.35
```

## 阶段验收结果（2026-08-16）

| 验收项目 | 实测结果 | 结论 |
|---|---:|---|
| 正常停靠 | 11.5 秒完成；首次停车距离 0.378905 m；目标 0.35 m | 通过，误差 0.028905 m |
| 二维码消失停车 | 最后识别 37.3 秒；停车 38.1 秒 | 通过，响应时间 0.8 秒 |
| 前方障碍停车 | TRACK 后 3.4 秒停车；首次触发距离 0.261047 m | 通过，速度归零 |

障碍停车阈值为 `0.28 m`。三个测试的停车状态分别记录为 `reached`、
`target_lost` 和 `obstacle`。

## 指标定义

- 成功：运行中出现 `stop_reason=reached`。
- 停车误差：首次到达停车状态附近的有效距离记录与目标距离之差。停车行缺少实时
  识别值时，统计器采用停车后的第一条有效距离；该值对应静止状态下的相机估计。
- 成功率：成功次数除以总实验次数。
- 目标丢失停车时间：最后一个 `marker_found=True` 样本到首个 `target_lost` 样本的时间差。

统计命令：

```bash
python3 scripts/analyze_runs.py data/run_*.csv --target-distance 0.35
```

## 结果表

完成仿真实验后填写：

| 指标 | 结果 |
|---|---:|
| 成功次数 / 总次数 | 10 / 10 |
| 成功率 | 100.0% |
| 平均停车误差 | 0.0278 m |
| 最大停车误差 | 0.0298 m |
| 目标丢失停车时间 | 0.8 s |

分组结果：

| 初始位置 | 成功次数 | 成功率 | 平均停车误差 | 最大停车误差 |
|---|---:|---:|---:|---:|
| 正前方 | 4 / 4 | 100.0% | 0.0293 m | 0.0298 m |
| 左偏 0.35 m | 3 / 3 | 100.0% | 0.0264 m | 0.0288 m |
| 右偏 0.35 m | 3 / 3 | 100.0% | 0.0272 m | 0.0286 m |
