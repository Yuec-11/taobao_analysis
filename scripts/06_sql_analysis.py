#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Part 补充: SQL 分析脚本（SQLite 兼容）
用于在飞浆环境或本地用 SQL 复现部分分析指标
"""

import os
import sys
import pandas as pd
import sqlite3
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    CLEANED_DATA, SQL_OUTPUT_DIR,
    PARQUET_COLUMNS, ensure_dirs
)

ensure_dirs()

# ==================== 建表 ====================
SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS user_behavior (
    user_id INTEGER,
    item_id INTEGER,
    category_id INTEGER,
    behavior_type TEXT,
    timestamp INTEGER,
    datetime TEXT,
    date TEXT,
    hour INTEGER,
    weekday INTEGER,
    weekday_name TEXT,
    weekend INTEGER
);
"""

# ==================== 分析SQL ====================

SQL_BEHAVIOR_COUNTS = """
SELECT
    behavior_type,
    COUNT(*) AS total_count,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT item_id) AS unique_items,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM user_behavior
GROUP BY behavior_type
ORDER BY total_count DESC;
"""

SQL_DAU = """
SELECT
    date,
    COUNT(DISTINCT user_id) AS dau,
    COUNT(*) AS total_actions
FROM user_behavior
GROUP BY date
ORDER BY date;
"""

SQL_HOURLY_ACTIVITY = """
SELECT
    hour,
    COUNT(*) AS total_actions,
    COUNT(DISTINCT user_id) AS unique_users
FROM user_behavior
GROUP BY hour
ORDER BY hour;
"""

SQL_WEEKEND_VS_WEEKDAY = """
SELECT
    CASE WHEN weekend = 1 THEN '周末' ELSE '工作日' END AS day_type,
    COUNT(*) AS total_actions,
    COUNT(DISTINCT user_id) AS unique_users,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT user_id), 2) AS actions_per_user
FROM user_behavior
GROUP BY day_type;
"""

SQL_CONVERSION_FUNNEL = """
SELECT '浏览' AS stage, COUNT(DISTINCT user_id) AS user_count
FROM user_behavior WHERE behavior_type = 'pv'
UNION ALL
SELECT '收藏' AS stage, COUNT(DISTINCT user_id) AS user_count
FROM user_behavior WHERE behavior_type = 'fav'
UNION ALL
SELECT '加购' AS stage, COUNT(DISTINCT user_id) AS user_count
FROM user_behavior WHERE behavior_type = 'cart'
UNION ALL
SELECT '购买' AS stage, COUNT(DISTINCT user_id) AS user_count
FROM user_behavior WHERE behavior_type = 'buy';
"""

SQL_USER_ACTIVITY_LEVEL = """
SELECT
    CASE
        WHEN actions >= 500 THEN 'S级: 超高活跃'
        WHEN actions >= 200 THEN 'A级: 高活跃'
        WHEN actions >= 100 THEN 'B级: 中活跃'
        WHEN actions >= 30 THEN 'C级: 低活跃'
        ELSE 'D级: 沉睡用户'
    END AS activity_level,
    COUNT(*) AS user_count,
    ROUND(AVG(actions), 2) AS avg_actions,
    ROUND(AVG(active_days), 2) AS avg_active_days
FROM (
    SELECT user_id, COUNT(*) AS actions, COUNT(DISTINCT date) AS active_days
    FROM user_behavior GROUP BY user_id
) t
GROUP BY activity_level
ORDER BY activity_level;
"""

SQL_DAILY_CONVERSION = """
SELECT
    date,
    COUNT(DISTINCT CASE WHEN behavior_type = 'pv' THEN user_id END) AS pv_users,
    COUNT(DISTINCT CASE WHEN behavior_type = 'buy' THEN user_id END) AS buy_users,
    ROUND(COUNT(DISTINCT CASE WHEN behavior_type = 'buy' THEN user_id END) * 100.0 /
          NULLIF(COUNT(DISTINCT CASE WHEN behavior_type = 'pv' THEN user_id END), 0), 2) AS pv_to_buy_rate
FROM user_behavior
GROUP BY date
ORDER BY date;
"""

