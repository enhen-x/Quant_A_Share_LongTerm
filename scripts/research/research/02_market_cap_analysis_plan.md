# 市值维度分析脚本实现方案

## 脚本信息
- **文件名**: `scripts/research/market_cap_analysis.py`
- **优先级**: P0（最高优先级）
- **预计开发时间**: 1-2天
- **依赖**: 数据加载模块、统计计算模块、可视化模块

---

## 功能概述

分析不同市值区间股票的收益率分布特征，研究市值效应（小盘股溢价/折价），为市值配置策略提供数据支持。

---

## 核心功能模块

### 1. 市值分组统计分析
**功能描述**: 按市值将股票分组，计算各组统计指标

**市值分组标准**:
```python
market_cap_groups = {
    'mega_cap': {'min': 100_000_000_000, 'max': float('inf'), 'name': '超大盘'},  # >1000亿
    'large_cap': {'min': 50_000_000_000, 'max': 100_000_000_000, 'name': '大盘'},  # 500-1000亿
    'mid_cap': {'min': 10_000_000_000, 'max': 50_000_000_000, 'name': '中盘'},    # 100-500亿
    'small_cap': {'min': 5_000_000_000, 'max': 10_000_000_000, 'name': '小盘'},   # 50-100亿
    'micro_cap': {'min': 0, 'max': 5_000_000_000, 'name': '微盘'},                # <50亿
}
```

**输出指标**:
```python
{
    'cap_group': 'large_cap',
    'stock_count': 250,
    'avg_market_cap': 75_000_000_000,
    'mean_return_daily': 0.0006,
    'std_return_daily': 0.0180,
    'sharpe_ratio': 1.35,
    'max_drawdown': -0.32,
    'skewness': -0.12,
    'kurtosis': 3.45,
    'win_rate': 0.53,
    'avg_turnover_rate': 0.025,
    'liquidity_score': 0.85,
}
```

**实现步骤**:
1. 加载市值数据和日线数据
2. 按日期动态分组（市值会变化）
3. 计算各组收益率统计
4. 分析流动性指标
5. 生成对比图表

---

### 2. 市值效应分析
**功能描述**: 研究市值与收益率的关系，量化市值效应

**分析方法**:
```python
# 1. 回归分析
# Return_i = α + β * log(MarketCap_i) + ε
from sklearn.linear_model import LinearRegression

model = LinearRegression()
X = np.log(market_caps).reshape(-1, 1)
y = returns
model.fit(X, y)

cap_effect_coefficient = model.coef_[0]  # 市值效应系数

# 2. 分组收益率差异
small_cap_return = small_cap_group['mean_return']
large_cap_return = large_cap_group['mean_return']
small_cap_premium = small_cap_return - large_cap_return

# 3. Fama-French SMB因子
smb_factor = small_cap_portfolio_return - large_cap_portfolio_return
```

**输出指标**:
```python
{
    'date': '20240115',
    'cap_effect_coefficient': -0.0015,  # 负值表示小盘股溢价
    'small_cap_premium': 0.0025,
    'smb_factor': 0.0020,
    't_statistic': 2.5,
    'p_value': 0.012,
    'r_squared': 0.15,
}
```

---

### 3. 市值效应时间序列分析
**功能描述**: 分析市值效应的时间稳定性和周期性

**分析维度**:
```python
# 1. 滚动窗口分析
rolling_windows = [60, 120, 250, 500]

# 2. 牛熊市对比
market_regimes = {
    'bull': '牛市',
    'bear': '熊市',
    'sideways': '震荡市',
}

# 3. 年度对比
yearly_analysis = True
```

**输出格式**:
```python
{
    'date': '20240115',
    'window': 250,
    'small_cap_premium_rolling': 0.0022,
    'cap_effect_coefficient_rolling': -0.0012,
    'market_regime': 'bull',
    'year': 2024,
    'small_cap_premium_ytd': 0.0018,
}
```

---

### 4. 市值与其他因子的交互分析
**功能描述**: 分析市值与行业、估值等因子的交互效应

**交互因子**:
```python
interaction_factors = {
    'industry': '行业',
    'pe_ratio': '市盈率',
    'pb_ratio': '市净率',
    'roe': '净资产收益率',
    'volatility': '波动率',
}
```

**分析方法**:
```python
# 双因子分组
# 例如：市值 × 行业
for cap_group in cap_groups:
    for industry in industries:
        subset = stocks[(stocks['cap_group'] == cap_group) & 
                       (stocks['industry'] == industry)]
        stats = calculate_stats(subset)
```

