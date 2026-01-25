# 波动率分析脚本实现方案

## 脚本信息
- **文件名**: `scripts/research/volatility_analysis.py`
- **优先级**: P0（最高优先级）
- **预计开发时间**: 1天
- **依赖**: 数据加载模块、统计计算模块、可视化模块

---

## 功能概述

分析股票收益率波动率的分布特征、时间序列特性、波动率聚集性，以及波动率与未来收益率的关系。

---

## 核心功能模块

### 1. 历史波动率计算
**功能描述**: 使用多种方法计算历史波动率

**计算方法**:
```python
# 1. 标准差法（最常用）
volatility_std = returns.rolling(window=20).std() * np.sqrt(252)

# 2. 帕金森波动率（使用高低价）
parkinson_vol = np.sqrt(
    (1 / (4 * np.log(2))) * 
    np.log(high / low) ** 2
) * np.sqrt(252)

# 3. Garman-Klass波动率（使用开高低收）
gk_vol = np.sqrt(
    0.5 * np.log(high / low) ** 2 - 
    (2 * np.log(2) - 1) * np.log(close / open) ** 2
) * np.sqrt(252)

# 4. Rogers-Satchell波动率
rs_vol = np.sqrt(
    np.log(high / close) * np.log(high / open) +
    np.log(low / close) * np.log(low / open)
) * np.sqrt(252)

# 5. Yang-Zhang波动率（综合方法）
yz_vol = calculate_yang_zhang_volatility(open, high, low, close)
```

**输出指标**:
```python
{
    'ts_code': '000001.SZ',
    'trade_date': '20240115',
    'vol_5d': 0.25,      # 5日波动率（年化）
    'vol_20d': 0.28,     # 20日波动率
    'vol_60d': 0.30,     # 60日波动率
    'vol_120d': 0.32,    # 120日波动率
    'vol_250d': 0.35,    # 250日波动率
    'vol_parkinson': 0.29,
    'vol_gk': 0.27,
    'vol_rs': 0.28,
    'vol_yz': 0.28,
}
```

---

### 2. 波动率分布分析
**功能描述**: 分析波动率的统计分布特征

**分析内容**:
```python
volatility_stats = {
    'mean': volatility.mean(),
    'median': volatility.median(),
    'std': volatility.std(),
    'min': volatility.min(),
    'max': volatility.max(),
    'q25': volatility.quantile(0.25),
    'q75': volatility.quantile(0.75),
    'skewness': stats.skew(volatility),
    'kurtosis': stats.kurtosis(volatility),
    'cv': volatility.std() / volatility.mean(),  # 变异系数
}

# 分组分析
volatility_groups = {
    'low': volatility < volatility.quantile(0.33),
    'medium': (volatility >= volatility.quantile(0.33)) & 
              (volatility < volatility.quantile(0.67)),
    'high': volatility >= volatility.quantile(0.67),
}
```

---

### 3. 波动率聚集性分析
**功能描述**: 分析波动率的时间序列特性（ARCH效应）

**分析方法**:
```python
# 1. 自相关分析
from statsmodels.tsa.stattools import acf, pacf

acf_values = acf(volatility, nlags=20)
pacf_values = pacf(volatility, nlags=20)

# 2. ARCH效应检验
from statsmodels.stats.diagnostic import het_arch

lm_stat, lm_pvalue, f_stat, f_pvalue = het_arch(returns, nlags=5)

# 3. GARCH模型拟合
from arch import arch_model

model = arch_model(returns, vol='Garch', p=1, q=1)
results = model.fit()

# 4. 波动率持续性指标
persistence = results.params['alpha[1]'] + results.params['beta[1]']
```

**输出指标**:
```python
{
    'acf_lag1': 0.85,        # 1阶自相关系数
    'acf_lag5': 0.65,        # 5阶自相关系数
    'arch_lm_stat': 125.5,   # ARCH-LM统计量
    'arch_pvalue': 0.001,    # p值
    'garch_alpha': 0.15,     # GARCH alpha参数
    'garch_beta': 0.80,      # GARCH beta参数
    'persistence': 0.95,     # 持续性
    'half_life': 13.5,       # 半衰期（天）
}
```