SQL_TOP_USERS = """
SELECT
    user_id,
    COUNT(*) AS total_actions,
    SUM(CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END) AS pv_count,
    SUM(CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END) AS fav_count,
    SUM(CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END) AS cart_count,
    SUM(CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END) AS buy_count,
    COUNT(DISTINCT date) AS active_days,
    COUNT(DISTINCT category_id) AS categories_viewed
FROM user_behavior
GROUP BY user_id
ORDER BY total_actions DESC
LIMIT 10;
"""

SQL_PRE_BUY = """
SELECT t1.user_id, t1.behavior_type AS pre_buy_behavior, COUNT(*) AS count
FROM user_behavior t1
INNER JOIN user_behavior t2
    ON t1.user_id = t2.user_id
    AND t2.behavior_type = 'buy'
    AND t2.timestamp > t1.timestamp
    AND t2.timestamp - t1.timestamp < 3600
WHERE t1.behavior_type != 'buy'
GROUP BY t1.user_id, t1.behavior_type
ORDER BY count DESC;
"""

SQL_DAILY_NEW_USER = """
SELECT
    first_date,
    COUNT(*) AS new_users,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM (
    SELECT user_id, MIN(date) AS first_date
    FROM user_behavior GROUP BY user_id
) t
GROUP BY first_date
ORDER BY first_date;
"""


def execute_sql_analysis():
    """在 SQLite 中复现分析"""
    print('=' * 60)
    print('飞浆环境 SQL 分析（SQLite兼容）')
    print('=' * 60)

    if not os.path.exists(CLEANED_DATA):
        print(f'⚠ 文件不存在: {CLEANED_DATA}')
        print('请先运行 01_data_cleaning.py')
        return

    df = pd.read_parquet(CLEANED_DATA, engine="fastparquet",
                          columns=["user_id", "item_id", "category_id",
                                   "behavior_type", "timestamp"])
    print(f'加载数据: {len(df):,} 行')

    # 限制 SQLite 分析的行数
    if len(df) > 200000:
        df_sql = df.sample(n=200000, random_state=42)
        print(f'SQL分析采样: {len(df_sql):,} 行')
    else:
        df_sql = df

    # 添加派生列（SQL查询需要）
    df_sql['datetime'] = pd.to_datetime(df_sql['timestamp'], unit='s')
    df_sql['date'] = df_sql['datetime'].dt.strftime('%Y-%m-%d')
    df_sql['hour'] = df_sql['datetime'].dt.hour
    df_sql['weekday'] = df_sql['datetime'].dt.weekday
    df_sql['weekend'] = df_sql['weekday'].isin([5, 6]).astype(int)

    # 创建内存数据库
    conn = sqlite3.connect(':memory:')
    df_sql[['user_id', 'item_id', 'category_id', 'behavior_type', 'timestamp',
            'date', 'hour', 'weekday', 'weekend']].to_sql(
        'user_behavior', conn, index=False, if_exists='replace')

    print(f'\nSQL分析结果:')

    queries = [
        ('各行为类型统计', SQL_BEHAVIOR_COUNTS),
        ('每日活跃用户(DAU)', SQL_DAU),
        ('每小时活跃度', SQL_HOURLY_ACTIVITY),
        ('工作日vs周末', SQL_WEEKEND_VS_WEEKDAY),
        ('转化漏斗', SQL_CONVERSION_FUNNEL),
        ('用户活跃分层', SQL_USER_ACTIVITY_LEVEL),
        ('每日转化率', SQL_DAILY_CONVERSION),
        ('TOP10用户', SQL_TOP_USERS),
        ('每日新用户', SQL_DAILY_NEW_USER),
    ]

    for name, query in queries:
        print(f'\n  --- {name} ---')
        try:
            result = pd.read_sql_query(query, conn)
            print(result.to_string(index=False))
            safe_name = name.replace(' ', '_').replace('(', '').replace(')', '')
            result.to_csv(f'{SQL_OUTPUT_DIR}/sql_{safe_name}.csv',
                          index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f'  Error: {e}')

    conn.close()
    print(f'\n✅ SQL分析完成，结果保存在 {SQL_OUTPUT_DIR}/')


if __name__ == '__main__':
    execute_sql_analysis()
