# 行业维度分析脚本实现方案

## 脚本信息
- **文件名**: `scripts/research/industry_analysis.py`
- **优先级**: P0（最高优先级）
- **预计开发时间**: 1-2天
- **依赖**: 数据加载模块、统计计算模块、可视化模块

---

## 功能概述

分析不同行业的收益率分布特征、轮动规律和相对强弱，为行业配置和轮动策略提供数据支持。

---

## 核心功能模块

### 1. 行业基础统计分析
**功能描述**: 计算各行业的基础统计指标

**输入**:
- 行业指数日线数据
- 时间范围参数

**输出**:
- 行业统计表（CSV）
- 行业收益率分布图

**关键指标**:
```python
{
    'industry_code': '801010.SI',
    'industry_name': '农林牧渔',
    'mean_return_daily': 0.0005,      # 日均收益率
    'mean_return_weekly': 0.0025,     # 周均收益率
    'mean_return_monthly': 0.0100,    # 月均收益率
    'std_return_daily': 0.0180,       # 日收益率标准差
    'std_return_weekly': 0.0400,      # 周收益率标准差
    'std_return_monthly': 0.0850,     # 月收益率标准差
    'sharpe_ratio': 1.25,             # 夏普比率（年化）
    'max_drawdown': -0.35,            # 最大回撤
    'skewness': -0.15,                # 偏度
    'kurtosis': 3.50,                 # 峰度
    'win_rate': 0.52,                 # 胜率
    'profit_loss_ratio': 1.15,        # 盈亏比
    'calmar_ratio': 0.85,             # 卡玛比率
    'sortino_ratio': 1.45,            # 索提诺比率
}
```

**实现步骤**:
1. 加载所有行业指数数据
2. 计算日/周/月收益率
3. 计算各项统计指标
4. 生成统计表和分布图
5. 保存结果

---

### 2. 行业轮动分析
**功能描述**: 识别行业轮动周期和规律

**输入**:
- 行业指数日线数据
- 轮动周期参数（如20日、60日）

**输出**:
- 行业轮动表（CSV）
- 行业轮动热力图
- 行业动量排名时间序列

**分析维度**:
```python
# 1. 动量轮动
momentum_windows = [20, 60, 120, 250]  # 不同周期的动量

# 2. 相对强弱轮动
relative_strength = {
    'vs_market': '相对市场基准',
    'vs_industry_avg': '相对行业平均',
}

# 3. 轮动信号
rotation_signals = {
    'strong_to_weak': '强转弱',
    'weak_to_strong': '弱转强',
    '持续强势': 'persistent_strong',
    'persistent_weak': '持续弱势',
}
```

**输出格式**:
```python
{
    'date': '20240115',
    'top_3_industries': ['801030', '801150', '801180'],  # 前3强行业
    'bottom_3_industries': ['801010', '801020', '801040'],  # 后3弱行业
    'rotation_signal': 'strong_to_weak',
    'momentum_20d': 0.05,
    'momentum_60d': 0.12,
    'relative_strength_vs_market': 0.03,
}
```

**实现步骤**:
1. 计算各行业不同周期的动量
2. 计算相对强弱指标
3. 识别轮动信号
4. 生成轮动热力图
5. 保存结果

---

### 3. 行业相对强弱分析
**功能描述**: 计算行业相对市场基准的超额收益

**输入**:
- 行业指数数据
- 市场基准数据（沪深300）

**输出**:
- 行业相对强弱表（CSV）
- 相对强弱走势图
- 超额收益分布图

**计算方法**:
```python
# 相对收益率
relative_return = industry_return - benchmark_return

# 累计相对收益率
cumulative_relative_return = (1 + relative_return).cumprod() - 1

# 相对强弱指标（RSI风格）
rs_index = (industry_price / benchmark_price) * 100

# 排名
rank = relative_return.rank(ascending=False)
```

**输出格式**:
```python
{
    'date': '20240115',
    'industry_code': '801030',
    'industry_name': '食品饮料',
    'industry_return': 0.015,
    'benchmark_return': 0.008,
    'relative_return': 0.007,
    'cumulative_relative_return': 0.125,
    'rs_index': 105.5,
    'rank': 3,
    'percentile': 0.90,
}
```

