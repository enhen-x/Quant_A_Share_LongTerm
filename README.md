# A股动态仓位管理系统（基于偏移率分布网格）

> **项目名称**: Quant_A_Share_Position_Distribution  
> **定位**: 基于偏移率分布特征的A股动态仓位管理系统  
> **核心思路**: 通过分析投资标的价格相对均值的偏移率分布（偏度、峰度），动态划分仓位管理网格  
> **数据源**: Tushare Pro API  
> **更新日期**: 2026-01-22

## 项目简介

本项目通过计算股票价格相对移动均值的偏移率（Deviation Ratio），分析其历史分布的统计特征（偏度、峰度），据此动态划分仓位管理网格。根据当前偏移率在网格中的位置，科学决定仓位配置。

### 与短线项目的定位对比

| 维度 | 短线项目 (Quant_A_Share_V2.0) | 本项目 (长线) |
|------|-----------------------------|---------------|
| 投资周期 | 4-5 个交易日 | 3 个月 ~ 1 年+ |
| 核心逻辑 | 技术面 + 机器学习 | 偏移率分布 + 统计学网格 |
| 换手频率 | 每周调仓 | 季度/月度调仓 |
| 数据源 | Baostock / Akshare | **Tushare Pro** |
| 决策依据 | 预测模型 | 历史分布特征 |

## 核心功能

- 📊 **偏移率计算**: 计算价格相对移动均值/标准差的偏移率
- 📈 **分布分析**: 分析偏移率序列的偏度、峰度、分位数等统计特征
- 🎯 **智能网格**: 根据分布形状（对称/偏态/重尾）自适应划分仓位网格
- 💰 **仓位决策**: 基于当前偏移率位置动态决定仓位
- 🛡️ **风险控制**: 回撤控制、集中度约束、流动性检查
- 📑 **分析报告**: 分布分析、网格可视化、仓位配置报告

## 核心理念

### 偏移率计算

```
DR = (Price - MA) / MA
```

或使用标准差标准化：

```
DR_zscore = (Price - MA) / Std
```

### 分布特征与网格划分

| 分布特征 | 网格策略 | 说明 |
|----------|----------|------|
| 偏度 ≈ 0, 峰度 ≈ 3 | 等距网格 | 近似正态分布，用对称等距划分 |
| 正偏度 (右偏) | 非对称网格 | 右侧稀疏，左侧密集 |
| 负偏度 (左偏) | 非对称网格 | 左侧稀疏，右侧密集 |
| 峰度 > 3 (尖峰) | 中间密集网格 | 极端值较少，中间区域细分 |
| 峰度 < 3 (扁平) | 边缘密集网格 | 极端值较多，边缘区域细分 |

## 数据架构

### 数据需求

| 数据类型 | 用途 | 更新频率 |
|----------|------|----------|
| 日线行情 | 偏移率计算、滚动统计 | 每日 |
| 指数行情 | 基准偏移率 | 每日 |
| 行业指数 | 行业偏移率 | 每日 |
| 偏移率序列 | 分布分析 | 每日 |
| 网格配置 | 网格划分结果 | 周度/月度 |

### 数据存储规划

```
data/
├── raw/                          # 原始数据
│   ├── market/                   # 市场行情
│   │   └── daily/                # 日线数据
│   └── index/                    # 指数数据
│
├── processed/                    # 处理后数据
│   ├── deviation/                # 偏移率数据
│   │   ├── stock_deviation.parquet    # 个股偏移率
│   │   ├── index_deviation.parquet    # 指数偏移率
│   │   └── industry_deviation.parquet # 行业偏移率
│   │
│   ├── distribution/             # 分布统计数据
│   │   ├── dist_stats.parquet        # 分布统计量
│   │   └── histogram.parquet         # 直方图数据
│   │
│   ├── grid/                     # 网格数据
│   │   ├── grid_config.parquet       # 网格配置
│   │   └── zone_mapping.parquet      # 区域映射
│   │
│   └── position/                 # 仓位数据
│       ├── target_position.parquet  # 目标仓位
│       └── position_history.parquet # 仓位历史
│
└── meta/                         # 元数据
    ├── stock_basic.parquet       # 股票基础信息
    └── trade_cal.parquet         # 交易日历
```

### 关键数据格式

