# Scripts 目录说明

本目录包含项目的所有可执行脚本，按功能分类组织。

## 目录结构

```
scripts/
├── data/                    # 数据获取和更新脚本
│   ├── update_data.py              # 更新基础行情数据
│   ├── fetch_daily_basic.py        # 获取市值、估值数据
│   ├── fetch_industry_data.py      # 获取行业分类和行业指数
│   ├── fetch_financial_data.py     # 获取财务数据（可选）
│   └── fetch_index_weight.py       # 获取指数成分股（可选）
│
├── analysis/                # 数据分析脚本
│   ├── calc_deviation.py           # 计算偏移率
│   ├── analyze_distribution.py     # 分析分布特征
│   ├── plot_stock_distribution.py  # 绘制个股分布图
│   └── plot_index_distribution.py  # 绘制指数分布图
│
├── research/                # 研究分析脚本
│   ├── data_gap_analysis.py        # 数据缺口分析
│   ├── industry_analysis.py        # 行业维度分析
│   ├── market_cap_analysis.py      # 市值维度分析
│   ├── volatility_analysis.py      # 波动率分析
│   ├── time_consistency.py         # 时间一致性分析
│   ├── clustering_analysis.py      # 聚类分析
│   ├── correlation_analysis.py     # 相关性分析
│   └── comprehensive_report.py     # 综合分析报告
│
├── calculation/             # 衍生数据计算脚本
│   ├── calc_rolling_stats.py      # 计算滚动分布统计
│   ├── calc_beta.py                # 计算Beta系数
│   ├── calc_relative_deviation.py  # 计算行业相对偏移率
│   └── calc_correlation.py         # 计算相关性矩阵
│
├── grid/                    # 网格相关脚本（待实现）
│   ├── generate_grid.py            # 生成网格配置
│   └── update_grid.py              # 更新网格配置
│
├── position/                # 仓位相关脚本（待实现）
│   ├── calculate_position.py      # 计算目标仓位
│   └── run_rebalance.py            # 执行调仓
│
└── report/                  # 报告生成脚本（待实现）
    └── generate_report.py          # 生成分析报告
```

## 使用说明

### 1. 数据获取流程

```bash
# 步骤1: 更新基础行情数据
python scripts/data/update_data.py

# 步骤2: 获取市值和估值数据
python scripts/data/fetch_daily_basic.py

# 步骤3: 获取行业数据
python scripts/data/fetch_industry_data.py

# 步骤4: 获取财务数据（可选）
python scripts/data/fetch_financial_data.py
```

### 2. 数据分析流程

```bash
# 步骤1: 计算偏移率
python scripts/analysis/calc_deviation.py

# 步骤2: 分析分布特征
python scripts/analysis/analyze_distribution.py

# 步骤3: 绘制分布图
python scripts/analysis/plot_stock_distribution.py
```

### 3. 研究分析流程

```bash
# 行业维度分析
python scripts/research/industry_analysis.py

# 市值维度分析
python scripts/research/market_cap_analysis.py

# 综合分析报告
python scripts/research/comprehensive_report.py
```

### 4. 衍生数据计算

```bash
# 计算滚动统计
python scripts/calculation/calc_rolling_stats.py

# 计算Beta系数
python scripts/calculation/calc_beta.py

# 计算相对偏移率
python scripts/calculation/calc_relative_deviation.py
```

## 脚本参数说明

大部分脚本支持命令行参数，使用 `--help` 查看详细说明：

```bash
python scripts/data/update_data.py --help
```

## 注意事项

1. 首次运行需要先执行数据获取脚本
2. 确保 Tushare Token 已在 config/main.yaml 中配置
3. 数据获取可能需要较长时间，建议使用进度条监控
4. 部分脚本需要依赖前置数据，请按顺序执行