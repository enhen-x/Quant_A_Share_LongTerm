# 研究分析脚本实现计划

## 项目概述

基于现有的股票市场数据（日线行情、市值数据、行业分类等），实现一套完整的多维度分析系统，用于研究股票收益率分布特征、行业轮动规律、市值效应等。

---

## 数据基础

### 可用数据源
1. **股票日线数据** (`data/raw/market/daily/`)
   - 约3000+只股票，2010年至今
   - 字段：开高低收、成交量、成交额、涨跌幅等

2. **市值估值数据** (`data/meta/daily_basic/by_stock/`)
   - 总市值、流通市值、换手率
   - PE、PB、PS等估值指标

3. **行业分类数据** (`data/meta/`)
   - 申万一级、二级、三级行业分类
   - 股票-行业映射关系

4. **行业指数数据** (`data/raw/industry/`)
   - 约30个申万一级行业指数
   - 行业整体表现数据

5. **市场指数数据** (`data/raw/index/`)
   - 上证指数、沪深300、中证500等
   - 市场基准数据

---

## 脚本实现计划

### 阶段一：基础分析脚本（优先级：P0）

#### 1. industry_analysis.py - 行业维度分析
**目标**: 分析不同行业的收益率分布特征和轮动规律

**核心功能**:
- 计算各行业的收益率统计（均值、标准差、偏度、峰度）
- 分析行业收益率的时间序列特征
- 识别行业轮动周期和规律
- 计算行业相对强弱（相对市场基准）
- 行业间收益率差异显著性检验

**输入数据**:
- `data/raw/industry/*.parquet` - 行业指数日线
- `data/meta/stock_industry_mapping.parquet` - 股票行业映射
- `data/raw/market/daily/*.parquet` - 个股日线（用于行业内个股分析）
- `data/raw/index/000300.SH.parquet` - 沪深300作为基准

**输出结果**:
- `results/industry_analysis/industry_stats.csv` - 行业统计表
- `results/industry_analysis/industry_rotation.csv` - 行业轮动分析
- `results/industry_analysis/industry_relative_strength.csv` - 行业相对强弱
- `results/industry_analysis/plots/` - 可视化图表
  - 行业收益率分布图
  - 行业轮动热力图
  - 行业相对强弱走势图

**第一阶段补充分析清单（与`01_industry_analysis_plan.md`一致）**:
1. 多周期收益与风险：日/周/月收益与波动，扩展指标（Profit/Loss、Calmar、Sortino）
2. 行业收益分布：直方/KDE、箱线/小提琴等分布形态对比
3. 行业轮动热力图+信号：动量窗口热力图与强弱轮动信号
4. 相对强弱排名/分位：相对收益、累计相对收益、排名与分位序列
5. 行业内个股分布与集中度：离散度、集中度、胜率等结构指标
6. 显著性检验补强：多重检验校正（FDR/BH）+ 效应量（Cohen's d）

**关键指标**:
- 行业平均收益率（日/周/月）
- 行业收益率波动率
- 行业夏普比率
- 行业最大回撤
- 行业Beta系数
- 行业相对收益率（超额收益）

**实现难点**:
- 处理行业成分股变动（需要时间序列对齐）
- 行业指数与个股数据的一致性验证
- 行业轮动周期的识别算法

---

#### 2. market_cap_analysis.py - 市值维度分析
**目标**: 分析不同市值区间股票的收益率分布特征

**核心功能**:
- 按市值分组（大盘、中盘、小盘、微盘）
- 计算各市值组的收益率统计
- 分析市值效应（小盘股溢价/折价）
- 市值组收益率的时间稳定性分析
- 市值与收益率的非线性关系探索

**输入数据**:
- `data/meta/daily_basic/by_stock/*.parquet` - 市值数据
- `data/raw/market/daily/*.parquet` - 个股日线
- `data/raw/index/000300.SH.parquet` - 市场基准

**输出结果**:
- `results/market_cap_analysis/cap_group_stats.csv` - 市值组统计
- `results/market_cap_analysis/cap_effect.csv` - 市值效应分析
- `results/market_cap_analysis/cap_time_series.csv` - 市值效应时间序列
- `results/market_cap_analysis/plots/` - 可视化图表
  - 市值组收益率分布图
  - 市值效应时间序列图
  - 市值与收益率散点图

**市值分组标准**:
- 大盘股：市值 > 500亿
- 中盘股：100亿 < 市值 <= 500亿
- 小盘股：50亿 < 市值 <= 100亿
- 微盘股：市值 <= 50亿

**关键指标**:
- 各市值组平均收益率
- 各市值组收益率波动率
- 市值效应系数（回归分析）
- 市值组相对收益率
- 市值组换手率差异