- `stock_deviation.parquet`: `trade_date`, `ts_code`, `close`, `ma`, `std`, `dr_raw`, `dr_zscore`, `dr_percentile`, `window_type`, `window_size`
- `dist_stats.parquet`: `as_of_date`, `ts_code`, `stats_window`, `mean`, `std`, `min`, `max`, `skewness`, `kurtosis`, `jarque_bera`, `p_value`, 分位数(`p05`-`p95`), `distribution_type`
- `grid_config.parquet`: `as_of_date`, `ts_code`, `grid_type`, `n_zones`, `distribution_type`，每个区域上下界(`zone_i_lower/upper`)及对应仓位(`zone_i_position`)

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 Tushare Token
# 编辑 config/main.yaml，填入你的 token

# 3. 更新数据
python scripts/data/update_data.py

# 4. 计算偏移率
python scripts/analysis/calc_deviation.py

# 5. 分析分布
python scripts/analysis/analyze_distribution.py

# 6. 生成网格
python scripts/analysis/generate_grid.py

# 7. 计算仓位
python scripts/position/calculate_position.py

# 8. 执行调仓
python scripts/position/run_rebalance.py

# 9. 生成报告
python scripts/report/generate_report.py
```

## 目录结构

```
Quant_A_Share_Position_Distribution/
├── config/
│   └── main.yaml                 # 主配置文件
│
├── data/                         # 数据目录
│   ├── raw/                      # 原始数据
│   ├── processed/                # 处理后数据
│   └── meta/                     # 元数据
│
├── src/
│   ├── data_source/              # 数据获取层
│   │   ├── tushare_source.py     # Tushare API封装
│   │   └── datahub.py            # 统一数据入口
│   │
│   ├── deviation/                # 偏移率计算模块
│   │   ├── calculator.py         # 偏移率计算
│   │   ├── rolling_stats.py     # 滚动统计
│   │   └── normalization.py      # 标准化方法
│   │
│   ├── distribution/             # 分布分析模块
│   │   ├── stats_calculator.py   # 分布统计量计算
│   │   ├── shape_analyzer.py     # 形状分析（偏度、峰度）
│   │   ├── histogram.py          # 直方图统计
│   │   └── kde_estimator.py      # 核密度估计
│   │
│   ├── grid/                     # 网格划分模块
│   │   ├── base_grid.py          # 网格基类
│   │   ├── symmetric_grid.py     # 对称等距网格
│   │   ├── asymmetric_grid.py    # 非对称网格
│   │   ├── adaptive_grid.py      # 自适应网格
│   │   └── zone_manager.py       # 区域管理器
│   │
│   ├── position/                 # 仓位决策模块
│   │   ├── mapper.py             # 偏移率-仓位映射
│   │   ├── position_calculator.py # 仓位计算
│   │   ├── constraints.py        # 约束条件
│   │   └── optimizer.py          # 仓位优化
│   │
│   ├── risk/                     # 风险控制模块
│   │   ├── drawdown_control.py   # 回撤控制
│   │   ├── concentration.py      # 集中度控制
│   │   └── alert.py              # 风险预警
│   │
│   ├── execution/                # 执行模块
│   │   ├── order_generator.py    # 订单生成
│   │   ├── cost_estimator.py     # 成本估算
│   │   └── rebalancer.py         # 调仓执行
│   │
│   ├── analysis/                 # 分析模块
│   │   ├── distribution_report.py # 分布分析报告
│   │   ├── grid_report.py        # 网格分析报告
│   │   └── position_report.py    # 仓位分析报告
│   │
│   └── utils/                    # 工具模块
│       ├── logger.py
│       ├── config.py
│       └── io.py
│
├── scripts/                      # 脚本入口
│   ├── data/
│   │   └── update_data.py        # 数据更新
│   ├── analysis/
│   │   ├── calc_deviation.py     # 计算偏移率
│   │   ├── analyze_distribution.py # 分析分布
│   │   └── generate_grid.py      # 生成网格
│   ├── position/
│   │   ├── calculate_position.py # 计算仓位
│   │   └── run_rebalance.py      # 执行调仓
│   └── report/
│       └── generate_report.py    # 生成报告
│
├── notebooks/                    # 研究笔记
├── reports/                      # 输出报告
├── logs/                         # 日志
│
├── requirements.txt
├── architecture_LongTerm.md       # 详细架构文档
└── README.md
```

## 使用示例

### 单个标的仓位计算

```python
from src.data_source import TushareSource
from src.deviation import DeviationCalculator
from src.distribution import DistributionStats, ShapeAnalyzer
from src.grid import AdaptiveGrid, ZoneManager

# 数据源
data_source = TushareSource(token="YOUR_TOKEN")

# 获取历史数据
prices = data_source.get_daily(
    ts_code='600519.SH',
    start_date='2020-01-01',
    end_date='2024-12-31'
)

