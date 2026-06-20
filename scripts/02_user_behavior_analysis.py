#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Part 2: 用户行为分析
- 用户总量、各类行为次数统计
- 不同时间段活跃度分析（小时/星期/日期）
- 用户活跃度分层
- TOP商品/品类分析
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
    CLEANED_DATA, STATS_DIR, CHART_DIR,
    PARQUET_COLUMNS, BEHAVIOR_MAP, WEEKDAY_MAP, ensure_dirs
)

ensure_dirs()


def load_data():
    """加载清洗后的数据"""
    print('加载清洗后数据...')
    df = pd.read_parquet(CLEANED_DATA, engine="fastparquet", columns=PARQUET_COLUMNS)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df['date'] = df['datetime'].dt.date.astype(str)
    df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')
    print(f'  行数: {len(df):,}')
    print(f'  用户数: {df["user_id"].nunique():,}')
    print(f'  时间范围: {df["datetime"].min()} ~ {df["datetime"].max()}')
    return df


def overall_stats(df):
    """总体概览统计"""
    print('\n' + '=' * 60)
    print('【2.1】总体概览')
    print('=' * 60)

    total_users = df['user_id'].nunique()
    total_items = df['item_id'].nunique()
    total_cats = df['category_id'].nunique()
    total_records = len(df)
    total_days = df['date'].nunique()

    # 各行为统计
    behavior_counts = df.groupby('behavior_type').agg(
        总次数=('user_id', 'count'),
        独立用户=('user_id', 'nunique')
    ).reset_index()
    behavior_counts['行为'] = behavior_counts['behavior_type'].map(BEHAVIOR_MAP)
    behavior_counts['占比'] = (behavior_counts['总次数'] / total_records * 100).round(2)

    stats = {
        '总记录数': int(total_records),
        '独立用户': int(total_users),
        '独立商品': int(total_items),
        '独立品类': int(total_cats),
        '覆盖天数': int(total_days),
    }

    print(f'  总记录数: {total_records:,}')
    print(f'  独立用户: {total_users:,}')
    print(f'  独立商品: {total_items:,}')
    print(f'  独立品类: {total_cats:,}')
    print(f'  覆盖天数: {total_days}')
    print(f'\n  各行为统计:')
    print(behavior_counts[['行为', '总次数', '独立用户', '占比']].to_string(index=False))

    pd.DataFrame([stats]).to_csv(f'{STATS_DIR}/overall_stats.csv',
                                  index=False, encoding='utf-8-sig')
    behavior_counts.to_csv(f'{STATS_DIR}/behavior_counts.csv',
                            index=False, encoding='utf-8-sig')

    return stats, behavior_counts


def time_analysis(df):
    """时间维度分析"""
    print('\n' + '=' * 60)
    print('【2.2】时间维度分析')
    print('=' * 60)

    # === 2.2.1 每小时活跃度 ===
    hourly = df.groupby(['hour', 'behavior_type']).size().unstack(fill_value=0)
    hourly['总计'] = hourly.sum(axis=1)

    print('\n  每小时行为分布（Top 5小时）:')
    print(hourly.sort_values('总计', ascending=False).head(5).to_string())

    hourly.to_csv(f'{STATS_DIR}/hourly_behavior.csv', encoding='utf-8-sig')

    # === 2.2.2 星期活跃度 ===
    weekday = df.groupby(['weekday', 'behavior_type']).size().unstack(fill_value=0)
    weekday['总计'] = weekday.sum(axis=1)
    weekday.index = weekday.index.map(WEEKDAY_MAP)

    print('\n  星期行为分布:')
    print(weekday.to_string())

    weekday.to_csv(f'{STATS_DIR}/weekday_behavior.csv', encoding='utf-8-sig')

    # === 2.2.3 每日活跃度 ===
    daily = df.groupby(['date_str', 'behavior_type']).size().unstack(fill_value=0)
    daily['总计'] = daily.sum(axis=1)

    print(f'\n  每日行为分布（首5天）:')
    print(daily.head().to_string())

    daily.to_csv(f'{STATS_DIR}/daily_behavior.csv', encoding='utf-8-sig')

    # === 2.2.4 周末 vs 工作日 ===
    weekend = df.groupby(['weekend', 'behavior_type']).size().unstack(fill_value=0)
    weekend['总计'] = weekend.sum(axis=1)
    weekend.index = ['工作日', '周末']

    print('\n  工作日 vs 周末:')
    print(weekend.to_string())

    # 人均行为
    user_daily = df.groupby(['user_id', 'date_str', 'behavior_type']).size().reset_index(name='count')
    per_user_per_day = user_daily.groupby('behavior_type')['count'].mean()

    print('\n  人均每日行为次数:')
    for bt, val in per_user_per_day.items():
        print(f'    {BEHAVIOR_MAP.get(bt, bt)}: {val:.2f} 次')

    per_user_per_day.to_csv(f'{STATS_DIR}/per_user_daily.csv', encoding='utf-8-sig')

    # === 2.2.5 活跃时间段聚类 ===
    hour_active = df.groupby('hour').size()
    peak_hours = hour_active.nlargest(5)
    low_hours = hour_active.nsmallest(5)

    print(f'\n  高峰时段: {list(peak_hours.index)}  (总行为数 {peak_hours.sum():,})')
    print(f'  低谷时段: {list(low_hours.index)}  (总行为数 {low_hours.sum():,})')

    return hourly, weekday, daily