**输出示例**:
```python
{
    'cap_group': 'small_cap',
    'industry': '801030',  # 食品饮料
    'stock_count': 15,
    'mean_return': 0.0012,
    'interaction_effect': 0.0005,  # 交互效应
}
```

---

### 5. 市值迁移分析
**功能描述**: 分析股票在不同市值组间的迁移

**分析内容**:
```python
# 1. 迁移矩阵
transition_matrix = pd.DataFrame({
    'from_micro': [0.85, 0.12, 0.03, 0.00, 0.00],
    'from_small': [0.08, 0.75, 0.15, 0.02, 0.00],
    'from_mid': [0.02, 0.10, 0.70, 0.15, 0.03],
    'from_large': [0.00, 0.02, 0.12, 0.75, 0.11],
    'from_mega': [0.00, 0.00, 0.03, 0.15, 0.82],
}, index=['to_micro', 'to_small', 'to_mid', 'to_large', 'to_mega'])

# 2. 迁移收益率
# 分析从小盘迁移到大盘的股票收益率特征
```

---

## 数据流程图

```
[市值数据] ──┐
            ├──> [动态分组] ──> [分组统计] ──┐
[日线数据] ──┤                              │
            └──> [收益率计算] ──────────────┤
                                            ├──> [市值效应分析] ──> [结果输出]
[行业数据] ──> [交互分析] ──────────────────┤
                                            │
[基准数据] ──> [相对收益] ──────────────────┘
```

---

## 代码结构