**实现步骤**:
1. 加载行业和基准数据
2. 计算相对收益率
3. 计算累计相对收益率
4. 计算排名和百分位
5. 生成可视化图表
6. 保存结果

---

### 4. 行业内个股分析
**功能描述**: 分析行业内个股的收益率分布

**输入**:
- 个股日线数据
- 股票-行业映射关系

**输出**:
- 行业内个股统计表
- 行业内收益率分布图
- 行业内个股离散度分析

**分析指标**:
```python
{
    'industry_code': '801030',
    'industry_name': '食品饮料',
    'stock_count': 85,
    'mean_return': 0.0008,
    'median_return': 0.0006,
    'std_return': 0.0250,
    'min_return': -0.0500,
    'max_return': 0.0800,
    'q25_return': -0.0050,
    'q75_return': 0.0150,
    'dispersion': 0.0200,  # 离散度（Q75-Q25）
    'concentration': 0.65,  # 集中度（中位数/均值）
}
```

**实现步骤**:
1. 加载股票-行业映射
2. 按行业分组加载个股数据
3. 计算行业内统计指标
4. 分析离散度和集中度
5. 生成分布图
6. 保存结果

---

### 5. 行业间差异显著性检验
**功能描述**: 检验行业间收益率差异是否显著

**输入**:
- 各行业收益率时间序列

**输出**:
- 显著性检验结果表
- 行业对比箱线图

**检验方法**:
```python
# 1. 方差分析（ANOVA）
from scipy.stats import f_oneway
f_stat, p_value = f_oneway(*industry_returns)

# 2. Kruskal-Wallis检验（非参数）
from scipy.stats import kruskal
h_stat, p_value = kruskal(*industry_returns)

# 3. 两两比较（Post-hoc）
from scipy.stats import ttest_ind
for i, j in combinations(industries, 2):
    t_stat, p_value = ttest_ind(returns_i, returns_j)
```

**输出格式**:
```python
{
    'test_method': 'ANOVA',
    'f_statistic': 12.5,
    'p_value': 0.001,
    'significant': True,
    'pairwise_comparisons': [
        {
            'industry_1': '801030',
            'industry_2': '801010',
            't_statistic': 3.2,
            'p_value': 0.002,
            'significant': True,
        },
        # ...
    ]
}
```

---

## 数据流程图

```
[行业指数数据] ──┐
                 ├──> [数据加载] ──> [收益率计算] ──┐
[市场基准数据] ──┘                                 │
                                                   ├──> [统计分析] ──> [结果输出]
[个股日线数据] ──┐                                 │
                 ├──> [行业分组] ──> [分组统计] ──┘
[行业映射数据] ──┘
```

---

## 代码结构

