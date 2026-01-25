import pandas as pd
import numpy as np
from scipy import stats
from typing import Union, Tuple

class StatisticsCalculator:
    """统计计算工具类"""
    
    @staticmethod
    def calc_returns(prices: Union[pd.Series, pd.DataFrame], method: str = 'log') -> Union[pd.Series, pd.DataFrame]:
        """计算收益率"""
        if method == 'log':
            return np.log(prices / prices.shift(1))
        else:
            return prices.pct_change(fill_method=None)
            
    @staticmethod
    def calc_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
        """计算年化夏普比率"""
        if returns.empty or returns.std() == 0:
            return np.nan
        excess_returns = returns - risk_free_rate / periods
        return np.sqrt(periods) * excess_returns.mean() / excess_returns.std()

    @staticmethod
    def calc_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
        """计算年化索提诺比率"""
        if returns.empty:
            return np.nan
        excess_returns = returns - risk_free_rate / periods
        downside = excess_returns[excess_returns < 0]
        if downside.empty or downside.std() == 0:
            return np.nan
        return np.sqrt(periods) * excess_returns.mean() / downside.std()

    @staticmethod
    def calc_calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        """计算卡玛比率"""
        if max_drawdown is None or max_drawdown == 0 or np.isnan(max_drawdown):
            return np.nan
        return annualized_return / abs(max_drawdown)

    @staticmethod
    def calc_profit_loss_ratio(returns: pd.Series) -> float:
        """计算盈亏比"""
        if returns.empty:
            return np.nan
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        if losses.empty:
            return np.nan
        return gains.mean() / abs(losses.mean()) if not gains.empty else 0.0
        
    @staticmethod
    def calc_max_drawdown(prices: pd.Series) -> float:
        """计算最大回撤"""
        if prices.empty:
            return np.nan
        cummax = prices.cummax()
        drawdown = (prices - cummax) / cummax
        return drawdown.min()
        
    @staticmethod
    def calc_basic_stats(returns: pd.Series, periods: int = 252) -> dict:
        """计算基础统计指标"""
        if returns.empty:
            return {}
        
        # 移除NaN
        clean_returns = returns.dropna()
        if clean_returns.empty:
            return {}
            
        return {
            'mean_return': clean_returns.mean(),
            'annualized_return': clean_returns.mean() * periods,
            'std_dev': clean_returns.std(),
            'annualized_volatility': clean_returns.std() * np.sqrt(periods),
            'skewness': stats.skew(clean_returns),
            'kurtosis': stats.kurtosis(clean_returns),
            'min_return': clean_returns.min(),
            'max_return': clean_returns.max(),
            'win_rate': (clean_returns > 0).mean()
        }
    
    @staticmethod
    def calc_rolling_stats(series: pd.Series, window: int) -> pd.DataFrame:
        """计算滚动统计量"""
        res = pd.DataFrame(index=series.index)
        res['mean'] = series.rolling(window=window).mean()
        res['std'] = series.rolling(window=window).std()
        return res

    @staticmethod
    def calc_beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """计算Beta系数"""
        # 对齐数据
        common_index = asset_returns.index.intersection(benchmark_returns.index)
        if len(common_index) < 2:
            return np.nan
            
        y = asset_returns.loc[common_index]
        x = benchmark_returns.loc[common_index]
        
        cov = np.cov(x, y)[0, 1]
        var = np.var(x)
        
        if var == 0:
            return np.nan
        return cov / var