```python
# scripts/research/market_cap_analysis.py

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression

from utils.data_loader import DataLoader
from utils.statistics import StatisticsCalculator
from utils.visualization import Visualizer
from utils.logger import setup_logger

class MarketCapAnalyzer:
    """市值维度分析器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.data_loader = DataLoader()
        self.stats_calc = StatisticsCalculator()
        self.visualizer = Visualizer()
        self.logger = setup_logger('market_cap_analysis')
        
        # 市值分组标准
        self.cap_groups = config.get('market_cap_groups', {
            'mega_cap': 100_000_000_000,
            'large_cap': 50_000_000_000,
            'mid_cap': 10_000_000_000,
            'small_cap': 5_000_000_000,
        })
        
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """加载所有需要的数据"""
        self.logger.info("加载数据...")
        
        data = {
            'market_cap': self._load_market_cap_data(),
            'daily': self._load_daily_data(),
            'industry': self._load_industry_mapping(),
            'benchmark': self._load_benchmark_data(),
        }
        
        return data
        
    def _load_market_cap_data(self) -> pd.DataFrame:
        """加载市值数据"""
        # 从 data/meta/daily_basic/by_stock/ 加载
        pass
        
    def classify_by_market_cap(self, 
                              market_cap_data: pd.DataFrame) -> pd.DataFrame:
        """按市值分组"""
        def get_cap_group(market_cap):
            if market_cap >= self.cap_groups['mega_cap']:
                return 'mega_cap'
            elif market_cap >= self.cap_groups['large_cap']:
                return 'large_cap'
            elif market_cap >= self.cap_groups['mid_cap']:
                return 'mid_cap'
            elif market_cap >= self.cap_groups['small_cap']:
                return 'small_cap'
            else:
                return 'micro_cap'
        
        market_cap_data['cap_group'] = market_cap_data['total_mv'].apply(
            lambda x: get_cap_group(x * 10000)  # 万元转元
        )
        
        return market_cap_data
        
    def calc_group_stats(self, 
                        grouped_data: pd.DataFrame) -> pd.DataFrame:
        """计算各市值组统计指标"""
        stats_list = []
        
        for cap_group, group_df in grouped_data.groupby('cap_group'):
            stats = {
                'cap_group': cap_group,
                'stock_count': group_df['ts_code'].nunique(),
                'avg_market_cap': group_df['total_mv'].mean() * 10000,
                'mean_return': group_df['pct_chg'].mean() / 100,
                'std_return': group_df['pct_chg'].std() / 100,
                'sharpe_ratio': self.stats_calc.calc_sharpe_ratio(
                    group_df['pct_chg'] / 100
                ),
                'max_drawdown': self.stats_calc.calc_max_drawdown(
                    group_df['close']
                ),
                'skewness': stats.skew(group_df['pct_chg']),
                'kurtosis': stats.kurtosis(group_df['pct_chg']),
                'win_rate': (group_df['pct_chg'] > 0).mean(),
                'avg_turnover_rate': group_df['turnover_rate'].mean(),
            }
            stats_list.append(stats)
        
        return pd.DataFrame(stats_list)
        
    def analyze_cap_effect(self, 
                          market_cap_data: pd.DataFrame,
                          return_data: pd.DataFrame) -> pd.DataFrame:
        """分析市值效应"""
        # 合并数据
        merged = pd.merge(
            market_cap_data[['ts_code', 'trade_date', 'total_mv']],
            return_data[['ts_code', 'trade_date', 'pct_chg']],
            on=['ts_code', 'trade_date']
        )
        
        results = []
        
        # 按日期分组进行回归
        for date, date_df in merged.groupby('trade_date'):
            # 对数市值
            X = np.log(date_df['total_mv'] * 10000).values.reshape(-1, 1)
            y = (date_df['pct_chg'] / 100).values
            
            # 回归分析
            model = LinearRegression()
            model.fit(X, y)
            
            # 计算小盘股溢价
            small_cap_return = date_df[
                date_df['cap_group'] == 'small_cap'
            ]['pct_chg'].mean() / 100
            
            large_cap_return = date_df[
                date_df['cap_group'] == 'large_cap'
            ]['pct_chg'].mean() / 100
            
            results.append({
                'date': date,
                'cap_effect_coefficient': model.coef_[0],
                'intercept': model.intercept_,
                'small_cap_premium': small_cap_return - large_cap_return,
                'r_squared': model.score(X, y),
            })
        
        return pd.DataFrame(results)
        
    def analyze_time_series(self, 
                           cap_effect: pd.DataFrame) -> pd.DataFrame:
        """分析市值效应时间序列"""
        results = []
        
        for window in self.config['rolling_windows']:
            rolling_stats = cap_effect.rolling(window=window).agg({
                'cap_effect_coefficient': 'mean',
                'small_cap_premium': 'mean',
            })
            
            rolling_stats['window'] = window
            results.append(rolling_stats)
        
        return pd.concat(results, ignore_index=True)
        
    def analyze_interaction(self,
                          market_cap_data: pd.DataFrame,
                          industry_data: pd.DataFrame) -> pd.DataFrame:
        """分析市值与行业的交互效应"""
        # 合并市值和行业数据
        merged = pd.merge(
            market_cap_data,
            industry_data,
            on='ts_code'
        )
        
        # 双因子分组统计
        interaction_stats = merged.groupby(
            ['cap_group', 'industry']
        ).agg({
            'ts_code': 'count',
            'pct_chg': ['mean', 'std'],
        }).reset_index()
        
        return interaction_stats
        
    def analyze_transition(self,
                          market_cap_data: pd.DataFrame) -> pd.DataFrame:
        """分析市值迁移"""
        # 计算每只股票在不同时期的市值组
        stock_groups = market_cap_data.pivot_table(
            index='ts_code',
            columns='trade_date',
            values='cap_group',
            aggfunc='first'
        )
        
        # 计算迁移矩阵
        transitions = []
        
        for i in range(len(stock_groups.columns) - 1):
            from_group = stock_groups.iloc[:, i]
            to_group = stock_groups.iloc[:, i + 1]
            
            transition = pd.crosstab(
                from_group, 
                to_group, 
                normalize='index'
            )
            transitions.append(transition)
        
        # 平均迁移矩阵
        avg_transition = pd.concat(transitions).groupby(level=0).mean()
        
        return avg_transition
        
    def generate_plots(self, results: dict):
        """生成所有图表"""
        output_dir = Path(self.config['output_dir']) / 'plots'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 市值组收益率分布箱线图
        self._plot_cap_group_distribution(
            results['group_stats'],
            output_dir / 'cap_group_distribution.png'
        )
        
        # 2. 市值效应时间序列图
        self._plot_cap_effect_time_series(
            results['cap_effect'],
            output_dir / 'cap_effect_time_series.png'
        )
        
        # 3. 市值与收益率散点图
        self._plot_cap_return_scatter(
            results['cap_effect'],
            output_dir / 'cap_return_scatter.png'
        )
        
        # 4. 市值迁移热力图
        self._plot_transition_heatmap(
            results['transition'],
            output_dir / 'transition_heatmap.png'
        )
        
        self.logger.info(f"图表已保存到: {output_dir}")
        
    def save_results(self, results: dict):
        """保存分析结果"""
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存CSV文件
        results['group_stats'].to_csv(
            output_dir / 'cap_group_stats.csv', 
            index=False
        )
        results['cap_effect'].to_csv(
            output_dir / 'cap_effect.csv',
            index=False
        )
        results['time_series'].to_csv(
            output_dir / 'cap_time_series.csv',
            index=False
        )
        
        self.logger.info(f"结果已保存到: {output_dir}")
        
    def run(self):
        """运行完整分析流程"""
        self.logger.info("开始市值维度分析...")
        
        # 1. 加载数据
        data = self.load_data()
        
        # 2. 市值分组
        classified_data = self.classify_by_market_cap(data['market_cap'])
        
        # 3. 分组统计
        group_stats = self.calc_group_stats(classified_data)
        
        # 4. 市值效应分析
        cap_effect = self.analyze_cap_effect(
            classified_data,
            data['daily']
        )
        
        # 5. 时间序列分析
        time_series = self.analyze_time_series(cap_effect)
        
        # 6. 交互分析
        interaction = self.analyze_interaction(
            classified_data,
            data['industry']
        )
        
        # 7. 迁移分析
        transition = self.analyze_transition(classified_data)
        
        # 8. 生成图表
        results = {
            'group_stats': group_stats,
            'cap_effect': cap_effect,
            'time_series': time_series,
            'interaction': interaction,
            'transition': transition,
        }
        self.generate_plots(results)
        
        # 9. 保存结果
        self.save_results(results)
        
        self.logger.info("市值维度分析完成！")
        return results

def main():
    """主函数"""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description='市值维度分析')
    parser.add_argument('--config', type=str,
                       default='config/research_config.yaml',
                       help='配置文件路径')
    parser.add_argument('--start-date', type=str,
                       help='开始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str,
                       help='结束日期 (YYYYMMDD)')
    parser.add_argument('--output-dir', type=str,
                       default='results/market_cap_analysis',
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
    config['output_dir'] = args.output_dir
    
    # 运行分析
    analyzer = MarketCapAnalyzer(config)
    results = analyzer.run()
    
    print(f"\n分析完成！结果已保存到: {args.output_dir}")
    print(f"- 分组统计: {args.output_dir}/cap_group_stats.csv")
    print(f"- 市值效应: {args.output_dir}/cap_effect.csv")
    print(f"- 时间序列: {args.output_dir}/cap_time_series.csv")
    print(f"- 图表: {args.output_dir}/plots/")

if __name__ == '__main__':
    main()
```