---

### 4. 波动率与收益率关系分析
**功能描述**: 研究波动率对未来收益率的预测能力

**分析维度**:
```python
# 1. 波动率分组的未来收益率
for group in ['low_vol', 'medium_vol', 'high_vol']:
    future_returns = calculate_forward_returns(
        stocks_in_group, 
        periods=[5, 20, 60]
    )

# 2. 波动率风险溢价
risk_premium = high_vol_return - low_vol_return

# 3. 回归分析
# Return_{t+1} = α + β * Volatility_t + ε
model = LinearRegression()
X = volatility.values.reshape(-1, 1)
y = future_returns.values
model.fit(X, y)

# 4. 非线性关系
# 使用多项式回归或分段回归
```

**输出格式**:
```python
{
    'vol_group': 'high_vol',
    'avg_volatility': 0.45,
    'forward_return_5d': 0.002,
    'forward_return_20d': 0.008,
    'forward_return_60d': 0.020,
    'sharpe_ratio': 0.85,
    'max_drawdown': -0.45,
}
```

---

### 5. 波动率择时策略回测
**功能描述**: 基于波动率的简单择时策略

**策略逻辑**:
```python
# 策略1: 低波动率策略
# 买入波动率最低的20%股票

# 策略2: 波动率突破策略
# 当波动率突破历史分位数时调整仓位

# 策略3: 波动率均值回归策略
# 当波动率偏离均值时反向操作

def backtest_low_volatility_strategy(volatility_data, return_data):
    """
    低波动率策略回测
    """
    results = []
    
    for date in trading_dates:
        # 选择低波动率股票
        low_vol_stocks = volatility_data[
            volatility_data['date'] == date
        ].nsmallest(100, 'volatility')['ts_code'].tolist()
        
        # 计算组合收益
        portfolio_return = return_data[
            (return_data['date'] == date) &
            (return_data['ts_code'].isin(low_vol_stocks))
        ]['return'].mean()
        
        results.append({
            'date': date,
            'portfolio_return': portfolio_return,
            'stock_count': len(low_vol_stocks),
        })
    
    return pd.DataFrame(results)
```

---

## 代码结构

