#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
淘宝用户行为数据分析 - 主控脚本
运行全部分析流程
"""

import os
import sys
import time
import subprocess
from datetime import datetime


def run_script(script_path, label):
    """运行一个分析脚本并计时"""
    print('\n' + '=' * 70)
    print(f'  [{datetime.now().strftime("%H:%M:%S")}] 开始: {label}')
    print(f'  脚本: {script_path}')
    print('=' * 70)

    start = time.time()

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=False,
        text=True,
    )

    elapsed = time.time() - start
    mins, secs = divmod(elapsed, 60)

    print(f'\n  [{datetime.now().strftime("%H:%M:%S")}] 完成: {label}')
    print(f'  耗时: {int(mins)}分{secs:.1f}秒')
    print('=' * 70)

    return elapsed


def main():
    """运行全部分析流程"""
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║       淘宝用户行为数据 - 全部分析流程                   ║')
    print(f'║       启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                   ║')
    print('╚══════════════════════════════════════════════════════════╝')

    # 脚本目录（run_all.py 所在的目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 分析脚本列表（按执行顺序）
    steps = [
        ('01_data_cleaning.py',          '数据清洗与预处理'),
        ('02_user_behavior_analysis.py', '用户行为分析'),
        ('03_conversion_funnel.py',      '行为转化漏斗分析'),
        ('04_user_value_analysis.py',    '用户价值与RFM分析'),
        ('05_visualization.py',          '可视化图表生成'),
        ('06_sql_analysis.py',           'SQL分析'),
        ('07_export_for_powerbi.py',     'Power BI数据导出'),
    ]

    total_times = {}
    total_start = time.time()

    for script_name, label in steps:
        script_path = os.path.join(script_dir, script_name)
        t = run_script(script_path, label)
        total_times[label] = t

    total_time = time.time() - total_start
    total_mins, total_secs = divmod(total_time, 60)

    # 结果汇总
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║                 全部流程完成！                          ║')
    print('╠══════════════════════════════════════════════════════════╣')
    for label, t in total_times.items():
        print(f'║  {label:<20} {t:>6.1f}秒                      ║')
    print(f'║  总耗时:            {int(total_mins)}分{total_secs:.1f}秒                            ║')
    print('╠══════════════════════════════════════════════════════════╣')
    print('║  输出目录:                                              ║')
    print('║    Stats:  output/stats/                                ║')
    print('║    Charts: output/charts/                               ║')
    print('║    PowerBI: output/powerbi/                             ║')
    print('║    Report: output/reports/                              ║')
    print('╚══════════════════════════════════════════════════════════╝')


if __name__ == '__main__':
    main()