**实现难点**:
- 市值数据的动态更新（股票市值随时间变化）
- 幸存者偏差处理（退市股票）
- 市值分组的动态调整

---

#### 3. volatility_analysis.py - 波动率分析
**目标**: 分析收益率波动率的分布特征和预测能力

**核心功能**:
- 计算历史波动率（不同窗口期）
- 分析波动率的时间序列特征（波动率聚集性）
- 波动率与未来收益率的关系
- 高波动率股票的收益率分布
- 波动率分组的收益率差异

**输入数据**:
- `data/raw/market/daily/*.parquet` - 个股日线
- `data/processed/rolling_stats/` - 滚动统计数据（如果已计算）

**输出结果**:
- `results/volatility_analysis/volatility_stats.csv` - 波动率统计
- `results/volatility_analysis/volatility_return_relation.csv` - 波动率-收益率关系
- `results/volatility_analysis/volatility_groups.csv` - 波动率分组分析
- `results/volatility_analysis/plots/` - 可视化图表
  - 波动率分布图
  - 波动率时间序列图
  - 波动率-收益率散点图
  - 波动率聚集性图

**波动率计算方法**:
- 标准差法（5日、20日、60日）
- GARCH模型（可选）
- 已实现波动率（Realized Volatility）
- 帕金森波动率（Parkinson Volatility，使用高低价）

**关键指标**:
- 历史波动率均值
- 波动率的波动率（Vol of Vol）
- 波动率自相关系数
- 高波动率组 vs 低波动率组收益率
- 波动率风险溢价

**实现难点**:
- 波动率的准确计算（处理停牌、涨跌停）
- 波动率预测模型的选择
- 波动率异常值处理

---

### 阶段二：高级分析脚本（优先级：P1）

#### 4. time_consistency.py - 时间一致性分析
**目标**: 分析收益率分布特征在不同时间段的稳定性

**核心功能**:
- 滚动窗口分析（不同时间窗口的统计特征）
- 牛熊市分布差异分析
- 季节性效应分析（月份效应、星期效应）
- 分布参数的时间稳定性检验
- 结构突变检测

**输入数据**:
- `data/raw/market/daily/*.parquet` - 个股日线
- `data/raw/index/*.parquet` - 市场指数（用于牛熊市划分）
- `data/meta/trade_cal.parquet` - 交易日历

**输出结果**:
- `results/time_consistency/rolling_stats.csv` - 滚动窗口统计
- `results/time_consistency/bull_bear_comparison.csv` - 牛熊市对比
- `results/time_consistency/seasonal_effect.csv` - 季节性效应
- `results/time_consistency/stability_test.csv` - 稳定性检验结果
- `results/time_consistency/plots/` - 可视化图表
  - 滚动统计时间序列图
  - 牛熊市分布对比图
  - 季节性效应图
  - 结构突变检测图

**时间窗口设置**:
- 短期：20日、60日
- 中期：120日、250日
- 长期：500日、1000日

**关键指标**:
- 滚动均值、标准差、偏度、峰度
- 牛熊市收益率差异
- 月份平均收益率
- 星期平均收益率
- 分布参数的变异系数

**实现难点**:
- 牛熊市的客观划分标准
- 结构突变点的识别算法
- 季节性效应的显著性检验

---

#### 5. clustering_analysis.py - 聚类分析
**目标**: 基于收益率特征对股票进行聚类，发现相似模式

**核心功能**:
- 基于收益率时间序列的聚类
- 基于统计特征的聚类（均值、波动率、偏度、峰度）
- 聚类结果的行业分布分析
- 聚类结果的市值分布分析
- 聚类稳定性分析

**输入数据**:
- `data/raw/market/daily/*.parquet` - 个股日线
- `data/meta/stock_industry_mapping.parquet` - 行业映射
- `data/meta/daily_basic/by_stock/*.parquet` - 市值数据

**输出结果**:
- `results/clustering_analysis/cluster_labels.csv` - 聚类标签
- `results/clustering_analysis/cluster_profiles.csv` - 聚类特征画像
- `results/clustering_analysis/cluster_industry_dist.csv` - 聚类行业分布
- `results/clustering_analysis/cluster_cap_dist.csv` - 聚类市值分布
- `results/clustering_analysis/plots/` - 可视化图表
  - 聚类结果可视化（PCA降维）
  - 聚类特征雷达图
  - 聚类行业分布图
  - 聚类市值分布图

**聚类算法**:
- K-Means聚类
- 层次聚类（Hierarchical Clustering）
- DBSCAN（密度聚类）
- 时间序列聚类（DTW距离）

