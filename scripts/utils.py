#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
共享工具函数模块
提供统一的数据加载、行为映射等公共函数
"""

import pandas as pd
import os
import sys

# Windows 终端编码兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    CLEANED_DATA, PARQUET_COLUMNS, BEHAVIOR_MAP,
    BEHAVIOR_ORDER, BEHAVIOR_LABELS, COLORS, COLORS_CN,
    WEEKDAY_LABELS, WEEKDAY_MAP, ensure_dirs,
)


def load_cleaned_data(columns=None):
    """
    加载清洗后的数据，自动重建派生时间字段

    Parameters:
        columns: 需要从parquet读取的列，默认使用 PARQUET_COLUMNS

    Returns:
        DataFrame with datetime, date, date_str, hour, weekday, weekend
    """
    if columns is None:
        columns = PARQUET_COLUMNS

    df = pd.read_parquet(CLEANED_DATA, engine='fastparquet', columns=columns)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['datetime'].dt.date.astype(str)
    df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')

    # 补全可能缺失的字段
    if 'hour' not in df.columns:
        df['hour'] = df['datetime'].dt.hour
    if 'weekday' not in df.columns:
        df['weekday'] = df['datetime'].dt.weekday
    if 'weekend' not in df.columns:
        df['weekend'] = df['weekday'].isin([5, 6]).astype(int)

    print(f'  行数: {len(df):,}')
    print(f'  用户数: {df["user_id"].nunique():,}')
    print(f'  时间范围: {df["datetime"].min()} ~ {df["datetime"].max()}')
    return df