```python
# scripts/research/industry_analysis.py

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 导入自定义模块
from utils.data_loader import DataLoader
from utils.statistics import StatisticsCalculator
from utils.visualization import Visualizer
from utils.logger import setup_logger

class IndustryAnalyzer:
    """行业维度分析器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.data_loader = DataLoader()
        self.stats_calc = StatisticsCalculator()
        self.visualizer = Visualizer()
        self.logger = setup_logger('industry_analysis')
        
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """加载所有需要的数据"""
        pass
        
    def calc_industry_stats(self, industry_data: pd.DataFrame) -> pd.DataFrame:
        """计算行业基础统计"""
        pass
        
    def analyze_rotation(self, industry_data: pd.DataFrame) -> pd.DataFrame:
        """分析行业轮动"""
        pass
        
    def calc_relative_strength(self, 
                               industry_data: pd.DataFrame,
                               benchmark_data: pd.DataFrame) -> pd.DataFrame:
        """计算相对强弱"""
        pass
        
    def analyze_within_industry(self, 
                                stock_data: Dict[str, pd.DataFrame],
                                industry_mapping: pd.DataFrame) -> pd.DataFrame:
        """分析行业内个股"""
        pass
        
    def test_significance(self, industry_returns: Dict[str, pd.Series]) -> dict:
        """显著性检验"""
        pass
        
    def generate_plots(self, results: dict):
        """生成所有图表"""
        pass
        
    def save_results(self, results: dict):
        """保存分析结果"""
        pass
        
    def run(self):
        """运行完整分析流程"""
        self.logger.info("开始行业维度分析...")
        
        # 1. 加载数据
        data = self.load_data()
        
        # 2. 基础统计
        industry_stats = self.calc_industry_stats(data['industry'])
        
        # 3. 轮动分析
        rotation_results = self.analyze_rotation(data['industry'])
        
        # 4. 相对强弱
        relative_strength = self.calc_relative_strength(
            data['industry'], 
            data['benchmark']
        )
        
        # 5. 行业内分析
        within_industry = self.analyze_within_industry(
            data['stocks'],
            data['mapping']
        )
        
        # 6. 显著性检验
        significance = self.test_significance(data['industry_returns'])
        
        # 7. 生成图表
        results = {
            'stats': industry_stats,
            'rotation': rotation_results,
            'relative_strength': relative_strength,
            'within_industry': within_industry,
            'significance': significance,
        }
        self.generate_plots(results)
        
        # 8. 保存结果
        self.save_results(results)
        
        self.logger.info("行业维度分析完成！")
        return results

def main():
    """主函数"""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description='行业维度分析')
    parser.add_argument('--config', type=str, 
                       default='config/research_config.yaml',
                       help='配置文件路径')
    parser.add_argument('--start-date', type=str, 
                       help='开始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str,
                       help='结束日期 (YYYYMMDD)')
    parser.add_argument('--industries', nargs='+',
                       help='指定行业代码列表')
    parser.add_argument('--output-dir', type=str,
                       default='results/industry_analysis',
                       help='输出目录')
    
    args = parser.parse_args()
    
    # 加载配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 更新配置
    if args.start_date:
        config['data_range']['start_date'] = args.start_date
    if args.end_date:
        config['data_range']['end_date'] = args.end_date
    if args.industries:
        config['industries'] = args.industries
    config['output_dir'] = args.output_dir
    
    # 运行分析
    analyzer = IndustryAnalyzer(config)
    results = analyzer.run()
    
    print(f"\n分析完成！结果已保存到: {args.output_dir}")
    print(f"- 统计表: {args.output_dir}/industry_stats.csv")
    print(f"- 轮动分析: {args.output_dir}/industry_rotation.csv")
    print(f"- 相对强弱: {args.output_dir}/industry_relative_strength.csv")
    print(f"- 图表: {args.output_dir}/plots/")

if __name__ == '__main__':
    main()
```

---

## 第一阶段补充分析清单（与`RESEARCH_PLAN.md`一致）
1. 多周期收益与风险：日/周/月收益与波动，扩展指标（Profit/Loss、Calmar、Sortino）
2. 行业收益分布：直方/KDE、箱线/小提琴等分布形态对比
3. 行业轮动热力图+信号：动量窗口热力图与强弱轮动信号
4. 相对强弱排名/分位：相对收益、累计相对收益、排名与分位序列
5. 行业内个股分布与集中度：离散度、集中度、胜率等结构指标
6. 显著性检验补强：多重检验校正（FDR/BH）+ 效应量（Cohen's d）

## 配置参数

```yaml
# config/research_config.yaml - 行业分析部分

industry_analysis:
  # 数据范围
  start_date: "20100101"
  end_date: "20241231"
  
  # 基准指数
  benchmark: "000300.SH"  # 沪深300
  
  # 行业列表（空表示全部）
  industries: []
  
  # 统计周期
  return_periods:
    - daily
    - weekly
    - monthly
  
  # 轮动分析
  rotation:
    momentum_windows: [20, 60, 120, 250]
    top_n: 3
    bottom_n: 3
  
  # 相对强弱
  relative_strength:
    rolling_window: 250
    
  # 行业内分析
  within_industry:
    min_stocks: 10  # 最少股票数
    
  # 显著性检验
  significance:
    alpha: 0.05
    method: "anova"  # anova, kruskal
    
  # 可视化
  plots:
    figsize: [12, 8]
    dpi: 300
    style: "seaborn"
    
  # 输出
  output:
    save_csv: true
    save_plots: true
    plot_format: "png"
```

---

## 输出示例