**特征工程**:
- 收益率统计特征（均值、标准差、偏度、峰度）
- 技术指标（RSI、MACD、布林带等）
- 波动率特征
- 换手率特征
- 市值、行业等基本面特征

**关键指标**:
- 聚类数量（肘部法则、轮廓系数）
- 聚类内聚度和分离度
- 聚类稳定性指标
- 聚类与行业/市值的关联度

**实现难点**:
- 高维数据的降维处理
- 聚类数量的自动选择
- 时间序列聚类的距离度量
- 聚类结果的可解释性

---

#### 6. correlation_analysis.py - 相关性分析
**目标**: 分析股票间、行业间的相关性结构

**核心功能**:
- 计算股票间收益率相关性矩阵
- 计算行业间相关性矩阵
- 相关性的时间变化分析（滚动相关性）
- 识别高相关性股票组
- 相关性网络分析

**输入数据**:
- `data/raw/market/daily/*.parquet` - 个股日线
- `data/raw/industry/*.parquet` - 行业指数
- `data/meta/stock_industry_mapping.parquet` - 行业映射

**输出结果**:
- `results/correlation_analysis/stock_correlation_matrix.csv` - 股票相关性矩阵
- `results/correlation_analysis/industry_correlation_matrix.csv` - 行业相关性矩阵
- `results/correlation_analysis/rolling_correlation.csv` - 滚动相关性
- `results/correlation_analysis/high_corr_pairs.csv` - 高相关性股票对
- `results/correlation_analysis/plots/` - 可视化图表
  - 相关性热力图
  - 相关性网络图
  - 滚动相关性时间序列图
  - 相关性分布直方图

**相关性计算方法**:
- Pearson相关系数
- Spearman秩相关系数
- Kendall相关系数
- 动态条件相关性（DCC-GARCH，可选）

**关键指标**:
- 平均相关性
- 相关性分布（直方图）
- 高相关性对数量（相关性 > 0.7）
- 相关性的时间稳定性
- 行业内相关性 vs 行业间相关性

**实现难点**:
- 大规模相关性矩阵的计算效率
- 相关性的统计显著性检验
- 相关性网络的可视化
- 滚动相关性的平滑处理

---

### 阶段三：综合报告脚本（优先级：P2）

#### 7. comprehensive_report.py - 综合分析报告
**目标**: 整合所有分析结果，生成综合研究报告

**核心功能**:
- 汇总所有分析模块的结果
- 生成HTML/PDF格式的研究报告
- 关键发现和结论总结
- 投资建议和风险提示
- 交互式可视化仪表板

**输入数据**:
- `results/industry_analysis/` - 行业分析结果
- `results/market_cap_analysis/` - 市值分析结果
- `results/volatility_analysis/` - 波动率分析结果
- `results/time_consistency/` - 时间一致性分析结果
- `results/clustering_analysis/` - 聚类分析结果
- `results/correlation_analysis/` - 相关性分析结果

**输出结果**:
- `results/comprehensive_report/report.html` - HTML报告
- `results/comprehensive_report/report.pdf` - PDF报告
- `results/comprehensive_report/executive_summary.md` - 执行摘要
- `results/comprehensive_report/dashboard/` - 交互式仪表板

**报告结构**:
1. **执行摘要**
   - 研究背景和目标
   - 主要发现
   - 投资建议

2. **数据概览**
   - 数据范围和质量
   - 样本统计

3. **行业分析**
   - 行业收益率特征
   - 行业轮动规律
   - 行业投资建议

4. **市值分析**
   - 市值效应
   - 市值组表现
   - 市值配置建议

5. **波动率分析**
   - 波动率特征
   - 波动率与收益率关系
   - 风险管理建议

6. **时间一致性分析**
   - 分布稳定性
   - 季节性效应
   - 时机选择建议

7. **聚类分析**
   - 股票分类
   - 聚类特征
   - 组合构建建议

8. **相关性分析**
   - 相关性结构
   - 分散化效果
   - 风险对冲建议

9. **综合结论**
   - 关键发现总结
   - 投资策略建议
   - 风险提示

**技术实现**:
- 使用Jinja2模板生成HTML报告
- 使用WeasyPrint或ReportLab生成PDF
- 使用Plotly/Dash构建交互式仪表板
- 使用Markdown生成执行摘要

**实现难点**:
- 报告的自动化生成
- 图表的美观性和可读性
- 交互式仪表板的性能优化
- 报告的定期更新机制

---

## 技术架构

### 通用模块设计

