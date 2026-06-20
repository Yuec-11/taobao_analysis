#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Part 1: 数据清洗与预处理
- 缺失值、重复值、异常值检查
- 时间格式统一，生成日期/小时/星期等派生字段
- 对原始数据进行逐块处理与分层采样
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    RAW_DATA_PATH, OUTPUT_DIR, STATS_DIR, CLEANED_DATA, REPORT_DIR,
    COLUMNS, BEHAVIOR_MAP, VALID_BEHAVIORS,
    TS_MIN, TS_MAX, CHUNK_SIZE, SAMPLE_RATIO, ensure_dirs, check_raw_data
)

# 确保目录存在
ensure_dirs()

REPORT_FILE = os.path.join(REPORT_DIR, 'data_quality_report.txt')


def inspect_raw_data():
    """检查原始数据概况"""
    print('=' * 60)
    print('【1】原始数据概览')
    print('=' * 60)

    # 读取第一块了解结构
    chunk = pd.read_csv(RAW_DATA_PATH, names=COLUMNS, nrows=10000)
    print(f'  列名: {list(chunk.columns)}')
    print(f'  数据类型:\n{chunk.dtypes.to_string()}')
    print(f'\n  行为类型分布:')
    print(chunk['behavior_type'].value_counts().to_string())
    print(f'\n  时间戳范围: {chunk["timestamp"].min()} ~ {chunk["timestamp"].max()}')

    # 估算总行数
    total_est = sum(1 for _ in open(RAW_DATA_PATH, 'rb'))
    print(f'\n  估算总行数: {total_est:,}')

    return total_est


def chunked_quality_check():
    """逐块检查数据质量（内存友好）"""
    print('\n' + '=' * 60)
    print('【2】数据质量检查（逐块）')
    print('=' * 60)

    total_rows = 0
    total_duplicates = 0
    total_nulls = pd.Series([0] * 5, index=COLUMNS)
    invalid_timestamps = 0
    invalid_behaviors = 0
    unique_users = set()
    unique_items = set()
    unique_cats = set()
    min_ts = float('inf')
    max_ts = float('-inf')

    chunk_iter = pd.read_csv(RAW_DATA_PATH, names=COLUMNS, chunksize=CHUNK_SIZE)

    for i, chunk in enumerate(chunk_iter):
        total_rows += len(chunk)

        # 空值检查
        nulls = chunk.isnull().sum()
        total_nulls += nulls

        # 重复行检查
        total_duplicates += chunk.duplicated().sum()

        # 行为类型合法性
        invalid_behaviors += (~chunk['behavior_type'].isin(VALID_BEHAVIORS)).sum()

        # 时间戳合法范围
        valid_ts_range = (chunk['timestamp'] >= TS_MIN) & (chunk['timestamp'] <= TS_MAX)
        invalid_timestamps += (~valid_ts_range).sum()

        # 唯一值收集（采样前几块就够了）
        if i < 5:
            unique_users.update(chunk['user_id'].unique())
            unique_items.update(chunk['item_id'].unique())
            unique_cats.update(chunk['category_id'].unique())

        if (i + 1) % 10 == 0:
            print(f'  已检查 {(i+1)*CHUNK_SIZE/1e6:.0f}M 行...', end='\r')

    print(f'\n  总检查行数: {total_rows:,}')
    print(f'  空值统计:')
    for col in COLUMNS:
        print(f'    {col}: {total_nulls[col]:,}')
    print(f'  重复行数: {total_duplicates:,} ({total_duplicates/total_rows*100:.4f}%)')
    print(f'  非法行为类型: {invalid_behaviors:,}')
    print(f'  异常时间戳: {invalid_timestamps:,}')
    print(f'  预估唯一用户: {len(unique_users):,}')
    print(f'  预估唯一商品: {len(unique_items):,}')
    print(f'  预估唯一品类: {len(unique_cats):,}')

    return {
        'total_rows': total_rows,
        'total_duplicates': total_duplicates,
        'total_nulls': total_nulls,
        'invalid_behaviors': invalid_behaviors,
        'invalid_timestamps': invalid_timestamps,
    }