```python
# scripts/research/volatility_analysis.py

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.stats.diagnostic import het_arch
from arch import arch_model

from utils.data_loader import DataLoader
from utils.statistics import StatisticsCalculator
from utils.visualization import Visualizer
from utils.logger import setup_logger

class VolatilityAnalyzer:
    """波动率分析器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.data_loader = DataLoader()
        self.stats_calc = StatisticsCalculator()
        self.visualizer = Visualizer()
        self.logger = setup_logger('volatility_analysis')
        
        # 波动率计算窗口
        self.windows = config.get('volatility_windows', [5, 20, 60, 120, 250])
        
    def calc_historical_volatility(self, 
                                   prices: pd.DataFrame,
                                   method: str = 'std') -> pd.DataFrame:
        """计算历史波动率"""
        if method == 'std':
            return self._calc_std_volatility(prices)
        elif method == 'parkinson':
            return self._calc_parkinson_volatility(prices)
        elif method == 'garman_klass':
            return self._calc_gk_volatility(prices)
        elif method == 'rogers_satchell':
            return self._calc_rs_volatility(prices)
        elif method == 'yang_zhang':
            return self._calc_yz_volatility(prices)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calc_std_volatility(self, prices: pd.DataFrame) -> pd.DataFrame:
        """标准差法计算波动率"""
        returns = prices['close'].pct_change()
        
        volatility = pd.DataFrame()
        for window in self.windows:
            vol = returns.rolling(window=window).std() * np.sqrt(252)
            volatility[f'vol_{window}d'] = vol
        
        return volatility
    
    def _calc_parkinson_volatility(self, prices: pd.DataFrame) -> pd.DataFrame:
        """帕金森波动率"""
        hl_ratio = np.log(prices['high'] / prices['low'])
        parkinson_vol = np.sqrt(
            (1 / (4 * np.log(2))) * hl_ratio ** 2
        ) * np.sqrt(252)
        
        return pd.DataFrame({'vol_parkinson': parkinson_vol})
    
    def analyze_distribution(self, 
                           volatility: pd.DataFrame) -> Dict:
        """分析波动率分布"""
        stats_dict = {}
        
        for col in volatility.columns:
            vol_series = volatility[col].dropna()
            
            stats_dict[col] = {
                'mean': vol_series.mean(),
                'median': vol_series.median(),
                'std': vol_series.std(),
                'min': vol_series.min(),
                'max': vol_series.max(),
                'q25': vol_series.quantile(0.25),
                'q75': vol_series.quantile(0.75),
                'skewness': stats.skew(vol_series),
                'kurtosis': stats.kurtosis(vol_series),
            }
        
        return stats_dict
    
    def analyze_clustering(self, 
                          returns: pd.Series) -> Dict:
        """分析波动率聚集性"""
        # 计算波动率
        volatility = returns.rolling(window=20).std()
        
        # 自相关分析
        acf_values = acf(volatility.dropna(), nlags=20)
        
        # ARCH效应检验
        lm_stat, lm_pvalue, f_stat, f_pvalue = het_arch(
            returns.dropna(), 
            nlags=5
        )
        
        # GARCH模型
        try:
            model = arch_model(returns.dropna() * 100, vol='Garch', p=1, q=1)
            results = model.fit(disp='off')
            
            garch_params = {
                'alpha': results.params.get('alpha[1]', np.nan),
                'beta': results.params.get('beta[1]', np.nan),
                'persistence': results.params.get('alpha[1]', 0) + 
                              results.params.get('beta[1]', 0),
            }
        except:
            garch_params = {
                'alpha': np.nan,
                'beta': np.nan,
                'persistence': np.nan,
            }
        
        return {
            'acf_lag1': acf_values[1],
            'acf_lag5': acf_values[5],
            'arch_lm_stat': lm_stat,
            'arch_pvalue': lm_pvalue,
            **garch_params,
        }
    
    def analyze_vol_return_relation(self,
                                   volatility: pd.DataFrame,
                                   returns: pd.DataFrame) -> pd.DataFrame:
        """分析波动率与收益率关系"""
        # 波动率分组
        vol_groups = pd.qcut(
            volatility['vol_20d'], 
            q=3, 
            labels=['low', 'medium', 'high']
        )
        
        results = []
        
        for group in ['low', 'medium', 'high']:
            group_mask = vol_groups == group
            
            # 计算未来收益率
            for period in [5, 20, 60]:
                future_return = returns['close'].pct_change(period).shift(-period)
                
                group_return = future_return[group_mask].mean()
                group_vol = volatility['vol_20d'][group_mask].mean()
                
                results.append({
                    'vol_group': group,
                    'period': period,
                    'avg_volatility': group_vol,
                    'forward_return': group_return,
                })
        
        return pd.DataFrame(results)
    
    def generate_plots(self, results: dict):
        """生成所有图表"""
        output_dir = Path(self.config['output_dir']) / 'plots'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 波动率分布直方图
        self._plot_volatility_distribution(
            results['volatility'],
            output_dir / 'volatility_distribution.png'
        )
        
        # 2. 波动率时间序列图
        self._plot_volatility_time_series(
            results['volatility'],
            output_dir / 'volatility_time_series.png'
        )
        
        # 3. 波动率自相关图
        self._plot_acf(
            results['clustering']['acf'],
            output_dir / 'volatility_acf.png'
        )
        
        # 4. 波动率-收益率关系图
        self._plot_vol_return_relation(
            results['vol_return_relation'],
            output_dir / 'vol_return_relation.png'
        )
        
        self.logger.info(f"图表已保存到: {output_dir}")
    
    def save_results(self, results: dict):
        """保存分析结果"""
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存波动率数据
        results['volatility'].to_csv(
            output_dir / 'volatility_stats.csv',
            index=False
        )
        
        # 保存波动率-收益率关系
        results['vol_return_relation'].to_csv(
            output_dir / 'volatility_return_relation.csv',
            index=False
        )
        
        self.logger.info(f"结果已保存到: {output_dir}")
    
    def run(self):
        """运行完整分析流程"""
        self.logger.info("开始波动率分析...")
        
        # 1. 加载数据
        data = self.data_loader.load_all_stocks_daily(
            self.config['start_date'],
            self.config['end_date']
        )
        
        # 2. 计算波动率
        volatility = self.calc_historical_volatility(
            data, 
            method=self.config.get('volatility_method', 'std')
        )
        
        # 3. 分布分析
        distribution = self.analyze_distribution(volatility)
        
        # 4. 聚集性分析
        clustering = self.analyze_clustering(data['close'].pct_change())
        
        # 5. 波动率-收益率关系
        vol_return_relation = self.analyze_vol_return_relation(
            volatility,
            data
        )
        
        # 6. 生成图表
        results = {
            'volatility': volatility,
            'distribution': distribution,
            'clustering': clustering,
            'vol_return_relation': vol_return_relation,
        }
        self.generate_plots(results)
        
        # 7. 保存结果
        self.save_results(results)
        
        self.logger.info("波动率分析完成！")
        return results

def main():
    """主函数"""
    import argparse
    import yaml
    
    parser = argparse.ArgumentParser(description='波动率分析')
    parser.add_argument('--config', type=str,
                       default='config/research_config.yaml')
    parser.add_argument('--method', type=str,
                       choices=['std', 'parkinson', 'garman_klass', 
                               'rogers_satchell', 'yang_zhang'],
                       default='std',
                       help='波动率计算方法')
    parser.add_argument('--output-dir', type=str,
                       default='results/volatility_analysis')
    
    args = parser.parse_args()
    
    # 加载配置
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['volatility_method'] = args.method
    config['output_dir'] = args.output_dir
    
    # 运行分析
    analyzer = VolatilityAnalyzer(config)
    results = analyzer.run()
    
    print(f"\n分析完成！结果已保存到: {args.output_dir}")

if __name__ == '__main__':
    main()
```