#### 1. 数据加载模块 (`utils/data_loader.py`)
```python
class DataLoader:
    """统一的数据加载接口"""
    
    def load_stock_daily(self, ts_code: str, start_date: str, end_date: str)
    def load_all_stocks_daily(self, start_date: str, end_date: str)
    def load_industry_data(self, industry_code: str, start_date: str, end_date: str)
    def load_market_cap(self, ts_code: str, start_date: str, end_date: str)
    def load_stock_industry_mapping(self)
    def load_trade_calendar(self)
```

#### 2. 统计计算模块 (`utils/statistics.py`)
```python
class StatisticsCalculator:
    """统计指标计算"""
    
    def calc_return(self, prices: pd.Series, method: str = 'simple')
    def calc_volatility(self, returns: pd.Series, window: int = 20)
    def calc_rolling_stats(self, data: pd.Series, window: int)
    def calc_distribution_params(self, data: pd.Series)
    def test_normality(self, data: pd.Series)
    def test_stationarity(self, data: pd.Series)
```

#### 3. 可视化模块 (`utils/visualization.py`)
```python
class Visualizer:
    """统一的可视化接口"""
    
    def plot_distribution(self, data: pd.Series, title: str)
    def plot_time_series(self, data: pd.DataFrame, title: str)
    def plot_heatmap(self, matrix: pd.DataFrame, title: str)
    def plot_correlation_network(self, corr_matrix: pd.DataFrame)
    def save_figure(self, fig, filepath: str)
```

#### 4. 报告生成模块 (`utils/report_generator.py`)
```python
class ReportGenerator:
    """报告生成工具"""
    
    def generate_html_report(self, data: dict, template: str)
    def generate_pdf_report(self, html_path: str, pdf_path: str)
    def generate_markdown_summary(self, data: dict)
    def create_dashboard(self, data: dict)
```

---

## 实施步骤

### Phase 1: 基础设施搭建（1-2天）
1. 创建目录结构
   ```bash
   mkdir -p scripts/analysis/research
   mkdir -p results/{industry_analysis,market_cap_analysis,volatility_analysis,time_consistency,clustering_analysis,correlation_analysis,comprehensive_report}
   mkdir -p utils
   ```

2. 实现通用模块
   - `utils/data_loader.py`
   - `utils/statistics.py`
   - `utils/visualization.py`
   - `utils/report_generator.py`

3. 编写单元测试
   - `tests/test_data_loader.py`
   - `tests/test_statistics.py`

### Phase 2: 基础分析脚本（3-5天）
1. 实现 `industry_analysis.py`
2. 实现 `market_cap_analysis.py`
3. 实现 `volatility_analysis.py`
4. 测试和调试

### Phase 3: 高级分析脚本（3-5天）
1. 实现 `time_consistency.py`
2. 实现 `clustering_analysis.py`
3. 实现 `correlation_analysis.py`
4. 测试和调试

### Phase 4: 综合报告（2-3天）
1. 实现 `comprehensive_report.py`
2. 设计报告模板
3. 构建交互式仪表板
4. 整体测试

### Phase 5: 优化和文档（1-2天）
1. 性能优化
2. 代码重构
3. 编写文档
4. 用户手册

---

## 性能优化策略

### 1. 数据加载优化
- 使用Parquet格式（已实现）
- 按需加载数据（避免一次性加载所有股票）
- 使用缓存机制（LRU Cache）
- 并行加载数据（multiprocessing）

### 2. 计算优化
- 向量化计算（NumPy/Pandas）
- 使用Numba加速关键计算
- 并行计算（joblib/dask）
- 增量计算（避免重复计算）

### 3. 内存优化
- 分批处理数据
- 及时释放不需要的数据
- 使用生成器（generator）
- 数据类型优化（float32 vs float64）

---

## 质量保证

### 1. 代码质量
- 遵循PEP 8编码规范
- 使用类型提示（Type Hints）
- 编写文档字符串（Docstrings）
- 代码审查（Code Review）

### 2. 测试覆盖
- 单元测试（pytest）
- 集成测试
- 性能测试
- 数据验证测试

### 3. 错误处理
- 异常捕获和处理
- 日志记录（logging）
- 数据验证
- 边界条件检查

---

## 依赖包清单

### 核心依赖
```
pandas>=1.5.0
numpy>=1.23.0
scipy>=1.9.0
statsmodels>=0.13.0
scikit-learn>=1.1.0
```

### 可视化
```
matplotlib>=3.6.0
seaborn>=0.12.0
plotly>=5.11.0
```

### 报告生成
```
jinja2>=3.1.0
weasyprint>=57.0
markdown>=3.4.0
```

### 性能优化
```
numba>=0.56.0
joblib>=1.2.0
dask>=2022.10.0
```