def clean_and_sample(sample_ratio=SAMPLE_RATIO, seed=42):
    """
    数据清洗 + 分层采样
    - 去除重复行
    - 过滤非法行为类型
    - 过滤异常时间戳
    - 采样以适应后续分析
    """
    print('\n' + '=' * 60)
    print(f'【3】数据清洗 + 分层采样 (ratio={sample_ratio})')
    print('=' * 60)

    cleaned_chunks = []
    total_processed = 0

    chunk_iter = pd.read_csv(RAW_DATA_PATH, names=COLUMNS, chunksize=CHUNK_SIZE)

    for i, chunk in enumerate(chunk_iter):
        # 清洗
        chunk = chunk.drop_duplicates()
        chunk = chunk[chunk['behavior_type'].isin(VALID_BEHAVIORS)]
        chunk = chunk[(chunk['timestamp'] >= TS_MIN) & (chunk['timestamp'] <= TS_MAX)]

        # 转换时间
        chunk['datetime'] = pd.to_datetime(chunk['timestamp'], unit='s')
        chunk['date'] = chunk['datetime'].dt.date
        chunk['hour'] = chunk['datetime'].dt.hour
        chunk['weekday'] = chunk['datetime'].dt.weekday  # 0=周一
        chunk['weekday_name'] = chunk['datetime'].dt.day_name()
        chunk['weekend'] = chunk['weekday'].isin([5, 6]).astype(int)
        chunk['date_str'] = chunk['datetime'].dt.strftime('%Y-%m-%d')

        # 加入行为中文标签
        chunk['behavior_label'] = chunk['behavior_type'].map(BEHAVIOR_MAP)

        # 采样（按用户分层）
        if sample_ratio < 1.0:
            users = chunk['user_id'].unique()
            n_sample = max(1, int(len(users) * sample_ratio))
            rng = np.random.default_rng(seed + i)
            sampled_users = rng.choice(users, size=n_sample, replace=False)
            chunk = chunk[chunk['user_id'].isin(sampled_users)]

        cleaned_chunks.append(chunk)
        total_processed += len(chunk)

        if (i + 1) % 10 == 0:
            print(f'  已处理 {(i+1)*CHUNK_SIZE/1e6:.0f}M 行...', end='\r')

    # 合并
    df_clean = pd.concat(cleaned_chunks, ignore_index=True)
    print(f'\n\n  清洗后行数: {len(df_clean):,}')
    print(f'  唯一用户: {df_clean["user_id"].nunique():,}')
    print(f'  唯一商品: {df_clean["item_id"].nunique():,}')
    print(f'  时间范围: {df_clean["datetime"].min()} ~ {df_clean["datetime"].max()}')

    # 保存为 parquet（去掉 datetime 等 fastparquet 不兼容的列）
    print(f'\n  保存到 {CLEANED_DATA} ...')
    df_clean = df_clean.drop(
        columns=['datetime', 'date', 'date_str', 'weekday_name', 'behavior_label'],
        errors='ignore'
    )
    df_clean.to_parquet(CLEANED_DATA, index=False, engine='fastparquet')
    print(f'  保存完成！')

    # 保存清洗摘要
    summary = df_clean.groupby('behavior_type').agg(
        记录数=('user_id', 'count'),
        独立用户=('user_id', 'nunique'),
        独立商品=('item_id', 'nunique')
    ).reset_index()
    summary['行为'] = summary['behavior_type'].map(BEHAVIOR_MAP)

    summary.to_csv(f'{STATS_DIR}/cleaning_summary.csv', index=False, encoding='utf-8-sig')
    print(f'\n  清洗摘要:\n{summary.to_string(index=False)}')

    return df_clean


def generate_quality_report(quality_stats):
    """生成数据质量报告"""
    print('\n' + '=' * 60)
    print('【4】生成数据质量报告')
    print('=' * 60)

    lines = [
        '=' * 70,
        f'  淘宝用户行为数据 - 数据质量报告',
        f'  生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '=' * 70,
        '',
        '一、原始数据概览',
        '-' * 40,
        f'  总行数: {quality_stats["total_rows"]:,}',
        f'  列数: 5 (user_id, item_id, category_id, behavior_type, timestamp)',
        f'  数据来源: 阿里云天池 - 淘宝用户行为数据',
        f'  时间跨度: 2017年11月25日 ~ 2017年12月3日',
        '',
        '二、数据质量检查',
        '-' * 40,
        f'  缺失值: {quality_stats["total_nulls"].sum():,} 个（无缺失）',
        f'  重复行: {quality_stats["total_duplicates"]:,} 个 '
        f'({quality_stats["total_duplicates"]/quality_stats["total_rows"]*100:.4f}%)',
        f'  非法行为类型: {quality_stats["invalid_behaviors"]:,} 条',
        f'  异常时间戳: {quality_stats["invalid_timestamps"]:,} 条',
        '',
        '三、字段说明',
        '-' * 40,
        '  user_id: 用户ID（脱敏）',
        '  item_id: 商品ID（脱敏）',
        '  category_id: 商品类目ID（脱敏）',
        '  behavior_type: 行为类型（pv=浏览, buy=购买, cart=加购, fav=收藏）',
        '  timestamp: 行为发生时间戳（Unix时间戳，秒级）',
        '',
        '四、清洗策略',
        '-' * 40,
        '  1. 去除完全重复的行',
        '  2. 过滤非法行为类型（仅保留 pv/buy/cart/fav）',
        '  3. 过滤异常时间戳（仅保留2017年11月~12月范围内）',
        '  4. 将Unix时间戳转换为datetime格式',
        '  5. 生成派生字段：date, hour, weekday, weekday_name, weekend, date_str',
        '  6. 添加行为中文标签',
        '  7. 按用户分层采样10%用于后续分析',
        '',
        '=' * 70,
    ]

    report = '\n'.join(lines)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    return report


if __name__ == '__main__':
    print('淘宝用户行为数据 - 数据清洗模块')
    print('=' * 60)

    # 检查原始数据是否存在
    data_path = check_raw_data()
    if data_path and data_path != RAW_DATA_PATH:
        print(f'  使用原始数据: {data_path}')
    elif not data_path:
        print(f'  ⚠ 未找到原始数据文件！')
        print(f'  请将 UserBehavior.csv 放入: {os.path.join("data", "raw")}')
        sys.exit(1)

    # 1. 检查原始数据
    total_est = inspect_raw_data()

    # 2. 质量检查
    quality_stats = chunked_quality_check()

    # 3. 清洗 + 采样（默认10%）
    df_clean = clean_and_sample()

    # 4. 生成报告
    generate_quality_report(quality_stats)

    print('\n✅ 数据清洗完成！')
    print(f'  清洗数据: {CLEANED_DATA}')
    print(f'  质量报告: {REPORT_FILE}')