---

## 关键算法

### Yang-Zhang波动率
```python
def calculate_yang_zhang_volatility(open_prices, high_prices, 
                                    low_prices, close_prices, window=20):
    """
    Yang-Zhang波动率估计器
    综合了开盘跳空、日内波动和收盘波动
    """
    # 对数收益率
    log_ho = np.log(high_prices / open_prices)
    log_lo = np.log(low_prices / open_prices)
    log_co = np.log(close_prices / open_prices)
    
    log_oc = np.log(open_prices / close_prices.shift(1))
    log_cc = np.log(close_prices / close_prices.shift(1))
    
    # Rogers-Satchell波动率
    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    
    # 开盘跳空波动率
    open_vol = log_oc ** 2
    
    # 收盘波动率
    close_vol = log_cc ** 2
    
    # 权重参数
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    
    # Yang-Zhang波动率
    yz_vol = np.sqrt(
        open_vol.rolling(window).mean() +
        k * close_vol.rolling(window).mean() +
        (1 - k) * rs.rolling(window).mean()
    ) * np.sqrt(252)
    
    return yz_vol
```

---

## 输出示例

### volatility_stats.csv
```csv
ts_code,trade_date,vol_5d,vol_20d,vol_60d,vol_120d,vol_250d
000001.SZ,20240115,0.25,0.28,0.30,0.32,0.35
000001.SZ,20240116,0.26,0.28,0.30,0.32,0.35
...
```

### volatility_return_relation.csv
```csv
vol_group,period,avg_volatility,forward_return
low,5,0.18,0.002
low,20,0.18,0.008
low,60,0.18,0.025
medium,5,0.28,0.001
medium,20,0.28,0.005
medium,60,0.28,0.015
high,5,0.45,0.000
high,20,0.45,0.002
high,60,0.45,0.008
```

---

**文档版本**: v1.0  
**最后更新**: 2024-01-XX  
**状态**: 待实施