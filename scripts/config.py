#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
淘宝用户行为数据分析 - 全局配置模块

集中管理所有路径、常量、映射关系。
所有脚本通过 `from config import ...` 引用，不再硬编码本地路径。
"""

import os

# ==================== 路径解析 ====================
# 无论从哪个目录运行，都基于脚本所在位置推算项目根目录
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SCRIPTS_DIR)

# ==================== 数据路径 ====================
# 用户需将 UserBehavior.csv 放入 data/raw/ 目录
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
RAW_DATA_PATH = os.path.join(RAW_DATA_DIR, 'UserBehavior.csv')

# ==================== 输出路径 ====================
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
STATS_DIR = os.path.join(OUTPUT_DIR, 'stats')
CHART_DIR = os.path.join(OUTPUT_DIR, 'charts')
PBI_DIR = os.path.join(OUTPUT_DIR, 'powerbi')
REPORT_DIR = os.path.join(OUTPUT_DIR, 'reports')

# 清洗后数据缓存
CLEANED_DATA = os.path.join(OUTPUT_DIR, 'cleaned_sample.parquet')

# SQL 分析输出
SQL_OUTPUT_DIR = STATS_DIR

# ==================== 数据列名 ====================
COLUMNS = ['user_id', 'item_id', 'category_id', 'behavior_type', 'timestamp']

# 行为类型映射
BEHAVIOR_MAP = {'pv': '浏览', 'fav': '收藏', 'cart': '加购', 'buy': '购买'}
BEHAVIOR_ORDER = ['pv', 'fav', 'cart', 'buy']
BEHAVIOR_LABELS = ['浏览', '收藏', '加购', '购买']
VALID_BEHAVIORS = {'pv', 'buy', 'cart', 'fav'}

# 颜色方案
COLORS = {'pv': '#5B9BD5', 'fav': '#FFC000', 'cart': '#ED7D31', 'buy': '#70AD47'}
COLORS_CN = {'浏览': '#5B9BD5', '收藏': '#FFC000', '加购': '#ED7D31', '购买': '#70AD47'}

# 星期标签
WEEKDAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
WEEKDAY_MAP = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}

# Parquet 读取列（清洗后数据不含 datetime/date 等派生列）
PARQUET_COLUMNS = ["user_id", "item_id", "category_id",
                   "behavior_type", "timestamp", "hour",
                   "weekday", "weekend"]

# 时间戳有效范围（2017年11月）
TS_MIN = 1508745600  # 2017-10-23
TS_MAX = 1514736000  # 2017-12-31

# 分块处理大小
CHUNK_SIZE = 500000

# 采样比例
SAMPLE_RATIO = 0.1


def ensure_dirs():
    """确保所有输出目录存在"""
    for d in [OUTPUT_DIR, STATS_DIR, CHART_DIR, PBI_DIR, REPORT_DIR, RAW_DATA_DIR]:
        os.makedirs(d, exist_ok=True)


def check_raw_data():
    """检查原始数据是否存在，返回路径或 None"""
    if os.path.exists(RAW_DATA_PATH):
        return RAW_DATA_PATH
    # 也检查 C:/Users/AUSUS/Desktop/ 下的旧路径（兼容）
    alt_path = os.path.expanduser('~/Desktop/UserBehavior.csv/UserBehavior.csv')
    if os.path.exists(alt_path):
        return alt_path
    return None