def user_activity_level(df):
    """用户活跃度分层"""
    print('\n' + '=' * 60)
    print('【2.3】用户活跃度分层')
    print('=' * 60)

    user_activity = df.groupby('user_id').agg(
        总行为数=('behavior_type', 'count'),
        浏览数=('behavior_type', lambda x: (x == 'pv').sum()),
        收藏数=('behavior_type', lambda x: (x == 'fav').sum()),
        加购数=('behavior_type', lambda x: (x == 'cart').sum()),
        购买数=('behavior_type', lambda x: (x == 'buy').sum()),
        活跃天数=('date', 'nunique'),
    ).reset_index()

    # 独立计算购买天数
    buy_days = df[df['behavior_type'] == 'buy'].groupby('user_id')['date'].nunique().reset_index()
    buy_days.columns = ['user_id', '购买天数']
    user_activity = user_activity.merge(buy_days, on='user_id', how='left')
    user_activity['购买天数'] = user_activity['购买天数'].fillna(0).astype(int)

    def classify_activity(total, days):
        if total >= 500:
            return 'S级: 超高活跃'
        elif total >= 200:
            return 'A级: 高活跃'
        elif total >= 100:
            return 'B级: 中活跃'
        elif total >= 30:
            return 'C级: 低活跃'
        else:
            return 'D级: 沉睡用户'

    user_activity['活跃等级'] = user_activity.apply(
        lambda x: classify_activity(x['总行为数'], x['活跃天数']), axis=1)

    level_stats = user_activity['活跃等级'].value_counts().reset_index()
    level_stats.columns = ['活跃等级', '用户数']
    level_stats['占比'] = (level_stats['用户数'] / level_stats['用户数'].sum() * 100).round(2)

    print('\n  用户活跃度分层:')
    print(level_stats.to_string(index=False))

    level_behavior = user_activity.groupby('活跃等级').agg(
        用户数=('user_id', 'count'),
        人均行为数=('总行为数', 'mean'),
        人均浏览=('浏览数', 'mean'),
        人均收藏=('收藏数', 'mean'),
        人均加购=('加购数', 'mean'),
        人均购买=('购买数', 'mean'),
        人均活跃天数=('活跃天数', 'mean')
    ).round(2)

    print('\n  各层级人均行为:')
    print(level_behavior.to_string())

    level_stats.to_csv(f'{STATS_DIR}/user_activity_level.csv',
                        index=False, encoding='utf-8-sig')
    level_behavior.to_csv(f'{STATS_DIR}/level_behavior_avg.csv',
                           encoding='utf-8-sig')
    user_activity.to_csv(f'{STATS_DIR}/user_activity_detail.csv',
                          index=False, encoding='utf-8-sig')

    return user_activity, level_stats