### 其他
```
tqdm>=4.64.0  # 进度条
loguru>=0.6.0  # 日志
pyyaml>=6.0  # 配置文件
```

---

## 配置文件

### config/research_config.yaml
```yaml
# 研究分析配置

# 数据范围
data_range:
  start_date: "20100101"
  end_date: "20241231"
  
# 市值分组
market_cap_groups:
  large: 50000000000  # 500亿
  medium: 10000000000  # 100亿
  small: 5000000000    # 50亿
  
# 波动率计算
volatility:
  windows: [5, 20, 60, 120, 250]
  method: "std"  # std, garch, realized, parkinson
  
# 时间窗口
time_windows:
  short: [20, 60]
  medium: [120, 250]
  long: [500, 1000]
  
# 聚类参数
clustering:
  n_clusters: 10
  method: "kmeans"  # kmeans, hierarchical, dbscan
  features: ["return_mean", "return_std", "skewness", "kurtosis"]
  
# 相关性计算
correlation:
  method: "pearson"  # pearson, spearman, kendall
  rolling_window: 250
  threshold: 0.7
  
# 报告生成
report:
  format: ["html", "pdf", "markdown"]
  include_plots: true
  interactive_dashboard: true
```

---

## 预期输出示例

### 1. 行业分析输出
```
results/industry_analysis/
├── industry_stats.csv
│   ├── industry_code, industry_name, mean_return, std_return, sharpe_ratio, max_drawdown
├── industry_rotation.csv
│   ├── date, top_industry, bottom_industry, rotation_signal
├── industry_relative_strength.csv
│   ├── date, industry_code, relative_return, rank
└── plots/
    ├── industry_return_distribution.png
    ├── industry_rotation_heatmap.png
    └── industry_relative_strength.png
```

### 2. 市值分析输出
```
results/market_cap_analysis/
├── cap_group_stats.csv
│   ├── cap_group, mean_return, std_return, sharpe_ratio
├── cap_effect.csv
│   ├── date, small_cap_premium, cap_effect_coefficient
└── plots/
    ├── cap_group_distribution.png
    ├── cap_effect_time_series.png
    └── cap_return_scatter.png
```

---

## 后续扩展方向

### 1. 机器学习模型
- 收益率预测模型
- 风险预测模型
- 因子挖掘

### 2. 高频数据分析
- 分钟级数据分析
- 日内模式识别
- 微观结构分析

### 3. 另类数据
- 舆情数据
- 资金流向数据
- 宏观经济数据

### 4. 实时监控
- 实时数据更新
- 实时指标计算
- 实时预警系统

---

## 项目时间表

| 阶段 | 任务 | 预计时间 | 负责人 |
|------|------|---------|--------|
| Phase 1 | 基础设施搭建 | 1-2天 | - |
| Phase 2 | 基础分析脚本 | 3-5天 | - |
| Phase 3 | 高级分析脚本 | 3-5天 | - |
| Phase 4 | 综合报告 | 2-3天 | - |
| Phase 5 | 优化和文档 | 1-2天 | - |
| **总计** | | **10-17天** | |

---

## 风险和挑战

### 1. 数据质量风险
- **风险**: 数据缺失、异常值、停牌数据
- **应对**: 数据清洗、异常值检测、缺失值处理

### 2. 计算性能风险
- **风险**: 大规模数据计算耗时长
- **应对**: 并行计算、增量计算、缓存机制

### 3. 模型有效性风险
- **风险**: 分析结果可能不稳定或不显著
- **应对**: 稳健性检验、敏感性分析、多模型验证

### 4. 可维护性风险
- **风险**: 代码复杂度高，难以维护
- **应对**: 模块化设计、文档完善、单元测试

---

## 成功标准

### 1. 功能完整性
- ✅ 所有7个分析脚本实现完成
- ✅ 通用模块功能完善
- ✅ 报告生成功能正常

### 2. 性能指标
- ✅ 单个分析脚本运行时间 < 30分钟
- ✅ 综合报告生成时间 < 10分钟
- ✅ 内存占用 < 16GB

### 3. 质量指标
- ✅ 代码测试覆盖率 > 80%
- ✅ 无严重Bug
- ✅ 文档完整

### 4. 可用性指标
- ✅ 用户可以独立运行所有脚本
- ✅ 报告清晰易懂
- ✅ 可视化效果良好

---

## 联系和支持

如有问题或建议，请通过以下方式联系：
- 项目文档：`docs/`
- 问题追踪：GitHub Issues
- 技术讨论：项目Wiki

---

**文档版本**: v1.0  
**最后更新**: 2024-01-XX  
**状态**: 待实施
