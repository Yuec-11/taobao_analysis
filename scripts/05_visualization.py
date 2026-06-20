#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Part 5: 数据可视化
- 生成所有分析结果图表
- 输出为 PNG 图片，供 Power BI 看板使用
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互后端
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.font_manager import FontProperties
import warnings
import sys
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import (
    STATS_DIR, CHART_DIR,
    BEHAVIOR_ORDER, BEHAVIOR_LABELS, COLORS, COLORS_CN,
    WEEKDAY_LABELS, ensure_dirs
)

ensure_dirs()

# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.figsize'] = (12, 6)


def load_stats(filename):
    """加载统计结果CSV"""
    path = os.path.join(STATS_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    print(f'  ⚠ 文件不存在: {filename}')
    return None


# ==================== 图表 1: 行为分布柱状图 ====================
def chart_behavior_distribution():
    """图1: 各类行为分布"""
    print('\n  生成图1: 行为分布柱状图...')

    df = load_stats('behavior_counts.csv')
    if df is None:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 左图: 总次数
    colors = [COLORS.get(r['behavior_type'], '#999')
              for _, r in df.iterrows()]
    bars1 = ax1.bar(df['行为'], df['总次数'], color=colors, edgecolor='white', linewidth=0.5)

    ax1.set_title('各行为总次数分布', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel('次数')
    ax1.ticklabel_format(style='scientific', axis='y', scilimits=(4, 4))

    # 在柱子上标注数值和占比
    total = df['总次数'].sum()
    for bar, val, pct in zip(bars1, df['总次数'], df['占比']):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f'{val/1e6:.1f}M\n({pct}%)',
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    # 右图: 独立用户数
    bars2 = ax2.bar(df['行为'], df['独立用户'], color=colors, edgecolor='white', linewidth=0.5)
    ax2.set_title('各行为独立用户数分布', fontsize=14, fontweight='bold', pad=15)
    ax2.set_ylabel('用户数')
    ax2.ticklabel_format(style='scientific', axis='y', scilimits=(4, 4))

    for bar, val in zip(bars2, df['独立用户']):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f'{val/1e4:.1f}万',
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/01_behavior_distribution.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 2: 每小时活跃度热力图 ====================
def chart_hourly_activity():
    """图2: 24小时行为分布"""
    print('  生成图2: 每小时活跃度折线图...')

    df = load_stats('hourly_behavior.csv')
    if df is None:
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    for bt in BEHAVIOR_ORDER:
        if bt in df.columns:
            label = BEHAVIOR_LABELS[BEHAVIOR_ORDER.index(bt)]
            ax.plot(df.index, df[bt], label=label,
                    color=COLORS[bt], linewidth=2.5, marker='o', markersize=4)

    ax.set_title('24小时用户行为活跃度分布', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('小时', fontsize=12)
    ax.set_ylabel('行为次数', fontsize=12)
    ax.set_xticks(range(0, 24))
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)

    # 标注高峰
    total_col = '总计' if '总计' in df.columns else BEHAVIOR_ORDER[0]
    peak_hour = df[total_col].idxmax()
    peak_val = df.loc[peak_hour, total_col]
    ax.annotate(f'高峰期: {peak_hour}:00\n({peak_val/1e6:.1f}M)',
                xy=(peak_hour, peak_val),
                xytext=(peak_hour + 2, peak_val),
                fontsize=11,
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/02_hourly_activity.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 3: 星期活跃度 ====================
def chart_weekly_activity():
    """图3: 星期行为分布"""
    print('  生成图3: 星期活跃度...')

    df = load_stats('weekday_behavior.csv')
    if df is None:
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    x = range(len(df))
    width = 0.2

    for i, bt in enumerate(BEHAVIOR_ORDER):
        if bt in df.columns:
            offset = (i - 1.5) * width
            bars = ax.bar([xi + offset for xi in x], df[bt], width,
                          label=BEHAVIOR_LABELS[i], color=COLORS[bt], edgecolor='white')

    ax.set_title('一周内各天用户行为分布', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('星期', fontsize=12)
    ax.set_ylabel('行为次数', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(WEEKDAY_LABELS, fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/03_weekly_activity.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 4: 每日趋势 ====================
def chart_daily_trend():
    """图4: 每日行为趋势"""
    print('  生成图4: 每日行为趋势...')

    df = load_stats('daily_behavior.csv')
    if df is None:
        return

    # 确保第一列是日期索引
    if df.index.dtype == 'int64' and 'date_str' in df.columns:
        df = df.set_index('date_str')
    elif df.index.dtype == 'int64':
        # 尝试第一列作为日期
        first_col = df.columns[0]
        df = df.set_index(first_col)

    fig, ax = plt.subplots(figsize=(14, 6))

    for bt in BEHAVIOR_ORDER:
        if bt in df.columns:
            ax.plot(range(len(df)), df[bt], label=BEHAVIOR_LABELS[BEHAVIOR_ORDER.index(bt)],
                    color=COLORS[bt], linewidth=2.5, marker='o', markersize=5)

    ax.set_title('每日用户行为变化趋势', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('行为次数', fontsize=12)

    # 日期标签
    date_labels = [d[-5:] for d in df.index[:len(df)]]  # 取 MM-DD
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(date_labels, rotation=30, fontsize=9)

    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/04_daily_trend.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 5: 转化漏斗图 ====================
def chart_conversion_funnel():
    """图5: 转化漏斗"""
    print('  生成图5: 转化漏斗图...')

    df = load_stats('funnel_overall.csv')
    if df is None:
        return

    fig, ax = plt.subplots(figsize=(10, 7))

    values = df['用户数'].values
    labels = df['行为'].values
    rates = df['相对上一步转化率'].values

    # 漏斗图
    max_val = max(values)
    colors_funnel = ['#5B9BD5', '#FFC000', '#ED7D31', '#70AD47']

    for i, (val, label, rate) in enumerate(zip(values[::-1], labels[::-1], rates[::-1])):
        width = val / max_val * 0.8
        left = (1 - width) / 2
        rect = ax.barh(i, width, height=0.5, left=left,
                       color=colors_funnel[len(values) - 1 - i],
                       edgecolor='white', linewidth=2)

        # 标签
        pct = df.iloc[len(values) - 1 - i]['占总用户比']
        rate_text = f' ({rate:.1f}%)' if not pd.isna(rate) else ''
        ax.text(0.5, i,
                f'{labels[::-1][i]}\n{val:,} 用户\n占比{pct:.1f}%{rate_text}',
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')

    ax.set_yticks(range(len(values)))
    ax.set_yticklabels([])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title('用户行为转化漏斗', fontsize=16, fontweight='bold', pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/05_conversion_funnel.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 6: 每日转化率趋势 ====================
def chart_daily_conversion():
    """图6: 每日转化率趋势"""
    print('  生成图6: 每日转化率趋势...')

    df = load_stats('funnel_daily.csv')
    if df is None:
        return

    # 确保日期作为索引
    if df.index.dtype == 'int64':
        first_col = df.columns[0]
        df = df.set_index(first_col)

    conv_cols = [c for c in df.columns if '转化率' in c]
    if not conv_cols:
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    colors_conv = ['#5B9BD5', '#FFC000', '#70AD47', '#ED7D31', '#FF6699']

    for i, col in enumerate(conv_cols):
        if col in df.columns:
            ax.plot(range(len(df)), df[col], label=col,
                    color=colors_conv[i % len(colors_conv)],
                    linewidth=2, marker='o', markersize=4)

    date_labels = [d[-5:] for d in df.index[:len(df)]]
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(date_labels, rotation=30, fontsize=9)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('转化率 (%)', fontsize=12)
    ax.set_title('每日各环节转化率趋势', fontsize=14, fontweight='bold', pad=15)
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/06_daily_conversion_trend.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 7: 用户活跃分层 ====================
def chart_user_segments():
    """图7: 用户活跃分层"""
    print('  生成图7: 用户活跃分层...')

    df = load_stats('user_activity_level.csv')
    if df is None:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 左: 饼图
    colors_levels = ['#FF4444', '#FF8800', '#FFBB33', '#66BB6A', '#42A5F5']
    wedges, texts, autotexts = ax1.pie(
        df['用户数'], labels=df['活跃等级'], autopct='%1.1f%%',
        colors=colors_levels[:len(df)], startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight('bold')
    ax1.set_title('用户活跃度分层占比', fontsize=14, fontweight='bold', pad=15)

    # 右: 条形图
    ax2.barh(df['活跃等级'], df['用户数'], color=colors_levels[:len(df)],
             edgecolor='white', linewidth=0.5)
    ax2.set_xlabel('用户数', fontsize=12)
    ax2.set_title('各层级用户数', fontsize=14, fontweight='bold', pad=15)

    for i, v in enumerate(df['用户数']):
        ax2.text(v + max(df['用户数']) * 0.01, i, f'{v:,}',
                 va='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/07_user_activity_segments.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 8: 用户价值分群 ====================
def chart_rfm_segments():
    """图8: RFM用户价值分群"""
    print('  生成图8: RFM用户分群...')

    df = load_stats('user_segments.csv')
    if df is None:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    df_sorted = df.sort_values('用户数', ascending=True)

    colors_rfm = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(df_sorted)))
    colors_rfm = [colors_rfm[i] for i in range(len(df_sorted))]

    bars = ax.barh(df_sorted['用户分群'], df_sorted['用户数'],
                   color=colors_rfm, edgecolor='white', linewidth=0.5)

    ax.set_xlabel('用户数', fontsize=12)
    ax.set_title('基于RFM的用户价值分群', fontsize=14, fontweight='bold', pad=15)

    for bar, val, pct in zip(bars, df_sorted['用户数'], df_sorted['占比']):
        ax.text(bar.get_width() + max(df_sorted['用户数']) * 0.005,
                bar.get_y() + bar.get_height() / 2,
                f'{val:,} ({pct}%)',
                va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/08_rfm_segments.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 9: 行为转移矩阵热力图 ====================
def chart_transition_heatmap():
    """图9: 行为转移热力图"""
    print('  生成图9: 行为路径转移热力图...')

    df = load_stats('behavior_transition_pairs.csv')
    if df is None:
        return

    # 构建转移矩阵
    behaviors = ['浏览', '收藏', '加购', '购买']
    matrix = np.zeros((4, 4))

    for _, row in df.iterrows():
        if row['来源'] in behaviors and row['目标'] in behaviors:
            i = behaviors.index(row['来源'])
            j = behaviors.index(row['目标'])
            matrix[i][j] = row['占比']

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0)

    # 标注数值
    for i in range(4):
        for j in range(4):
            text = ax.text(j, i, f'{matrix[i, j]:.1f}%',
                           ha='center', va='center', fontsize=13,
                           fontweight='bold',
                           color='white' if matrix[i, j] > 30 else 'black')

    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels(behaviors, fontsize=12)
    ax.set_yticklabels(behaviors, fontsize=12)
    ax.set_xlabel('目标行为', fontsize=13, fontweight='bold')
    ax.set_ylabel('来源行为', fontsize=13, fontweight='bold')
    ax.set_title('用户行为转移概率矩阵', fontsize=14, fontweight='bold', pad=15)

    plt.colorbar(im, ax=ax, shrink=0.8, label='转移占比 (%)')
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/09_transition_heatmap.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 10: 购买前行为分布 ====================
def chart_pre_purchase():
    """图10: 购买前行为"""
    print('  生成图10: 购买前行为分布...')

    df = load_stats('pre_purchase_behavior.csv')
    if df is None:
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    colors_pre = ['#5B9BD5', '#ED7D31', '#FFC000']

    bars = ax.bar(df['行为'], df['次数'],
                  color=colors_pre[:len(df)], edgecolor='white', linewidth=1)
    ax.set_title('购买前一步行为分布', fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel('次数', fontsize=12)

    total = df['次数'].sum()
    for bar, val in zip(bars, df['次数']):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f'{val:,}\n({val/total*100:.1f}%)',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/10_pre_purchase_behavior.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 11: 高价值用户对比 ====================
def chart_high_value_comparison():
    """图11: 高价值用户 vs 其他"""
    print('  生成图11: 高价值用户对比雷达图...')

    df = load_stats('high_value_comparison.csv')
    if df is None:
        return

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

    categories = df['指标'].values
    high_vals = df['高价值用户'].values.astype(float)
    other_vals = df['其他用户'].values.astype(float)

    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    high_vals = np.concatenate([high_vals, [high_vals[0]]])
    other_vals = np.concatenate([other_vals, [other_vals[0]]])

    ax.plot(angles, high_vals, 'o-', linewidth=2, label='高价值用户', color='#FF6B35')
    ax.fill(angles, high_vals, alpha=0.1, color='#FF6B35')
    ax.plot(angles, other_vals, 'o-', linewidth=2, label='其他用户', color='#5B9BD5')
    ax.fill(angles, other_vals, alpha=0.1, color='#5B9BD5')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_title('高价值用户 vs 其他用户特征对比', fontsize=14, fontweight='bold', pad=25)
    ax.legend(fontsize=12, loc='upper right', bbox_to_anchor=(1.3, 1.1))

    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/11_high_value_radar.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 12: 综合看板图 ====================
def chart_dashboard():
    """图12: 综合看板组合图"""
    print('  生成图12: 综合数据看板...')

    overall = load_stats('overall_stats.csv')
    behavior = load_stats('behavior_counts.csv')
    funnel = load_stats('funnel_overall.csv')

    if overall is None:
        return

    fig = plt.figure(figsize=(20, 12))

    # 顶部: KPI卡片
    stats = overall.iloc[0] if len(overall) > 0 else {}
    kpi_data = [
        ('总用户', f'{int(stats.get("独立用户", 0)):,}', '#5B9BD5'),
        ('总记录数', f'{int(stats.get("总记录数", 0)):,}', '#70AD47'),
        ('总商品', f'{int(stats.get("独立商品", 0)):,}', '#FFC000'),
        ('总品类', f'{int(stats.get("独立品类", 0)):,}', '#ED7D31'),
        ('覆盖天数', f'{int(stats.get("覆盖天数", 0))}天', '#FF6699'),
    ]

    for i, (label, value, color) in enumerate(kpi_data):
        ax = fig.add_axes([0.04 + i * 0.19, 0.88, 0.17, 0.08])
        ax.set_facecolor(color)
        ax.text(0.5, 0.7, value, ha='center', va='center',
                fontsize=22, fontweight='bold', color='white', transform=ax.transAxes)
        ax.text(0.5, 0.25, label, ha='center', va='center',
                fontsize=11, color='white', alpha=0.9, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    # 行为分布图
    if behavior is not None:
        ax1 = fig.add_axes([0.04, 0.52, 0.28, 0.32])
        colors = ['#5B9BD5', '#FFC000', '#ED7D31', '#70AD47']
        bars = ax1.bar(behavior['行为'], behavior['总次数'], color=colors, edgecolor='white')
        ax1.set_title('各行为总次数', fontsize=12, fontweight='bold')
        ax1.ticklabel_format(style='scientific', axis='y', scilimits=(4, 4))
        for bar, val in zip(bars, behavior['总次数']):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f'{val/1e6:.1f}M', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 漏斗图
    if funnel is not None:
        ax2 = fig.add_axes([0.38, 0.52, 0.28, 0.32])
        values = funnel['用户数'].values
        labels = funnel['行为'].values
        max_val = max(values)
        funnel_colors = ['#5B9BD5', '#FFC000', '#ED7D31', '#70AD47']
        for i, (val, label) in enumerate(zip(values[::-1], labels[::-1])):
            width = val / max_val * 0.8
            left = (1 - width) / 2
            rect = ax2.barh(i, width, height=0.5, left=left,
                           color=funnel_colors[len(values) - 1 - i], edgecolor='white')
            ax2.text(0.5, i, f'{label}\n{val:,}', ha='center', va='center',
                    fontsize=10, fontweight='bold', color='white')
        ax2.set_title('转化漏斗', fontsize=12, fontweight='bold')
        ax2.set_xlim(0, 1)
        ax2.set_xticks([])
        ax2.set_yticks([])
        for spine in ax2.spines.values():
            spine.set_visible(False)

    # 购买前行为
    pre_buy = load_stats('pre_purchase_behavior.csv')
    if pre_buy is not None:
        ax3 = fig.add_axes([0.72, 0.52, 0.24, 0.32])
        colors_pre = ['#5B9BD5', '#ED7D31', '#FFC000']
        bars = ax3.bar(pre_buy['行为'], pre_buy['次数'], color=colors_pre[:len(pre_buy)],
                       edgecolor='white')
        ax3.set_title('购买前一步行为', fontsize=12, fontweight='bold')
        total = pre_buy['次数'].sum()
        for bar, val in zip(bars, pre_buy['次数']):
            ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f'{val/total*100:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 转化率折线图
    daily_conv = load_stats('funnel_daily.csv')
    if daily_conv is not None:
        if daily_conv.index.dtype == 'int64':
            first_col = daily_conv.columns[0]
            daily_conv = daily_conv.set_index(first_col)
        ax4 = fig.add_axes([0.04, 0.08, 0.44, 0.38])
        conv_cols = [c for c in daily_conv.columns if '转化率' in c]
        colors_conv = ['#5B9BD5', '#FFC000', '#70AD47', '#ED7D31', '#FF6699']
        for i, col in enumerate(conv_cols[:4]):
            if col in daily_conv.columns:
                ax4.plot(range(len(daily_conv)), daily_conv[col],
                        label=col, color=colors_conv[i], linewidth=2, marker='o', markersize=3)
        ax4.set_title('每日转化率趋势', fontsize=12, fontweight='bold')
        date_labels = [d[-5:] for d in daily_conv.index[:len(daily_conv)]]
        ax4.set_xticks(range(len(daily_conv)))
        ax4.set_xticklabels(date_labels, rotation=30, fontsize=8)
        ax4.legend(fontsize=9, loc='upper left')
        ax4.grid(True, alpha=0.3)

    # 用户活跃分层
    level = load_stats('user_activity_level.csv')
    if level is not None:
        ax5 = fig.add_axes([0.52, 0.08, 0.44, 0.38])
        colors_lv = ['#FF4444', '#FF8800', '#FFBB33', '#66BB6A', '#42A5F5']
        wedges, texts, autotexts = ax5.pie(
            level['用户数'], labels=level['活跃等级'], autopct='%1.1f%%',
            colors=colors_lv[:len(level)], startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1})
        for t in autotexts:
            t.set_fontsize(9)
        ax5.set_title('用户活跃度分层', fontsize=12, fontweight='bold')

    plt.suptitle('淘宝用户行为数据分析看板', fontsize=18, fontweight='bold', y=0.98)
    plt.savefig(f'{CHART_DIR}/12_dashboard.png', bbox_inches='tight', dpi=150)
    plt.close()
    print('    ✅')


# ==================== 图表 13: 用户分群特征对比 ====================
def chart_segment_profile():
    """图13: 各用户分群特征对比"""
    print('  生成图13: 用户分群特征对比...')

    df = load_stats('segment_profile.csv')
    if df is None:
        return

    metrics = ['平均购买数', '平均加购数', '平均收藏数', '平均活跃天数', '平均品类数']
    segments = df['用户分群'].values

    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 5))

    colors_sg = plt.cm.Set3(np.linspace(0, 1, len(segments)))

    for i, metric in enumerate(metrics):
        ax = axes[i]
        vals = df[metric].values
        bars = ax.bar(range(len(segments)), vals, color=colors_sg, edgecolor='white')
        ax.set_title(metric, fontsize=11, fontweight='bold')
        ax.set_xticks(range(len(segments)))
        ax.set_xticklabels([s[:4] for s in segments], rotation=45, fontsize=8)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f'{val:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.suptitle('各用户分群特征对比', fontsize=14, fontweight='bold', y=1.05)
    plt.tight_layout()
    plt.savefig(f'{CHART_DIR}/13_segment_profile.png', bbox_inches='tight')
    plt.close()
    print('    ✅')


# ==================== 图表 14: 高价值用户小时偏好 ====================
def chart_high_value_hourly():
    """图14: 高价值用户活跃时段"""
    print('  生成图14: 高价值用户活跃时段...')

    # 直接从 config 获取路径
    from config import CLEANED_DATA
    sample_path = CLEANED_DATA
    rfm_path = os.path.join(STATS_DIR, 'rfm_scores.csv')

    if os.path.exists(rfm_path):
        rfm = pd.read_csv(rfm_path)
        if '用户分群' in rfm.columns and os.path.exists(sample_path):
            df = pd.read_parquet(sample_path, engine="fastparquet", columns=["user_id","item_id","category_id","behavior_type","timestamp","hour","weekday","weekend"])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            df['date'] = df['datetime'].dt.date.astype(str)

            high_users = rfm[rfm['用户分群'] == '高价值用户']['user_id'].tolist()
            if len(high_users) > 10:
                high_df = df[df['user_id'].isin(high_users)]
                other_df = df[~df['user_id'].isin(high_users)]

                high_hourly = high_df.groupby('hour').size() / len(high_df['user_id'].unique())
                other_hourly = other_df.groupby('hour').size() / len(other_df['user_id'].unique())

                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(high_hourly.index, high_hourly.values,
                        label='高价值用户', color='#FF6B35', linewidth=2.5, marker='o', markersize=5)
                ax.plot(other_hourly.index, other_hourly.values,
                        label='其他用户', color='#5B9BD5', linewidth=2.5, marker='s', markersize=5)
                ax.set_title('高价值用户 vs 其他用户 24小时活跃度对比（人均）',
                            fontsize=14, fontweight='bold', pad=15)
                ax.set_xlabel('小时', fontsize=12)
                ax.set_ylabel('人均行为次数', fontsize=12)
                ax.set_xticks(range(0, 24))
                ax.legend(fontsize=12)
                ax.grid(True, alpha=0.3)

                plt.tight_layout()
                plt.savefig(f'{CHART_DIR}/14_high_value_hourly.png', bbox_inches='tight')
                plt.close()
                print('    ✅')
            else:
                print('    ⚠ 高价值用户太少，跳过')
        else:
            print('    ⚠ 数据不足，跳过')
    else:
        print('    ⚠ RFM数据不存在，跳过')


# ==================== 主函数 ====================
def generate_all_charts():
    """生成所有图表"""
    print('=' * 60)
    print('生成所有可视化图表')
    print('=' * 60)

    chart_behavior_distribution()
    chart_hourly_activity()
    chart_weekly_activity()
    chart_daily_trend()
    chart_conversion_funnel()
    chart_daily_conversion()
    chart_user_segments()
    chart_rfm_segments()
    chart_transition_heatmap()
    chart_pre_purchase()
    chart_high_value_comparison()
    chart_dashboard()
    chart_segment_profile()
    chart_high_value_hourly()

    print('\n' + '=' * 60)
    print(f'✅ 所有图表已生成到 {CHART_DIR}/')
    print('=' * 60)


if __name__ == '__main__':
    generate_all_charts()