def top_items_analysis(df, top_n=20):
    """TOP商品/品类分析"""
    print('\n' + '=' * 60)
    print(f'【2.4】TOP{top_n} 商品 & 品类分析')
    print('=' * 60)

    item_pop = df.groupby(['item_id', 'behavior_type']).size().unstack(fill_value=0)
    item_pop['总计'] = item_pop.sum(axis=1)
    top_items = item_pop.nlargest(top_n, '总计')

    print(f'\n  TOP{top_n} 热门商品:')
    print(top_items.to_string())
    top_items.to_csv(f'{STATS_DIR}/top_items.csv', encoding='utf-8-sig')

    cat_pop = df.groupby(['category_id', 'behavior_type']).size().unstack(fill_value=0)
    cat_pop['总计'] = cat_pop.sum(axis=1)
    top_cats = cat_pop.nlargest(top_n, '总计')

    print(f'\n  TOP{top_n} 热门品类:')
    print(top_cats.to_string())
    top_cats.to_csv(f'{STATS_DIR}/top_categories.csv', encoding='utf-8-sig')

    # 购买率最高的商品
    item_buy = df[df['behavior_type'] == 'buy'].groupby('item_id').size()
    item_pv = df[df['behavior_type'] == 'pv'].groupby('item_id').size()
    item_conversion = pd.DataFrame({'pv': item_pv, 'buy': item_buy}).fillna(0)
    item_conversion['转化率'] = (item_conversion['buy'] / item_conversion['pv'] * 100).round(2)
    item_conversion = item_conversion[item_conversion['pv'] >= 100]
    top_conversion = item_conversion.nlargest(10, '转化率')

    print(f'\n  转化率最高的10个商品:')
    print(top_conversion.to_string())
    top_conversion.to_csv(f'{STATS_DIR}/top_conversion_items.csv', encoding='utf-8-sig')

    return top_items, top_cats


def new_vs_returning(df):
    """新老用户分析"""
    print('\n' + '=' * 60)
    print('【2.5】新老用户分析')
    print('=' * 60)

    user_first = df.groupby('user_id')['date'].min().reset_index()
    user_first.columns = ['user_id', 'first_date']
    df_user = df.merge(user_first, on='user_id')
    df_user['is_new'] = (df_user['date'] == df_user['first_date']).astype(int)

    new_users = df_user[df_user['is_new'] == 1].groupby('date_str').agg(
        新用户数=('user_id', 'nunique')
    ).reset_index()

    print(f'\n  每日新用户数:')
    print(new_users.to_string(index=False))

    new_users.to_csv(f'{STATS_DIR}/daily_new_users.csv',
                      index=False, encoding='utf-8-sig')

    return new_users


def user_behavior_path(df):
    """用户行为路径简化分析"""
    print('\n' + '=' * 60)
    print('【2.6】用户行为路径概要')
    print('=' * 60)

    user_behavior_types = df.groupby('user_id')['behavior_type'].apply(set)
    behavior_count = user_behavior_types.apply(len).value_counts().sort_index()

    print('\n  用户涉及行为种类分布:')
    for k, v in behavior_count.items():
        print(f'    {int(k)}种行为: {v:,} 用户 ({v/len(user_behavior_types)*100:.1f}%)')

    has_buy = user_behavior_types.apply(lambda x: 'buy' in x)
    has_pv = user_behavior_types.apply(lambda x: 'pv' in x)

    print(f'\n  有浏览行为的用户: {has_pv.sum():,} ({has_pv.mean()*100:.1f}%)')
    print(f'  有购买行为的用户: {has_buy.sum():,} ({has_buy.mean()*100:.1f}%)')
    print(f'  既有浏览又有购买: {(has_pv & has_buy).sum():,}')

    return behavior_count


if __name__ == '__main__':
    print('淘宝用户行为数据 - 用户行为分析')
    print('=' * 60)

    df = load_data()

    overall_stats(df)
    time_analysis(df)
    user_activity_level(df)
    top_items_analysis(df)
    new_vs_returning(df)
    user_behavior_path(df)

    print('\n✅ 用户行为分析完成！')
    print(f'  结果保存在 {STATS_DIR}/')
