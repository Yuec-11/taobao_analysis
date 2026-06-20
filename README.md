<div align="center">
  <h1>🛒 淘宝用户行为数据分析</h1>
  <p>基于淘宝100M条真实用户行为数据的全链路分析项目</p>

  <p>
    <a href="#-项目概述">概述</a> •
    <a href="#-项目结构">结构</a> •
    <a href="#-快速开始">快速开始</a> •
    <a href="#-分析内容">分析内容</a> •
    <a href="#-结果预览">预览</a> •
    <a href="#-Power-BI">Power BI</a>
  </p>
</div>

---

## 📋 项目概述

对淘宝用户在 **2017年11月25日 ~ 2017年12月3日**（9天）的约 **1亿条** 行为记录进行全链路数据分析：

- **数据清洗** — 逐块处理3.5GB原始数据，检测并处理重复值/异常值
- **行为分析** — 活跃时段、星期偏好、用户分层、TOP商品、新老用户分析
- **转化漏斗** — 浏览→收藏→加购→购买各环节转化率与流失分析
- **RFM模型** — 用户价值评分与8类用户分群
- **可视化** — 13张分析图表 + 综合数据看板
- **Power BI** — 5张可直接导入的数据表 + 30-sheet Excel报告

### 数据集

| 项目 | 说明 |
|------|------|
| 来源 | 阿里云天池 - 淘宝用户行为数据 |
| 数据量 | ~1亿条记录，约3.5GB |
| 采样后 | ~1000万条，约10万用户 |
| 字段 | user_id, item_id, category_id, behavior_type, timestamp |
| 行为 | pv(浏览), fav(收藏), cart(加购), buy(购买) |

---

## 📁 项目结构

```
taobao_analysis/
├── main.py                      # 🚀 项目入口（PyCharm 直接运行）
├── requirements.txt             # 依赖清单
├── setup.py                     # 安装脚本
├── .gitignore                   # Git 忽略规则
│
├── scripts/                     # 📦 分析脚本包
│   ├── __init__.py
│   ├── config.py                # 全局配置（路径、常量、映射）
│   ├── utils.py                 # 共享工具函数
│   ├── 01_data_cleaning.py      # 数据清洗与预处理
│   ├── 02_user_behavior_analysis.py  # 用户行为分析
│   ├── 03_conversion_funnel.py  # 行为转化漏斗分析
│   ├── 04_user_value_analysis.py     # RFM用户价值分析
│   ├── 05_visualization.py      # 可视化图表生成
│   ├── 06_sql_analysis.py       # SQL分析（SQLite兼容）
│   ├── 07_export_for_powerbi.py # Power BI数据导出
│   └── run_all.py               # 传统主控脚本
│
├── data/
│   └── raw/                     # 📥 原始数据存放处
│       └── .gitkeep             # （将 UserBehavior.csv 放在这里）
│
├── output/                      # 📊 分析结果（自动生成，已 gitignore）
│   ├── cleaned_sample.parquet   # 清洗后数据缓存
│   ├── stats/                   # 统计结果 CSV
│   ├── charts/                  # 可视化图表 PNG
│   ├── powerbi/                 # Power BI 数据文件
│   └── reports/                 # Excel报告
│
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- Python **3.8+**（推荐 3.10）
- 约 **8GB** 可用内存（处理3.5GB原始数据）
- 约 **10GB** 磁盘空间

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/taobao_analysis.git
cd taobao_analysis

# 安装依赖
pip install -r requirements.txt
```

### 准备数据

