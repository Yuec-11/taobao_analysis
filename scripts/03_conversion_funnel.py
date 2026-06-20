#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Part 3: 行为转化分析（漏斗分析）
- 浏览 -> 收藏 -> 加购 -> 购买 转化率
- 各环节流失分析
- 用户行为路径序列分析
- 购买前行为模式分析
"""

import os
import sys
import pandas as pd
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    CLEANED_DATA, STATS_DIR, CHART_DIR,
    PARQUET_COLUMNS, BEHAVIOR_MAP, BEHAVIOR_ORDER, ensure_dirs
)

ensure_dirs()


def load_data():
    """加载清洗后数据"""
    print('加载清洗后数据...')
    df = pd.read_parquet(CLEANED_DATA, engine="fastparquet", columns=PARQUET_COLUMNS)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')
    print(f'  行数: {len(df):,}')
    print(f'  用户数: {df["user_id"].nunique():,}')
    print(f'  时间范围: {df["datetime"].min()} ~ {df["datetime"].max()}')
    return df


def safe_div(numerator, denominator):
    """安全除法，分母为0时返回0"""
    return (numerator / denominator.replace(0, float('nan')) * 100).round(2).fillna(0)


def funnel_overall(df):
    """【3.1】整体转化漏斗（用户级）"""
    print('\n' + '=' * 60)
    print('【3.1】整体转化漏斗（用户级）')
    print('=' * 60)

    user_behavior = df.groupby('user_id')['behavior_type'].apply(set)

    funnel_data = {}
    for bt in BEHAVIOR_ORDER:
        count = user_behavior.apply(lambda x: bt in x).sum()
        funnel_data[BEHAVIOR_MAP[bt]] = count

    funnel_df = pd.DataFrame(list(funnel_data.items()), columns=['行为', '用户数'])

    baseline = funnel_df.loc[funnel_df['行为'] == '浏览', '用户数'].values[0]
    funnel_df['占总用户比'] = (funnel_df['用户数'] / len(user_behavior) * 100).round(2)
    funnel_df['相对上一步转化率'] = (funnel_df['用户数'] / funnel_df['用户数'].shift(1) * 100).round(2)
    funnel_df['相对浏览转化率'] = (funnel_df['用户数'] / baseline * 100).round(2)

    print(f'\n  总用户数: {len(user_behavior):,}')
    print(f'  转化漏斗:')
    print(f'  {"行为":<8} {"用户数":<12} {"占总用户比":<12} {"相对上一步":<12} {"相对浏览":<12}')
    print(f'  {"-"*56}')
    for _, row in funnel_df.iterrows():
        print(f'  {row["行为"]:<8} {row["用户数"]:<12,} {row["占总用户比"]:<12} '
              f'{row["相对上一步转化率"] if pd.notna(row["相对上一步转化率"]) else "N/A":<12} '
              f'{row["相对浏览转化率"]:<12}')

    funnel_df.to_csv(f'{STATS_DIR}/funnel_overall.csv',
                      index=False, encoding='utf-8-sig')
    return funnel_df


def funnel_event_level(df):
    """【3.2】事件级转化率"""
    print('\n' + '=' * 60)
    print('【3.2】事件级转化（行为次数级）')
    print('=' * 60)

    event_counts = df['behavior_type'].value_counts()
    total_events = len(df)

    event_df = pd.DataFrame({
        '行为': event_counts.index.map(BEHAVIOR_MAP),
        '行为代码': event_counts.index,
        '事件数': event_counts.values,
        '占比': (event_counts.values / total_events * 100).round(2)
    }).reset_index(drop=True)

    event_df['sort_key'] = event_df['行为代码'].map(
        {b: i for i, b in enumerate(BEHAVIOR_ORDER)})
    event_df = event_df.sort_values('sort_key').drop('sort_key', axis=1)

    pv_count = event_df.loc[event_df['行为代码'] == 'pv', '事件数'].values[0]
    event_df['相对浏览转化率'] = (event_df['事件数'] / pv_count * 100).round(2)

    print(f'\n  总事件数: {total_events:,}')
    print(f'\n  {"行为":<8} {"事件数":<14} {"占比%":<10} {"相对浏览%":<10}')
    print(f'  {"-"*42}')
    for _, row in event_df.iterrows():
        print(f'  {row["行为"]:<8} {row["事件数"]:<14,} {row["占比"]:<10} {row["相对浏览转化率"]:<10}')

    event_df.to_csv(f'{STATS_DIR}/funnel_event_level.csv',
                     index=False, encoding='utf-8-sig')
    return event_df


def funnel_by_date(df):
    """【3.3】每日转化率趋势"""
    print('\n' + '=' * 60)
    print('【3.3】每日转化率趋势')
    print('=' * 60)

    daily_users = df.groupby(['date_str', 'behavior_type'])['user_id'].nunique().reset_index()
    daily_users.columns = ['日期', '行为类型', '用户数']

    pivot = daily_users.pivot(index='日期', columns='行为类型', values='用户数').fillna(0)

    for bt in BEHAVIOR_ORDER:
        if bt not in pivot.columns:
            pivot[bt] = 0

    pivot['浏览→收藏转化率'] = safe_div(pivot['fav'], pivot['pv'])
    pivot['浏览→加购转化率'] = safe_div(pivot['cart'], pivot['pv'])
    pivot['浏览→购买转化率'] = safe_div(pivot['buy'], pivot['pv'])
    pivot['加购→购买转化率'] = safe_div(pivot['buy'], pivot['cart'])
    pivot['收藏→购买转化率'] = safe_div(pivot['buy'], pivot['fav'])

    print('\n  每日转化率趋势:')
    print(pivot[[c for c in pivot.columns if '转化率' in c]].to_string())

    pivot.to_csv(f'{STATS_DIR}/funnel_daily.csv', encoding='utf-8-sig')
    return pivot


def user_path_analysis(df, top_n=10):
    """【3.4】用户行为路径分析"""
    print('\n' + '=' * 60)
    print('【3.4】用户行为路径分析')
    print('=' * 60)

    df_sorted = df.sort_values(['user_id', 'timestamp'])
    user_sequences = df_sorted.groupby('user_id')['behavior_type'].agg(list).reset_index()

    print('  分析行为转化路径...')

    pairs = []
    for seq in user_sequences['behavior_type']:
        for i in range(len(seq) - 1):
            pairs.append((seq[i], seq[i + 1]))

    pair_counts = Counter(pairs)
    total_pairs = sum(pair_counts.values())

    print(f'\n  TOP{top_n} 行为转化路径（相邻行为对）:')
    print(f'  {"来源":<10} {"→":<6} {"目标":<10} {"次数":<10} {"占比":<10}')
    print(f'  {"-"*46}')
    for (src, dst), cnt in pair_counts.most_common(top_n):
        print(f'  {BEHAVIOR_MAP.get(src, src):<10} {"→":<6} '
              f'{BEHAVIOR_MAP.get(dst, dst):<10} {cnt:<10,} {cnt/total_pairs*100:.2f}%')

    pair_df = pd.DataFrame([
        {'来源': BEHAVIOR_MAP.get(k[0], k[0]),
         '目标': BEHAVIOR_MAP.get(k[1], k[1]),
         '次数': v, '占比': v / total_pairs * 100}
        for k, v in pair_counts.most_common(20)
    ])
    pair_df.to_csv(f'{STATS_DIR}/behavior_transition_pairs.csv',
                    index=False, encoding='utf-8-sig')
    return pair_df


def purchase_path_analysis(df):
    """【3.5】购买路径分析"""
    print('\n' + '=' * 60)
    print('【3.5】购买前行为分析')
    print('=' * 60)

    df_sorted = df.sort_values(['user_id', 'timestamp'])

    pre_buy_behaviors = []
    for user_id, group in df_sorted.groupby('user_id'):
        behaviors = group['behavior_type'].values
        for i in range(1, len(behaviors)):
            if behaviors[i] == 'buy':
                pre_buy_behaviors.append(behaviors[i - 1])

    if pre_buy_behaviors:
        pre_buy_counter = Counter(pre_buy_behaviors)
        total_buys = len(pre_buy_behaviors)

        print(f'\n  购买事件总数: {total_buys:,}')
        print(f'  购买前一步行为分布:')
        print(f'  {"行为":<10} {"次数":<10} {"占比":<10}')
        print(f'  {"-"*30}')
        for bt in ['pv', 'cart', 'fav']:
            cnt = pre_buy_counter.get(bt, 0)
            print(f'  {BEHAVIOR_MAP[bt]:<10} {cnt:<10,} {cnt/total_buys*100:.2f}%')

        pre_buy_df = pd.DataFrame([
            {'行为': BEHAVIOR_MAP[k], '次数': v, '占比': v / total_buys * 100}
            for k, v in pre_buy_counter.most_common()
        ])
        pre_buy_df.to_csv(f'{STATS_DIR}/pre_purchase_behavior.csv',
                           index=False, encoding='utf-8-sig')

    # 购买前N步内的行为
    print('\n  购买前各步行为分布:')
    steps_data = {}
    for step_back in range(1, 6):
        step_behaviors = []
        for user_id, group in df_sorted.groupby('user_id'):
            behaviors = group['behavior_type'].values
            for i in range(step_back, len(behaviors)):
                if behaviors[i] == 'buy':
                    step_behaviors.append(behaviors[i - step_back])
        if step_behaviors:
            counter = Counter(step_behaviors)
            steps_data[f'前{step_back}步'] = {
                BEHAVIOR_MAP[k]: v for k, v in counter.most_common()
            }

    steps_df = pd.DataFrame(steps_data).fillna(0).astype(int)
    print(steps_df.to_string())
    steps_df.to_csv(f'{STATS_DIR}/purchase_steps_distribution.csv',
                     encoding='utf-8-sig')

    return pre_buy_behaviors


def conversion_by_category(df):
    """【3.6】各品类转化率"""
    print('\n' + '=' * 60)
    print('【3.6】各品类转化率分析')
    print('=' * 60)

    cat_stats = df.groupby('category_id').agg(
        浏览数=('behavior_type', lambda x: (x == 'pv').sum()),
        收藏数=('behavior_type', lambda x: (x == 'fav').sum()),
        加购数=('behavior_type', lambda x: (x == 'cart').sum()),
        购买数=('behavior_type', lambda x: (x == 'buy').sum()),
        独立用户=('user_id', 'nunique'),
    ).reset_index()

    cat_stats['浏览→购买转化率'] = (cat_stats['购买数'] / cat_stats['浏览数'] * 100).round(2)
    cat_stats['浏览→加购转化率'] = (cat_stats['加购数'] / cat_stats['浏览数'] * 100).round(2)
    cat_stats['加购→购买转化率'] = (cat_stats['购买数'] / cat_stats['加购数'] * 100).round(2)

    active_cats = cat_stats[cat_stats['浏览数'] >= 1000].copy()
    top_conversion_cats = active_cats.nlargest(10, '浏览→购买转化率')

    print(f'\n  转化率TOP10品类:')
    print(top_conversion_cats[['category_id', '浏览数', '购买数',
                                '浏览→购买转化率', '浏览→加购转化率']].to_string(index=False))

    top_conversion_cats.to_csv(f'{STATS_DIR}/category_conversion_top.csv',
                                index=False, encoding='utf-8-sig')
    active_cats.to_csv(f'{STATS_DIR}/category_conversion_all.csv',
                        index=False, encoding='utf-8-sig')
    return active_cats


if __name__ == '__main__':
    print('淘宝用户行为数据 - 转化漏斗分析')
    print('=' * 60)

    df = load_data()

    funnel_overall(df)
    funnel_event_level(df)
    funnel_by_date(df)
    user_path_analysis(df)
    purchase_path_analysis(df)
    conversion_by_category(df)

    print('\n✅ 转化漏斗分析完成！')
    print(f'  结果保存在 {STATS_DIR}/')
