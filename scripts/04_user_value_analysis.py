#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Part 4: 用户价值分析（RFM分析与用户分群）
- RFM模型构建
- 用户价值分层
- 高价值用户特征分析
"""

import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    CLEANED_DATA, STATS_DIR,
    PARQUET_COLUMNS, BEHAVIOR_MAP, ensure_dirs
)

ensure_dirs()


def load_data():
    """加载清洗后数据"""
    print('加载清洗后数据...')
    df = pd.read_parquet(CLEANED_DATA, engine="fastparquet", columns=PARQUET_COLUMNS)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['datetime'].dt.date.astype(str)
    print(f'  行数: {len(df):,}')
    print(f'  用户数: {df["user_id"].nunique():,}')
    return df


def rfm_analysis(df):
    """
    【4.1】RFM模型构建
    R (Recency): 最近一次购买距观察窗口结束的天数
    F (Frequency): 购买频率（行为总次数）
    M (Monetary): 无金额数据，使用 fav*2 + cart*3 + buy*5 作为价值代理
    """
    print('\n' + '=' * 60)
    print('【4.1】RFM模型构建')
    print('=' * 60)

    last_date = df['datetime'].max()
    print(f'  参考时间点: {last_date}')

    # 仅限有购买行为的用户做RFM
    buy_users = df[df['behavior_type'] == 'buy']
    if len(buy_users) < 1000:
        print('  购买用户较少，用所有行为用户的综合指标')
        buy_users = df

    rfm = buy_users.groupby('user_id').agg(
        Recency=('datetime', 'max'),
        Frequency=('behavior_type', 'count'),
        Diversity=('category_id', 'nunique'),
    ).reset_index()

    # 计算R值（距离参考时间的天数）
    rfm['Recency_Days'] = (last_date - rfm['Recency']).dt.total_seconds() / (3600 * 24)
    rfm['Recency_Days'] = rfm['Recency_Days'].round(1)

    # 添加更多行为维度的聚合
    user_stats = df.groupby('user_id').agg(
        total_pv=('behavior_type', lambda x: (x == 'pv').sum()),
        total_fav=('behavior_type', lambda x: (x == 'fav').sum()),
        total_cart=('behavior_type', lambda x: (x == 'cart').sum()),
        total_buy=('behavior_type', lambda x: (x == 'buy').sum()),
        active_days=('date', 'nunique'),
        items_interacted=('item_id', 'nunique'),
    ).reset_index()

    # 价值评分 M = fav*2 + cart*3 + buy*5（加权）
    user_stats['M_Score'] = (user_stats['total_fav'] * 2 +
                              user_stats['total_cart'] * 3 +
                              user_stats['total_buy'] * 5)

    rfm = rfm.merge(user_stats, on='user_id')

    # RFM打分
    r_labels = [4, 3, 2, 1]  # R: 4=最近刚来（最优）
    try:
        rfm['R_Score'] = pd.qcut(rfm['Recency_Days'], q=4, labels=r_labels, duplicates='drop')
    except ValueError:
        rfm['R_Score'] = pd.qcut(rfm['Recency_Days'].rank(method='first'), q=4,
                                  labels=r_labels, duplicates='drop')

    f_labels = [1, 2, 3, 4]  # F: 4=最频繁（最优）
    try:
        rfm['F_Score'] = pd.qcut(rfm['Frequency'], q=4, labels=f_labels, duplicates='drop')
    except ValueError:
        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4,
                                  labels=f_labels, duplicates='drop')

    try:
        rfm['M_Score'] = pd.qcut(rfm['M_Score'], q=4, labels=f_labels, duplicates='drop')
    except ValueError:
        rfm['M_Score'] = pd.qcut(rfm['M_Score'].rank(method='first'), q=4,
                                  labels=f_labels, duplicates='drop')

    rfm['R_Score'] = rfm['R_Score'].astype(int)
    rfm['F_Score'] = rfm['F_Score'].astype(int)
    rfm['M_Score'] = rfm['M_Score'].astype(int)
    rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

    print(f'\n  RFM评分完成，RFM总分范围: {rfm["RFM_Score"].min()} ~ {rfm["RFM_Score"].max()}')
    print(f'\n  RFM统计摘要:')
    print(rfm[['Recency_Days', 'Frequency', 'M_Score', 'RFM_Score']].describe().round(2).to_string())

    rfm.to_csv(f'{STATS_DIR}/rfm_scores.csv', index=False, encoding='utf-8-sig')
    return rfm


def user_segmentation(rfm):
    """【4.2】基于RFM的用户分群"""
    print('\n' + '=' * 60)
    print('【4.2】用户价值分群')
    print('=' * 60)

    def segment_user(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        if r >= 3 and f >= 3 and m >= 3:
            return '高价值用户'
        elif r >= 3 and f >= 3 and m < 3:
            return '重要发展用户'
        elif r >= 3 and f < 3 and m >= 3:
            return '重要保持用户'
        elif r >= 3 and f < 3 and m < 3:
            return '新用户'
        elif r < 3 and f >= 3 and m >= 3:
            return '重要挽留用户'
        elif r < 3 and f >= 3 and m < 3:
            return '一般价值用户'
        elif r < 3 and f < 3 and m >= 3:
            return '一般发展用户'
        else:
            return '流失风险用户'

    rfm['用户分群'] = rfm.apply(segment_user, axis=1)

    segment_stats = rfm['用户分群'].value_counts().reset_index()
    segment_stats.columns = ['用户分群', '用户数']
    segment_stats['占比'] = (segment_stats['用户数'] / segment_stats['用户数'].sum() * 100).round(2)

    print('\n  用户分群结果:')
    print(segment_stats.to_string(index=False))

    segment_profile = rfm.groupby('用户分群').agg(
        用户数=('user_id', 'count'),
        平均R分=('R_Score', 'mean'),
        平均F分=('F_Score', 'mean'),
        平均M分=('M_Score', 'mean'),
        平均RFM=('RFM_Score', 'mean'),
        平均购买数=('total_buy', 'mean'),
        平均加购数=('total_cart', 'mean'),
        平均收藏数=('total_fav', 'mean'),
        平均活跃天数=('active_days', 'mean'),
        平均品类数=('Diversity', 'mean'),
    ).round(2).reset_index()

    print('\n  各分群特征:')
    print(segment_profile.to_string(index=False))

    segment_stats.to_csv(f'{STATS_DIR}/user_segments.csv',
                          index=False, encoding='utf-8-sig')
    segment_profile.to_csv(f'{STATS_DIR}/segment_profile.csv',
                            index=False, encoding='utf-8-sig')

    return segment_stats, segment_profile


def high_value_user_analysis(df, rfm):
    """【4.3】高价值用户特征分析"""
    print('\n' + '=' * 60)
    print('【4.3】高价值用户特征分析')
    print('=' * 60)

    high_value = rfm[rfm['用户分群'] == '高价值用户']
    print(f'  高价值用户数: {len(high_value):,}')

    if len(high_value) < 10:
        print('  高价值用户太少，跳过详细分析')
        return None, None

    high_user_ids = high_value['user_id'].tolist()
    high_df = df[df['user_id'].isin(high_user_ids)]
    other_df = df[~df['user_id'].isin(high_user_ids)]

    comparison = pd.DataFrame({
        '指标': ['人均日行为数', '人均品类数', '人均商品数', '人均活跃天数',
                '周末活跃比', '收藏转化率', '加购转化率'],
        '高价值用户': [
            round(len(high_df) / len(high_df['user_id'].unique()), 2),
            round(high_df['category_id'].nunique() / len(high_df['user_id'].unique()), 2),
            round(high_df['item_id'].nunique() / len(high_df['user_id'].unique()), 2),
            round(high_df.groupby('user_id')['date'].nunique().mean(), 2),
            round(high_df[high_df['weekend'] == 1].shape[0] / len(high_df) * 100, 2),
            round(high_df[high_df['behavior_type'] == 'fav'].shape[0] /
                  max(high_df[high_df['behavior_type'] == 'pv'].shape[0], 1) * 100, 2),
            round(high_df[high_df['behavior_type'] == 'cart'].shape[0] /
                  max(high_df[high_df['behavior_type'] == 'pv'].shape[0], 1) * 100, 2),
        ],
        '其他用户': [
            round(len(other_df) / max(len(other_df['user_id'].unique()), 1), 2),
            round(other_df['category_id'].nunique() / max(len(other_df['user_id'].unique()), 1), 2),
            round(other_df['item_id'].nunique() / max(len(other_df['user_id'].unique()), 1), 2),
            round(other_df.groupby('user_id')['date'].nunique().mean(), 2),
            round(other_df[other_df['weekend'] == 1].shape[0] / max(len(other_df), 1) * 100, 2),
            round(other_df[other_df['behavior_type'] == 'fav'].shape[0] /
                  max(other_df[other_df['behavior_type'] == 'pv'].shape[0], 1) * 100, 2),
            round(other_df[other_df['behavior_type'] == 'cart'].shape[0] /
                  max(other_df[other_df['behavior_type'] == 'pv'].shape[0], 1) * 100, 2),
        ]
    })

    print('\n  高价值 vs 其他用户对比:')
    print(comparison.to_string(index=False))

    comparison.to_csv(f'{STATS_DIR}/high_value_comparison.csv',
                       index=False, encoding='utf-8-sig')

    return high_df, comparison


if __name__ == '__main__':
    print('淘宝用户行为数据 - 用户价值分析')
    print('=' * 60)

    df = load_data()

    rfm = rfm_analysis(df)
    segment_stats, segment_profile = user_segmentation(rfm)
    high_df, comparison = high_value_user_analysis(df, rfm)

    print('\n✅ 用户价值分析完成！')
    print(f'  结果保存在 {STATS_DIR}/')
