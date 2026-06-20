#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
淘宝用户行为数据分析 - 项目入口

用法:
    python main.py              # 运行全部分析流程
    python main.py --step 1     # 只运行第1步（数据清洗）
    python main.py --step 1-4   # 运行第1到第4步
    python main.py --list       # 查看可用的分析步骤

PyCharm 中直接右键 Run 'main' 即可运行全部流程。
"""

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime


# Windows 编码兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── 项目根目录（main.py 所在的目录） ──────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

# 分析步骤定义 (编号, 脚本名, 标签)
STEPS = [
    ('01', '01_data_cleaning.py',          '数据清洗与预处理'),
    ('02', '02_user_behavior_analysis.py', '用户行为分析'),
    ('03', '03_conversion_funnel.py',      '行为转化漏斗分析'),
    ('04', '04_user_value_analysis.py',    '用户价值与RFM分析'),
    ('05', '05_visualization.py',          '可视化图表生成'),
    ('06', '06_sql_analysis.py',           'SQL分析'),
    ('07', '07_export_for_powerbi.py',     'Power BI数据导出'),
]


def run_step(step_num, script_name, label):
    """运行单个分析步骤"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        print(f'  ⚠ 脚本不存在: {script_path}')
        return

    print('\n' + '=' * 70)
    print(f'  [{datetime.now().strftime("%H:%M:%S")}] 步骤 {step_num}/{len(STEPS)}: {label}')
    print(f'  脚本: scripts/{script_name}')
    print('=' * 70)

    start = time.time()

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=PROJECT_ROOT,  # 以项目根目录为工作目录
        capture_output=False,
        text=True,
    )

    elapsed = time.time() - start
    mins, secs = divmod(elapsed, 60)

    print(f'\n  [{datetime.now().strftime("%H:%M:%S")}] 完成: {label}')
    print(f'  耗时: {int(mins)}分{secs:.1f}秒')
    print('=' * 70)

    return elapsed


def list_steps():
    """列出所有可用的分析步骤"""
    print('\n淘宝用户行为数据分析 - 可用的分析步骤')
    print('=' * 60)
    for num, _, label in STEPS:
        print(f'  {num}. {label}')
    print()
    print('  运行全部: python main.py')
    print('  运行单步: python main.py --step 3')
    print('  运行范围: python main.py --step 2-5')
    print()


def parse_step_range(arg):
    """解析 --step 参数，返回要运行的步骤索引列表"""
    if '-' in arg:
        start, end = map(int, arg.split('-'))
        return list(range(start, end + 1))
    else:
        return [int(arg)]


def main():
    parser = argparse.ArgumentParser(
        description='淘宝用户行为数据分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py             运行全部 7 个步骤
  python main.py --step 1    仅运行数据清洗
  python main.py --step 1-4  运行前 4 个步骤
  python main.py --list      列出所有分析步骤
        """
    )
    parser.add_argument('--step', type=str, default=None,
                        help='要运行的步骤编号或范围（如：3 或 2-5）')
    parser.add_argument('--list', action='store_true',
                        help='列出所有分析步骤')
    args = parser.parse_args()

    if args.list:
        list_steps()
        return

    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║       淘宝用户行为数据分析                               ║')
    print(f'║       启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                   ║')
    print('╚══════════════════════════════════════════════════════════╝')
    print(f'  项目目录: {PROJECT_ROOT}')

    # 切换到项目根目录
    os.chdir(PROJECT_ROOT)

    # 确定要运行的步骤
    if args.step:
        step_indices = parse_step_range(args.step)
        steps_to_run = [(STEPS[i - 1]) for i in step_indices if 1 <= i <= len(STEPS)]
    else:
        steps_to_run = STEPS

    print(f'  即将运行 {len(steps_to_run)} 个步骤:\n')
    for num, _, label in steps_to_run:
        print(f'    [{num}] {label}')
    print()

    total_times = {}
    total_start = time.time()

    for num, script_name, label in steps_to_run:
        t = run_step(num, script_name, label)
        total_times[label] = t

    total_time = time.time() - total_start
    total_mins, total_secs = divmod(total_time, 60)

    # 汇总
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║                 分析流程完成！                          ║')
    print('╠══════════════════════════════════════════════════════════╣')
    for label, t in total_times.items():
        print(f'║  {label:<22} {t:>7.1f}秒                    ║')
    print(f'║  总耗时:              {int(total_mins)}分{total_secs:.1f}秒                      ║')
    print('╠══════════════════════════════════════════════════════════╣')
    print('║  输出目录:                                              ║')
    print('║    stats/  → output/stats/                              ║')
    print('║    charts/ → output/charts/                             ║')
    print('║    powerbi/ → output/powerbi/                           ║')
    print('║    report/ → output/reports/                            ║')
    print('╚══════════════════════════════════════════════════════════╝')


if __name__ == '__main__':
    main()