# 计算偏移率
calc = DeviationCalculator(window=252)
deviation_df = calc.calculate(prices['close'])

# 分析分布
stats = DistributionStats().calculate_full_stats(
    deviation_df['dr_zscore'].dropna()
)

shape = ShapeAnalyzer().analyze_distribution_shape(stats)

print(f"偏度: {stats['skewness']:.2f}")
print(f"峰度: {stats['kurtosis']:.2f}")
print(f"分布类型: {shape['distribution_type']}")

# 生成网格
grid_gen = AdaptiveGrid(n_zones=10)
grid_config = grid_gen.generate_grid(
    stats=stats,
    distribution_type=shape['distribution_type']
)

# 计算当前仓位
current_price = prices['close'].iloc[-1]
current_deviation = deviation_df['dr_zscore'].iloc[-1]

zone_manager = ZoneManager(grid_config)
position = zone_manager.get_position(current_deviation)

print(f"当前偏移率: {current_deviation:.2f}")
print(f"所在区域: {zone_manager.get_zone(current_deviation)}")
print(f"目标仓位: {position*100:.1f}%")
```

### 批量计算组合仓位

```python
from src.position import PositionCalculator

stocks = ['600519.SH', '000858.SZ', '000001.SZ']

config = {
    'n_zones': 10,
    'update_frequency': 'monthly',
}

calc = PositionCalculator(config)

results = []
for ts_code in stocks:
    prices = data_source.get_daily(ts_code, '2020-01-01', '2024-12-31')
    deviation_calc = DeviationCalculator(window=252)
    deviation_df = deviation_calc.calculate(prices['close'])
    
    result = calc.calculate_position(
        ts_code=ts_code,
        current_price=prices['close'].iloc[-1],
        deviation_history=deviation_df['dr_zscore'].dropna(),
        max_position=0.15
    )
    
    results.append(result)

for r in results:
    print(f"{r['ts_code']}: 偏移率={r['current_deviation']:.2f}, "
          f"区域={r['zone']}, 仓位={r['target_position']*100:.1f}%")
```

## 系统架构

- 输入层: 市场行情、指数行情、当前持仓
- 偏移率计算层: 移动均值/标准差、偏移率序列
- 分布分析层: 偏度、峰度、直方图、分布类型判定
- 网格划分层: 对称/非对称/自适应网格生成与区域标注
- 仓位决策层: 偏移率-仓位映射、仓位计算、约束应用
- 风险控制层: 回撤、集中度、流动性等多重约束
- 输出层: 目标仓位、调仓信号、分析报告

详细架构设计请参考 [architecture_LongTerm.md](./architecture_LongTerm.md)

## 报告输出

- 分布分析报告: 直方图、统计量摘要、偏度/峰度分析、JB 正态检验、分布类型判定、理论分布对比
- 网格可视化报告: 网格划分示意、当前位置标注、各区域仓位分配、历史分布与网格对比
- 仓位分析报告: 组合仓位概览、个股偏移率分布、仓位配置建议、风险指标、调仓计划

## 核心优势

### 理论优势

- **数据驱动**: 基于实际数据分布而非主观假设
- **自适应调整**: 根据分布特征动态调整网格
- **统计严谨**: 利用偏度、峰度等统计量刻画分布
- **可解释性强**: 仓位决策有明确的统计依据

### 实战优势

- **应对极端行情**: 重尾分布情况下边缘加密，更好应对极端
- **避免过度交易**: 平滑机制减少频繁调仓
- **风险可控**: 多重约束确保仓位安全
- **灵活配置**: 支持多种网格策略和参数调整

## 扩展方向

- **多周期网格**: 支持 20/60/252 日等多时间尺度网格，组合信号后决策
- **行业相对网格**: 使用 `DR_relative = DR_stock - DR_industry` 计算相对偏移率并定位仓位
- **贝叶斯更新**: 按 `Posterior ∝ Likelihood × Prior` 随新数据更新分布参数与网格
- **机器学习增强**: 引入 ARIMA、Prophet、XGBoost、LSTM 等模型预测偏移率并映射仓位

## 配置说明

主配置文件 `config/main.yaml` 包含以下配置项：

- Tushare API 配置
- 偏移率计算配置（窗口类型、标准化方法）
- 分布分析配置（统计窗口、直方图参数）
- 网格划分配置（区域数量、范围参数、平滑因子）
- 仓位配置（最大/最小仓位、日变动限制）
- 风险控制配置（回撤、集中度、流动性）
- 调仓配置（触发条件、调仓方式）
- 报告配置（生成频率、报告内容）

## License

MIT