---

## 关键算法

### 1. 市值效应回归
```python
def calc_cap_effect_regression(market_caps, returns):
    """
    计算市值效应回归系数
    
    模型: Return_i = α + β * log(MarketCap_i) + ε
    """
    from sklearn.linear_model import LinearRegression
    from scipy import stats as sp_stats
    
    # 对数市值
    log_caps = np.log(market_caps)
    
    # 回归
    X = log_caps.reshape(-1, 1)
    y = returns
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 计算t统计量和p值
    n = len(returns)
    y_pred = model.predict(X)
    residuals = y - y_pred
    mse = np.sum(residuals**2) / (n - 2)
    se = np.sqrt(mse / np.sum((log_caps - log_caps.mean())**2))
    t_stat = model.coef_[0] / se
    p_value = 2 * (1 - sp_stats.t.cdf(abs(t_stat), n - 2))
    
    return {
        'coefficient': model.coef_[0],
        'intercept': model.intercept_,
        't_statistic': t_stat,
        'p_value': p_value,
        'r_squared': model.score(X, y),
    }
```

### 2. SMB因子计算
```python
def calc_smb_factor(returns_by_cap):
    """
    计算Fama-French SMB (Small Minus Big) 因子
    """
    # 小盘股组合（市值最小的30%）
    small_cap_returns = returns_by_cap[
        returns_by_cap['cap_percentile'] <= 0.3
    ]['return'].mean()
    
    # 大盘股组合（市值最大的30%）
    big_cap_returns = returns_by_cap[
        returns_by_cap['cap_percentile'] >= 0.7
    ]['return'].mean()
    
    # SMB因子
    smb = small_cap_returns - big_cap_returns
    
    return smb
```

---

## 输出示例

### cap_group_stats.csv
```csv
cap_group,stock_count,avg_market_cap,mean_return,std_return,sharpe_ratio,max_drawdown,win_rate
mega_cap,50,250000000000,0.0005,0.0150,1.45,-0.28,0.54
large_cap,250,75000000000,0.0006,0.0180,1.35,-0.32,0.53
mid_cap,800,25000000000,0.0008,0.0220,1.25,-0.38,0.52
small_cap,1200,7500000000,0.0010,0.0280,1.15,-0.45,0.51
micro_cap,700,3000000000,0.0012,0.0350,1.05,-0.52,0.50
```

---

**文档版本**: v1.0  
**最后更新**: 2024-01-XX  
**状态**: 待实施