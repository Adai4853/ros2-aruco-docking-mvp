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

## 指标定义

- 成功：运行中出现 `stop_reason=reached`。
- 停车误差：首次到达停车状态时，`abs(distance_m - target_distance_m)`。
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
| 成功次数 / 总次数 | 待测 |
| 成功率 | 待测 |
| 平均停车误差 | 待测 |
| 最大停车误差 | 待测 |
| 目标丢失停车时间 | 待测 |
