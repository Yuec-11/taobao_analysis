#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Power BI 数据导出工具
将分析结果导出为 Power BI 可以直接读取的 CSV/Excel 格式
同时也生成汇总Excel报告
"""

import os
import sys
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    CLEANED_DATA, STATS_DIR, PBI_DIR, REPORT_DIR,
    PARQUET_COLUMNS, BEHAVIOR_MAP, ensure_dirs
)

ensure_dirs()


def export_for_powerbi():
    """导出 Power BI 可直接使用的数据文件"""
    print('=' * 60)
    print('Power BI 数据导出')
    print('=' * 60)

    if not os.path.exists(CLEANED_DATA):
        print(f'  ⚠ 未找到清洗数据，请先运行 01_data_cleaning.py')
        print(f'  需要: {CLEANED_DATA}')
        return

    print('\n  导出用户每日行为聚合表...')
    df = pd.read_parquet(CLEANED_DATA, engine="fastparquet", columns=PARQUET_COLUMNS)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['datetime'].dt.date.astype(str)
    df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')
    df['weekday_name'] = df['datetime'].dt.day_name()

    # 用户-日-行为 聚合
    daily_agg = df.groupby(['user_id', 'date_str', 'behavior_type']).agg(
        行为次数=('behavior_type', 'count'),
        独立商品数=('item_id', 'nunique'),
        独立品类数=('category_id', 'nunique'),
    ).reset_index()
    daily_agg['行为'] = daily_agg['behavior_type'].map(BEHAVIOR_MAP)

    # 宽表
    pivot = daily_agg.pivot_table(
        index=['user_id', 'date_str'],
        columns='behavior_type',
        values='行为次数',
        fill_value=0
    ).reset_index()
    pivot.columns.name = None
    for bt in ['pv', 'fav', 'cart', 'buy']:
        if bt not in pivot.columns:
            pivot[bt] = 0
    pivot.columns = ['user_id', 'date_str', '浏览数', '收藏数', '加购数', '购买数']

    # 星期信息
    day_info = df[['date_str', 'weekday', 'weekday_name', 'weekend']].drop_duplicates()
    final = pivot.merge(day_info, on='date_str', how='left')

    final.to_csv(f'{PBI_DIR}/user_daily_behavior.csv', index=False, encoding='utf-8-sig')
    print(f'  ✅ 用户日行为表: {len(final):,} 行')

    # 2. 用户统计特征表
    user_stats = df.groupby('user_id').agg(
        活跃天数=('date', 'nunique'),
        总浏览=('behavior_type', lambda x: (x == 'pv').sum()),
        总收藏=('behavior_type', lambda x: (x == 'fav').sum()),
        总加购=('behavior_type', lambda x: (x == 'cart').sum()),
        总购买=('behavior_type', lambda x: (x == 'buy').sum()),
        浏览品类数=('category_id', 'nunique'),
        浏览商品数=('item_id', 'nunique'),
    ).reset_index()

    user_stats.to_csv(f'{PBI_DIR}/user_profile.csv', index=False, encoding='utf-8-sig')
    print(f'  ✅ 用户画像表: {len(user_stats):,} 行')

    # 3. 商品统计表
    item_stats = df.groupby(['item_id', 'category_id']).agg(
        总浏览=('behavior_type', lambda x: (x == 'pv').sum()),
        总收藏=('behavior_type', lambda x: (x == 'fav').sum()),
        总加购=('behavior_type', lambda x: (x == 'cart').sum()),
        总购买=('behavior_type', lambda x: (x == 'buy').sum()),
        独立用户=('user_id', 'nunique'),
    ).reset_index()

    item_stats.to_csv(f'{PBI_DIR}/item_stats.csv', index=False, encoding='utf-8-sig')
    print(f'  ✅ 商品统计表: {len(item_stats):,} 行')

    # 4. 每日汇总表
    daily_summary = df.groupby('date_str').agg(
        活跃用户=('user_id', 'nunique'),
        总浏览=('behavior_type', lambda x: (x == 'pv').sum()),
        总收藏=('behavior_type', lambda x: (x == 'fav').sum()),
        总加购=('behavior_type', lambda x: (x == 'cart').sum()),
        总购买=('behavior_type', lambda x: (x == 'buy').sum()),
        浏览商品=('item_id', 'nunique'),
    ).reset_index()

    daily_summary.to_csv(f'{PBI_DIR}/daily_summary.csv', index=False, encoding='utf-8-sig')
    print(f'  ✅ 每日汇总表: {len(daily_summary):,} 行')

    # 5. 小时维度汇总
    hourly_summary = df.groupby(['hour', 'weekday', 'weekend']).agg(
        行为数=('behavior_type', 'count'),
        用户数=('user_id', 'nunique'),
    ).reset_index()

    hourly_summary.to_csv(f'{PBI_DIR}/hourly_summary.csv', index=False, encoding='utf-8-sig')
    print(f'  ✅ 小时维度表: {len(hourly_summary):,} 行')

    print(f'\n  Power BI 数据已导出到: {PBI_DIR}/')
    print('  Power BI 中可直接加载以下CSV文件:')
    for f in os.listdir(PBI_DIR):
        size = os.path.getsize(f'{PBI_DIR}/{f}') / 1024
        print(f'    - {f} ({size:.0f} KB)')


def generate_excel_report():
    """生成综合Excel报告"""
    print('\n  生成综合Excel报告...')

    excel_path = f'{REPORT_DIR}/taobao_analysis_report.xlsx'
    writer = pd.ExcelWriter(excel_path, engine='openpyxl')

    sheets_data = []

    for f in os.listdir(STATS_DIR):
        if f.endswith('.csv'):
            try:
                df = pd.read_csv(f'{STATS_DIR}/{f}')
                sheet_name = f.replace('.csv', '')[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                sheets_data.append(sheet_name)
                print(f'    写入: {sheet_name}')
            except Exception as e:
                print(f'    ⚠ 跳过 {f}: {e}')

    writer.close()
    print(f'  ✅ Excel报告已生成: {excel_path}')
    print(f'  包含 {len(sheets_data)} 个工作表:')
    for s in sheets_data:
        print(f'    - {s}')

    return excel_path


if __name__ == '__main__':
    export_for_powerbi()
    generate_excel_report()
    print('\n✅ Power BI 数据导出完成！')