### 1. industry_stats.csv
```csv
industry_code,industry_name,mean_return_daily,std_return_daily,sharpe_ratio,max_drawdown,skewness,kurtosis,win_rate
801010.SI,农林牧渔,0.0005,0.0180,1.25,-0.35,-0.15,3.50,0.52
801020.SI,采矿业,0.0003,0.0220,0.85,-0.45,-0.25,4.20,0.48
801030.SI,食品饮料,0.0008,0.0160,1.85,-0.28,0.05,3.20,0.55
...
```

### 2. industry_rotation.csv
```csv
date,top_1,top_2,top_3,bottom_1,bottom_2,bottom_3,rotation_signal
20240115,801030,801150,801180,801010,801020,801040,strong_to_weak
20240116,801030,801180,801150,801020,801010,801050,持续强势
...
```

### 3. industry_relative_strength.csv
```csv
date,industry_code,industry_return,benchmark_return,relative_return,cumulative_relative_return,rank
20240115,801030,0.015,0.008,0.007,0.125,3
20240115,801150,0.012,0.008,0.004,0.098,5
...
```

---

## 可视化示例

### 1. 行业收益率分布图
- 箱线图：展示各行业收益率分布
- 小提琴图：展示分布形状
- 直方图：展示收益率频率分布

### 2. 行业轮动热力图
- X轴：时间
- Y轴：行业
- 颜色：动量或相对强弱

### 3. 行业相对强弱走势图
- 多条线图：各行业相对基准的累计超额收益
- 面积图：展示相对强弱变化

### 4. 行业内个股分布图
- 分面箱线图：每个行业一个子图
- 散点图：行业均值 vs 离散度

---

## 性能优化

### 1. 数据加载优化
```python
# 并行加载行业数据
from joblib import Parallel, delayed

def load_industry(code):
    return pd.read_parquet(f'data/raw/industry/{code}.parquet')

industry_data = Parallel(n_jobs=-1)(
    delayed(load_industry)(code) for code in industry_codes
)
```

### 2. 计算优化
```python
# 向量化计算收益率
returns = prices.pct_change()

# 使用rolling进行滚动计算
rolling_stats = returns.rolling(window=20).agg(['mean', 'std', 'skew', 'kurt'])
```

### 3. 内存优化
```python
# 分批处理个股数据
batch_size = 100
for i in range(0, len(stock_codes), batch_size):
    batch_codes = stock_codes[i:i+batch_size]
    # 处理批次数据
    process_batch(batch_codes)
```

---

## 测试用例

### 1. 单元测试
```python
# tests/test_industry_analysis.py

def test_calc_industry_stats():
    """测试行业统计计算"""
    # 准备测试数据
    test_data = pd.DataFrame({
        'trade_date': pd.date_range('20200101', periods=100),
        'close': np.random.randn(100).cumsum() + 100
    })
    
    # 计算统计
    stats = analyzer.calc_industry_stats(test_data)
    
    # 断言
    assert 'mean_return_daily' in stats
    assert stats['mean_return_daily'] is not None
    assert -1 < stats['mean_return_daily'] < 1

def test_analyze_rotation():
    """测试轮动分析"""
    # ...
```

### 2. 集成测试
```python
def test_full_pipeline():
    """测试完整流程"""
    analyzer = IndustryAnalyzer(test_config)
    results = analyzer.run()
    
    assert 'stats' in results
    assert 'rotation' in results
    assert len(results['stats']) > 0
```

---

## 常见问题

### Q1: 行业数据缺失怎么办？
**A**: 使用前向填充或线性插值，记录缺失情况

### Q2: 行业成分股变动如何处理？
**A**: 使用时点数据，每个时点使用当时的成分股

### Q3: 如何处理新上市行业？
**A**: 从上市日期开始计算，标注数据起始日期

### Q4: 行业分类标准变更怎么办？
**A**: 使用统一的分类标准（如申万2021版），历史数据追溯调整

---

## 下一步计划

1. ✅ 完成基础统计分析
2. ✅ 实现轮动分析
3. ✅ 实现相对强弱分析
4. ⏳ 添加行业内个股分析
5. ⏳ 添加显著性检验
6. ⏳ 优化可视化效果
7. ⏳ 编写单元测试
8. ⏳ 性能优化

---

**文档版本**: v1.0  
**最后更新**: 2024-01-XX  
**状态**: 待实施
```