1. 从 [阿里云天池](https://tianchi.aliyun.com/dataset/649) 下载 `UserBehavior.csv`
2. 放入 `data/raw/` 目录
3. 或使用软链：`ln -s /your/path/UserBehavior.csv data/raw/UserBehavior.csv`

### 运行分析

**方式一：PyCharm**
- 打开项目根目录
- 右键 `main.py` → Run 'main'

**方式二：命令行**

```bash
# 运行全部 7 个步骤
python main.py

# 仅运行数据清洗
python main.py --step 1

# 运行前 4 个步骤
python main.py --step 1-4

# 查看所有步骤
python main.py --list
```

**方式三：单独运行某一步**

```bash
# 项目根目录下
python scripts/03_conversion_funnel.py
```

---

## 📊 分析内容

### 第一部分：数据清洗 (`01_data_cleaning.py`)
| 检查项 | 结果 |
|--------|------|
| 缺失值 | 0（无缺失） |
| 重复行 | ~49行 |
| 非法行为类型 | 0 |
| 异常时间戳 | ~2,808条 |
| 采样 | 按用户分层10% → ~1000万行 |

### 第二部分：用户行为分析 (`02_user_behavior_analysis.py`)
- 总体概览：用户数、商品数、行为分布
- 时间维度：小时活跃度、星期偏好、每日趋势、周末vs工作日
- 用户分层：S/A/B/C/D 五级活跃度
- TOP商品/品类、转化率最高商品
- 新老用户分析

### 第三部分：转化漏斗 (`03_conversion_funnel.py`)
- 用户级漏斗：浏览→收藏→加购→购买各环节转化率
- 事件级漏斗
- 每日转化率趋势
- 用户行为路径（行为转移矩阵）
- 购买前行为模式
- 品类转化率对比

### 第四部分：RFM用户价值 (`04_user_value_analysis.py`)
- **R** (Recency): 最近一次行为距今天数
- **F** (Frequency): 行为频率
- **M** (Monetary): 加权价值评分（fav×2 + cart×3 + buy×5）
- 8类用户分群：高价值用户、发展用户、保持用户、新用户、挽留用户...

### 第五部分：可视化 (`05_visualization.py`)
13张分析图表覆盖全部分析维度

### SQL分析 (`06_sql_analysis.py`)
10个SQL查询在SQLite中复现核心分析指标

### Power BI导出 (`07_export_for_powerbi.py`)
- 5张可直接加载的CSV表
- 30-sheet Excel综合报告

---

## 🖼️ 结果预览

| 图表 | 说明 |
|------|------|
| `01_behavior_distribution.png` | 各行为分布柱状图 |
| `02_hourly_activity.png` | 24小时活跃度折线图 |
| `03_weekly_activity.png` | 一周行为分布 |
| `04_daily_trend.png` | 每日行为趋势 |
| `05_conversion_funnel.png` | 转化漏斗图 |
| `06_daily_conversion_trend.png` | 每日转化率趋势 |
| `07_user_activity_segments.png` | 用户活跃度分层 |
| `08_rfm_segments.png` | RFM用户价值分群 |
| `09_transition_heatmap.png` | 行为转移热力图 |
| `10_pre_purchase_behavior.png` | 购买前行为分布 |
| `11_high_value_radar.png` | 高价值用户雷达图 |
| `12_dashboard.png` | 综合数据看板 |
| `13_segment_profile.png` | 用户分群特征对比 |

### 关键发现

| 指标 | 数值 |
|------|------|
| 浏览→购买转化率（用户级） | **68.01%** |
| 浏览→购买转化率（事件级） | **2.24%** |
| 高活跃时段 | 13:00-14:00, 21:00-22:00 |
| 周末活跃度 | 工作日的 **2.3倍** |
| 高价值用户占比 | **22.26%** |
| 流失风险用户 | **20.83%** |
| 高价值用户日均行为 | **151.68次**（vs 92.25） |

---

## 📈 Power BI 看板

导出的CSV文件（`output/powerbi/`）可直接在Power BI中加载：

```bash
output/powerbi/
├── user_daily_behavior.csv    # 用户每日行为（~71万行）
├── user_profile.csv           # 用户画像（~10万行）
├── item_stats.csv             # 商品统计（~159万行）
├── daily_summary.csv          # 每日汇总
└── hourly_summary.csv         # 小时维度
```

**Power BI Desktop 操作步骤：**
1. 获取数据 → 文本/CSV → 选择上述文件
2. 建立关系：`user_daily_behavior[user_id]` ↔ `user_profile[user_id]`
3. 创建可视化看板（日趋势、漏斗图、用户分群饼图等）

---

## 🧪 技术要点

- **大文件处理**: pandas `chunksize` 逐块读取（500K行/块），避免OOM
- **分层采样**: 按用户ID分层，保持用户行为完整性
- **存储格式**: Parquet + fastparquet 引擎，高效压缩与快速读取
- **路径管理**: 所有路径基于项目根目录相对计算，跨平台兼容
- **Python 3.8+ 兼容**: 无需额外依赖，标准数据科学生态

---

## 📝 许可证

MIT License

## 🙏 致谢

- 阿里云天池平台提供原始数据集
- 数据分析与可视化参考了RFM模型标准框架
