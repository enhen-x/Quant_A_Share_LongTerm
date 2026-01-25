import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import sys
import yaml

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts.utils.data_loader import DataLoader
from scripts.utils.statistics import StatisticsCalculator
from scripts.utils.visualization import Visualizer, get_chinese_font
from scripts.utils.logger import setup_logger, get_default_log_file

class IndustryAnalyzer:
    """行业维度分析器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.data_loader = DataLoader(data_root=str(project_root / "data"))
        self.stats_calc = StatisticsCalculator()
        self.visualizer = Visualizer()
        log_file = self.config.get("log_file", get_default_log_file("industry_analysis"))
        self.logger = setup_logger("industry_analysis", log_file=log_file)
        self.industry_name_map = self._load_industry_name_map()

    def _load_industry_name_map(self) -> Dict[str, str]:
        """加载行业代码-中文名称映射"""
        candidates = [
            project_root / "data" / "meta" / "industry_classification.parquet",
            project_root / "data" / "meta" / "sw_industry_l1.parquet",
            project_root / "data" / "meta" / "stock_industry_mapping.parquet",
        ]
        for path in candidates:
            self.logger.info(f"检查行业映射文件: {path} exists={path.exists()}")
            if not path.exists():
                continue
            try:
                df = pd.read_parquet(path)
            except Exception as exc:
                self.logger.warning(f"读取行业映射失败: {path} ({exc})")
                continue

            cols = set(df.columns)
            code_col = None
            name_col = None
            if {"index_code", "industry_name"}.issubset(cols):
                code_col, name_col = "index_code", "industry_name"
            elif {"industry_code", "industry_name"}.issubset(cols):
                code_col, name_col = "industry_code", "industry_name"
            elif {"code", "name"}.issubset(cols):
                code_col, name_col = "code", "name"

            if code_col and name_col:
                subset = df[[code_col, name_col]].dropna().drop_duplicates().copy()
                subset[code_col] = subset[code_col].astype(str).str.strip()
                subset[name_col] = subset[name_col].astype(str).str.strip()
                mapping = subset.set_index(code_col)[name_col].to_dict()
                # 兼容下划线版本（例如 801010_SI）
                mapping.update({k.replace(".", "_"): v for k, v in mapping.items() if "." in k})
                if mapping:
                    sample_keys = list(mapping.keys())[:5]
                    self.logger.info(f"加载行业名称映射: {path} ({len(mapping)} 条), 示例: {sample_keys}")
                    return mapping
        self.logger.warning("未找到行业代码-名称映射文件，将仅显示行业代码")
        return {}

    def _build_label_map(self, codes: List[str]) -> Dict[str, str]:
        """将行业代码映射为中文标签"""
        if not self.industry_name_map:
            return {code: code for code in codes}
        label_map = {}
        for code in codes:
            code_str = str(code).strip()
            code_key = code_str.replace("_", ".")
            name = self.industry_name_map.get(code_key) or self.industry_name_map.get(code_str)
            if not name and "." not in code_key:
                name = self.industry_name_map.get(f"{code_key}.SI")
            if name:
                label_map[code] = f"{name}({code})"
            else:
                label_map[code] = code
        return label_map
        
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """加载所有需要的数据"""
        self.logger.info("开始加载数据...")
        
        start_date = self.config['data_range'].get('start_date')
        end_date = self.config['data_range'].get('end_date')
        target_industries = self.config.get('industries', [])
        
        if not target_industries:
            target_industries = None
        
        data = {}
        
        # 1. 加载行业指数数据
        industry_data = self.data_loader.load_industry_data(
            industry_codes=target_industries,
            start_date=start_date,
            end_date=end_date
        )
        data['industry'] = self.data_loader.combine_prices(industry_data, col='close')
        
        # 2. 加载基准数据
        benchmark_code = self.config.get('benchmark', '000300.SH')
        benchmark_df = self.data_loader.load_benchmark_data(
            benchmark_code=benchmark_code,
            start_date=start_date,
            end_date=end_date
        )
        if not benchmark_df.empty:
            data['benchmark'] = benchmark_df.set_index('trade_date')['close']
        else:
            self.logger.warning("未能加载基准数据")
            
        # 3. 加载行业映射（如果需要行业内分析）
        # data['mapping'] = self.data_loader.load_stock_industry_mapping()
        
        self.logger.info("数据加载完成")
        return data
        
    def calc_industry_stats(self, industry_prices: pd.DataFrame, benchmark_prices: pd.Series = None) -> pd.DataFrame:
        """计算行业基础统计"""
        self.logger.info("计算行业统计指标...")

        returns = self.stats_calc.calc_returns(industry_prices)
        returns_simple = self.stats_calc.calc_returns(industry_prices, method='simple')
        weekly_returns = self._calc_period_returns(industry_prices, freq='W-FRI')
        monthly_returns = self._calc_period_returns(industry_prices, freq='ME')
        stats_list = []
        
        for col in returns.columns:
            series = returns[col]
            basic_stats = self.stats_calc.calc_basic_stats(series)
            sharpe = self.stats_calc.calc_sharpe_ratio(series)
            sortino = self.stats_calc.calc_sortino_ratio(series)
            max_dd = self.stats_calc.calc_max_drawdown(industry_prices[col])
            profit_loss = self.stats_calc.calc_profit_loss_ratio(series)
            calmar = self.stats_calc.calc_calmar_ratio(basic_stats.get('annualized_return', np.nan), max_dd)

            weekly_mean = weekly_returns[col].mean() if col in weekly_returns else np.nan
            weekly_std = weekly_returns[col].std() if col in weekly_returns else np.nan
            monthly_mean = monthly_returns[col].mean() if col in monthly_returns else np.nan
            monthly_std = monthly_returns[col].std() if col in monthly_returns else np.nan

            beta = np.nan
            if benchmark_prices is not None and not benchmark_prices.empty and col in returns_simple:
                benchmark_returns = self.stats_calc.calc_returns(benchmark_prices, method='simple')
                beta = self.stats_calc.calc_beta(returns_simple[col].dropna(), benchmark_returns.dropna())
            
            stats_dict = {
                'industry_code': col,
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino,
                'max_drawdown': max_dd,
                'profit_loss_ratio': profit_loss,
                'calmar_ratio': calmar,
                'mean_return_weekly': weekly_mean,
                'std_return_weekly': weekly_std,
                'mean_return_monthly': monthly_mean,
                'std_return_monthly': monthly_std,
                'beta': beta
            }
            stats_dict.update(basic_stats)
            stats_list.append(stats_dict)
            
        return pd.DataFrame(stats_list)

    def calc_annual_returns(self, industry_prices: pd.DataFrame) -> pd.DataFrame:
        """计算各行业年度收益率"""
        prices = industry_prices.copy()
        prices.index = pd.to_datetime(prices.index)

        def calc_year_return(series: pd.Series) -> float:
            series = series.dropna()
            if len(series) < 2:
                return np.nan
            return series.iloc[-1] / series.iloc[0] - 1

        annual_returns = prices.resample('YE').apply(calc_year_return)
        annual_returns.index = annual_returns.index.year
        return annual_returns.dropna(how='all')

    def _calc_period_returns(self, industry_prices: pd.DataFrame, freq: str) -> pd.DataFrame:
        """计算指定周期收益率"""
        prices = industry_prices.copy()
        prices.index = pd.to_datetime(prices.index)
        period_prices = prices.resample(freq).last()
        return period_prices.pct_change(fill_method=None)
        
    def analyze_rotation(self, industry_prices: pd.DataFrame) -> pd.DataFrame:
        """分析行业轮动 - 基于动量"""
        self.logger.info("分析行业轮动...")
        
        windows = self.config['rotation'].get('momentum_windows', [20, 60])
        top_n = self.config['rotation'].get('top_n', 3)
        
        rotation_records = []
        
        # 计算不同周期的动量
        for window in windows:
            momentum = industry_prices.pct_change(periods=window, fill_method=None)
            
            # 对每个时间点进行排名
            for date in momentum.index[window:]:
                date_momentum = momentum.loc[date].dropna()
                if date_momentum.empty:
                    continue
                    
                # 排序获取前N和后N
                sorted_momentum = date_momentum.sort_values(ascending=False)
                top_industries = sorted_momentum.head(top_n)
                bottom_industries = sorted_momentum.tail(top_n)
                
                record = {
                    'date': date,
                    'window': window,
                }
                
                # 记录前N
                for i, (ind, val) in enumerate(top_industries.items(), 1):
                    record[f'top_{i}'] = ind
                    record[f'top_{i}_momentum'] = val
                
                # 记录后N
                for i, (ind, val) in enumerate(bottom_industries.items(), 1):
                    record[f'bottom_{i}'] = ind
                    record[f'bottom_{i}_momentum'] = val
                
                rotation_records.append(record)
        
        rotation_df = pd.DataFrame(rotation_records)
        
        return rotation_df

    def calc_rotation_signals(self, industry_prices: pd.DataFrame) -> pd.DataFrame:
        """计算轮动信号与动量分位"""
        if industry_prices.empty:
            return pd.DataFrame()

        windows = self.config.get('rotation_heatmap_windows')
        if windows is None:
            windows = [self.config.get('rotation_heatmap_window', 60)]
        if isinstance(windows, int):
            windows = [windows]
        windows = [int(w) for w in windows]
        freq = self.config.get('rotation_heatmap_freq', 'ME')
        high = float(self.config.get('rotation_signal_high', 0.8))
        low = float(self.config.get('rotation_signal_low', 0.2))

        records = []
        for window in windows:
            momentum = industry_prices.pct_change(periods=window, fill_method=None)
            if freq:
                momentum.index = pd.to_datetime(momentum.index)
                momentum = momentum.resample(freq).last()

            rank = momentum.rank(axis=1, ascending=False, method='min')
            max_rank = rank.max(axis=1)
            denom = (max_rank - 1).replace(0, np.nan)
            percentile = 1 - (rank.sub(1, axis=0)).div(denom, axis=0)

            prev = percentile.shift(1)
            for date in percentile.index:
                curr_row = percentile.loc[date]
                prev_row = prev.loc[date]
                for code, value in curr_row.items():
                    prev_val = prev_row.get(code, np.nan)
                    signal = ''
                    if pd.notna(prev_val) and pd.notna(value):
                        if prev_val >= high and value <= low:
                            signal = 'strong_to_weak'
                        elif prev_val <= low and value >= high:
                            signal = 'weak_to_strong'
                        elif prev_val >= high and value >= high:
                            signal = 'persistent_strong'
                        elif prev_val <= low and value <= low:
                            signal = 'persistent_weak'
                    records.append({
                        'date': date,
                        'industry_code': code,
                        'momentum_window': window,
                        'percentile': value,
                        'prev_percentile': prev_val,
                        'signal': signal
                    })

        return pd.DataFrame(records)
        
    def calc_relative_strength(self, 
                               industry_prices: pd.DataFrame,
                               benchmark_prices: pd.Series) -> pd.DataFrame:
        """计算相对强弱"""
        self.logger.info("计算相对强弱...")
        
        # 对齐数据
        common_index = industry_prices.index.intersection(benchmark_prices.index)
        ind_prices = industry_prices.loc[common_index]
        bench_prices = benchmark_prices.loc[common_index]
        
        # 计算相对净值 (Industry / Benchmark)
        # 修正：直接计算价格比值，然后对每个行业单独归一化
        # 这样可以处理不同行业起始时间不同的情况
        
        # 1. 计算原始比率 (Price_Ind / Price_Bench)
        raw_ratio = ind_prices.div(bench_prices, axis=0)
        
        # 2. 对每一列进行归一化（除以该列第一个非空值）
        relative_strength = raw_ratio.copy()
        for col in relative_strength.columns:
            first_idx = relative_strength[col].first_valid_index()
            if first_idx is not None:
                relative_strength[col] = relative_strength[col] / relative_strength.loc[first_idx, col]
        
        return relative_strength

    def calc_relative_sharpe(self, relative_strength: pd.DataFrame) -> pd.Series:
        """计算相对强弱序列的日收益夏普率"""
        if relative_strength.empty:
            return pd.Series(dtype=float)

        rs_returns = self.stats_calc.calc_returns(relative_strength, method='simple')
        sharpe_map = {}
        for col in rs_returns.columns:
            sharpe_map[col] = self.stats_calc.calc_sharpe_ratio(rs_returns[col])
        return pd.Series(sharpe_map)

    def calc_relative_rank(self, industry_prices: pd.DataFrame, benchmark_prices: pd.Series) -> pd.DataFrame:
        """计算相对收益、排名与分位"""
        if industry_prices.empty or benchmark_prices is None or benchmark_prices.empty:
            return pd.DataFrame()

        common_index = industry_prices.index.intersection(benchmark_prices.index)
        ind_prices = industry_prices.loc[common_index]
        bench_prices = benchmark_prices.loc[common_index]

        ind_returns = self.stats_calc.calc_returns(ind_prices, method='simple')
        bench_returns = self.stats_calc.calc_returns(bench_prices, method='simple')
        relative_return = ind_returns.sub(bench_returns, axis=0)

        window = int(self.config.get('relative_rank_window', 20))
        if window > 1:
            rolling_relative_return = (1 + relative_return).rolling(window).apply(np.prod, raw=True) - 1
        else:
            rolling_relative_return = relative_return.copy()

        cumulative_relative_return = (1 + relative_return).cumprod() - 1
        rank = rolling_relative_return.rank(axis=1, ascending=False, method='min')
        max_rank = rank.max(axis=1)
        denom = (max_rank - 1).replace(0, np.nan)
        percentile = 1 - (rank.sub(1, axis=0)).div(denom, axis=0)

        records = []
        for date in relative_return.index:
            row = relative_return.loc[date]
            rolling_row = rolling_relative_return.loc[date]
            for code, value in row.items():
                records.append({
                    'date': date,
                    'industry_code': code,
                    'relative_return': value,
                    'rolling_relative_return': rolling_row.get(code, np.nan),
                    'rank': rank.loc[date, code],
                    'percentile': percentile.loc[date, code],
                    'cumulative_relative_return': cumulative_relative_return.loc[date, code],
                })
        return pd.DataFrame(records)
        
    def analyze_within_industry(self, industry_mapping: pd.DataFrame) -> pd.DataFrame:
        """分析行业内个股分布（可选，数据量较大）"""
        self.logger.info("分析行业内个股分布...")
        if industry_mapping.empty:
            self.logger.warning("行业映射为空，跳过行业内分析")
            return pd.DataFrame()

        code_col = None
        industry_col = None
        cols = set(industry_mapping.columns)
        if {"ts_code", "industry"}.issubset(cols):
            code_col, industry_col = "ts_code", "industry"
        elif {"ts_code", "industry_name"}.issubset(cols):
            code_col, industry_col = "ts_code", "industry_name"
        elif {"ts_code", "industry_code"}.issubset(cols):
            code_col, industry_col = "ts_code", "industry_code"

        if not code_col or not industry_col:
            self.logger.warning("行业映射字段不匹配，跳过行业内分析")
            return pd.DataFrame()

        min_stocks = int(self.config.get('within_industry', {}).get('min_stocks', 10))
        sample_n = int(self.config.get('within_industry', {}).get('sample_n', 50))

        results = []
        grouped = industry_mapping[[code_col, industry_col]].dropna().groupby(industry_col)
        for industry_name, group in grouped:
            codes = group[code_col].astype(str).unique().tolist()
            if len(codes) < min_stocks:
                continue
            if sample_n and len(codes) > sample_n:
                codes = codes[:sample_n]
            stock_data = self.data_loader.load_stock_daily(codes)
            if not stock_data:
                continue

            returns_list = []
            for _, df in stock_data.items():
                if df.empty or 'close' not in df.columns:
                    continue
                series = df.set_index('trade_date')['close']
                series_returns = self.stats_calc.calc_returns(series, method='simple').dropna()
                returns_list.append(series_returns)

            if not returns_list:
                continue

            all_returns = pd.concat(returns_list, axis=0)
            downside_returns = all_returns[all_returns < 0]
            upside_returns = all_returns[all_returns > 0]
            stats = {
                'industry': industry_name,
                'stock_count': len(codes),
                'mean_return': all_returns.mean(),
                'median_return': all_returns.median(),
                'std_return': all_returns.std(),
                'min_return': all_returns.min(),
                'max_return': all_returns.max(),
                'q25_return': all_returns.quantile(0.25),
                'q75_return': all_returns.quantile(0.75),
                'dispersion': all_returns.quantile(0.75) - all_returns.quantile(0.25),
                'concentration': (all_returns.median() / all_returns.mean()) if all_returns.mean() != 0 else np.nan,
                'win_rate': (all_returns > 0).mean(),
                'downside_std': downside_returns.std() if not downside_returns.empty else np.nan,
                'positive_mean_return': upside_returns.mean() if not upside_returns.empty else np.nan,
                'negative_mean_return': downside_returns.mean() if not downside_returns.empty else np.nan,
                'skew_return': all_returns.skew(),
                'kurtosis_return': all_returns.kurt()
            }
            results.append(stats)

        return pd.DataFrame(results)
        
    def test_significance(self, industry_prices: pd.DataFrame) -> dict:
        """显著性检验"""
        self.logger.info("进行显著性检验...")
        
        from scipy.stats import f_oneway, kruskal, ttest_ind
        from itertools import combinations

        def cohen_d(x: pd.Series, y: pd.Series) -> float:
            x = x.dropna()
            y = y.dropna()
            if len(x) < 2 or len(y) < 2:
                return np.nan
            nx, ny = len(x), len(y)
            vx, vy = x.var(ddof=1), y.var(ddof=1)
            pooled = ((nx - 1) * vx + (ny - 1) * vy) / (nx + ny - 2)
            if pooled == 0 or np.isnan(pooled):
                return np.nan
            return (x.mean() - y.mean()) / np.sqrt(pooled)

        def bh_adjust(pvals: List[float]) -> List[float]:
            pvals = np.array(pvals, dtype=float)
            n = len(pvals)
            order = np.argsort(pvals)
            ranked = pvals[order]
            qvals = np.empty(n, dtype=float)
            prev = 1.0
            for i in range(n - 1, -1, -1):
                rank = i + 1
                q = ranked[i] * n / rank
                prev = min(prev, q)
                qvals[i] = prev
            result = np.empty(n, dtype=float)
            result[order] = np.clip(qvals, 0, 1)
            return result.tolist()
        
        # 计算收益率
        returns = self.stats_calc.calc_returns(industry_prices, method='simple')
        
        # 准备数据：每个行业的收益率序列
        industry_returns_list = [returns[col].dropna() for col in returns.columns]
        industry_codes = returns.columns.tolist()
        
        results = {}
        
        # 1. ANOVA检验
        try:
            f_stat, p_value = f_oneway(*industry_returns_list)
            results['anova'] = {
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
            self.logger.info(f"ANOVA检验: F={f_stat:.4f}, p={p_value:.4f}")
        except Exception as e:
            self.logger.warning(f"ANOVA检验失败: {e}")
            results['anova'] = None
        
        # 2. Kruskal-Wallis检验（非参数）
        try:
            h_stat, p_value = kruskal(*industry_returns_list)
            results['kruskal'] = {
                'h_statistic': h_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
            self.logger.info(f"Kruskal-Wallis检验: H={h_stat:.4f}, p={p_value:.4f}")
        except Exception as e:
            self.logger.warning(f"Kruskal-Wallis检验失败: {e}")
            results['kruskal'] = None
        
        # 3. 两两比较（仅比较部分，避免过多组合）
        pairwise_comparisons = []
        n_industries = len(industry_codes)
        
        # 如果行业数量较少，进行全部两两比较
        if n_industries <= 10:
            pairs = list(combinations(range(n_industries), 2))
        else:
            # 如果行业太多，只比较部分（例如前5和后5）
            pairs = list(combinations(range(min(5, n_industries)), 2))
        
        for i, j in pairs[:20]:  # 最多比较20对
            try:
                t_stat, p_value = ttest_ind(
                    industry_returns_list[i], 
                    industry_returns_list[j],
                    equal_var=False  # Welch's t-test
                )
                effect = cohen_d(industry_returns_list[i], industry_returns_list[j])
                pairwise_comparisons.append({
                    'industry_1': industry_codes[i],
                    'industry_2': industry_codes[j],
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'cohens_d': effect,
                    'significant': p_value < 0.05
                })
            except Exception as e:
                self.logger.warning(f"两两比较失败 ({industry_codes[i]} vs {industry_codes[j]}): {e}")
        
        if pairwise_comparisons:
            qvals = bh_adjust([p['p_value'] for p in pairwise_comparisons])
            for comp, qval in zip(pairwise_comparisons, qvals):
                comp['p_value_fdr'] = qval
                comp['significant_fdr'] = qval < 0.05

        results['pairwise'] = pairwise_comparisons
        
        return results
        
    def generate_plots(self, results: dict, output_dir: Path):
        """生成所有图表"""
        self.logger.info("生成图表...")
        plots_dir = output_dir / 'plots'
        plots_dir.mkdir(parents=True, exist_ok=True)

        plot_top_n = int(self.config.get('plot_top_n', 8))
        plot_bottom_n = int(self.config.get('plot_bottom_n', 5))

        def order_by_rs(df: pd.DataFrame, rs_latest: pd.Series) -> pd.DataFrame:
            if rs_latest is None or rs_latest.empty or df.empty:
                return df
            order = rs_latest.sort_values(ascending=False).index.tolist()
            ordered_cols = [col for col in order if col in df.columns]
            remaining = [col for col in df.columns if col not in ordered_cols]
            return df[ordered_cols + remaining]

        rs_latest = None
        if 'relative_strength' in results and not results['relative_strength'].empty:
            rs_latest = results['relative_strength'].iloc[-1].dropna()

        relative_rank_df = None
        if 'relative_rank' in results and not results['relative_rank'].empty:
            relative_rank_df = results['relative_rank'].copy()
            relative_rank_df['date'] = pd.to_datetime(relative_rank_df['date'])
            relative_rank_df['industry_code'] = relative_rank_df['industry_code'].astype(str)
        
        # 1. 行业累计收益率对比
        if 'industry_prices' in results:
            industry_prices_plot = results['industry_prices']
            industry_prices_plot = order_by_rs(industry_prices_plot, rs_latest)
            price_label_map = self._build_label_map(industry_prices_plot.columns.tolist())
            industry_prices_plot = industry_prices_plot.rename(columns=price_label_map)
            self.visualizer.plot_time_series(
                industry_prices_plot,
                title='行业累计收益率',
                ylabel='Normalized Price',
                save_path=str(plots_dir / 'industry_returns.png'),
                legend_outside=True,
                legend_position='bottom',
                legend_ncol=6,
                legend_fontsize=7
            )

            # Top/Bottom 行业对比（按最新值排序）
            if not results['industry_prices'].empty:
                latest = results['industry_prices'].iloc[-1].dropna()
                if not latest.empty:
                    top_codes = latest.sort_values(ascending=False).head(plot_top_n).index
                    bottom_codes = latest.sort_values(ascending=True).head(plot_bottom_n).index
                    focus_codes = list(top_codes) + [c for c in bottom_codes if c not in top_codes]
                    focus_df = results['industry_prices'][focus_codes]
                    focus_df = order_by_rs(focus_df, rs_latest)
                    focus_df = focus_df.rename(columns=price_label_map)
                    self.visualizer.plot_time_series(
                        focus_df,
                        title=f'行业累计收益率 Top {len(top_codes)} / Bottom {len(bottom_codes)}',
                        ylabel='Normalized Price',
                        save_path=str(plots_dir / 'industry_returns_top_bottom.png'),
                        legend_outside=True,
                        legend_position='bottom',
                        legend_ncol=6,
                        legend_fontsize=7
                    )
            
        # 2. 行业统计分布
        if 'stats' in results and not results['stats'].empty:
            stats_df = results['stats'].set_index('industry_code')
            stats_label_map = self._build_label_map(stats_df.index.tolist())
            stats_df = stats_df.rename(index=stats_label_map)
            if 'annual_returns' in results and not results['annual_returns'].empty:
                annual_returns = results['annual_returns']
                top_n = self.config.get('annual_return_plot_top_n', 8)
                mean_returns = annual_returns.mean().dropna()
                if not mean_returns.empty:
                    selected = mean_returns.sort_values(ascending=False).head(top_n).index
                    annual_label_map = self._build_label_map(selected.tolist())
                    plot_data = annual_returns[selected].rename(columns=annual_label_map)
                    self.visualizer.plot_grouped_bar(
                        plot_data,
                        title=f'行业年度收益率 (Top {len(selected)})',
                        xlabel='Year',
                        ylabel='Annual Return',
                        save_path=str(plots_dir / 'industry_annual_return.png'),
                        legend_outside=True,
                        legend_position='bottom',
                        legend_ncol=6,
                        legend_fontsize=7
                    )
                    # 热力图 + 排名条（按平均排名排序）
                    ranks = plot_data.rank(axis=1, ascending=False)
                    avg_rank = ranks.mean().sort_values()
                    sorted_cols = avg_rank.index
                    sorted_data = plot_data[sorted_cols]

                    heatmap_data = sorted_data.T
                    font_prop = get_chinese_font()
                    fig, (ax_heat, ax_bar) = plt.subplots(
                        1, 2, figsize=(14, 8),
                        gridspec_kw={'width_ratios': [4, 1], 'wspace': 0.05},
                        constrained_layout=True
                    )
                    sns.heatmap(
                        heatmap_data,
                        cmap='coolwarm',
                        center=0,
                        ax=ax_heat,
                        cbar=True
                    )
                    ax_heat.set_title(
                        f'行业年度收益率热力图 (Top {len(selected)})',
                        fontproperties=font_prop
                    )
                    ax_heat.set_xlabel('Year', fontproperties=font_prop)
                    ax_heat.set_ylabel('Industry', fontproperties=font_prop)

                    ax_bar.barh(avg_rank.index, avg_rank.values, color='steelblue', alpha=0.8)
                    ax_bar.invert_yaxis()
                    ax_bar.set_xlabel('平均排名(越小越好)', fontproperties=font_prop)
                    ax_bar.set_yticklabels([])
                    ax_bar.grid(axis='x', alpha=0.3)

                    plt.savefig(
                        plots_dir / 'industry_annual_return_heatmap_rank.png',
                        dpi=300,
                        bbox_inches='tight'
                    )
                    plt.close(fig)
                else:
                    self.visualizer.plot_bar(
                        stats_df['annualized_return'],
                        title='行业年化收益率',
                        ylabel='Annualized Return',
                        save_path=str(plots_dir / 'industry_annual_return.png')
                    )
            else:
                self.visualizer.plot_bar(
                    stats_df['annualized_return'],
                    title='行业年化收益率',
                    ylabel='Annualized Return',
                    save_path=str(plots_dir / 'industry_annual_return.png')
                )
            
            self.visualizer.plot_bar(
                stats_df['sharpe_ratio'].sort_values(ascending=False),
                title='行业夏普比率',
                ylabel='Sharpe Ratio',
                save_path=str(plots_dir / 'industry_sharpe.png')
            )

            if 'max_drawdown' in stats_df.columns:
                self.visualizer.plot_bar(
                    stats_df['max_drawdown'].sort_values(),
                    title='行业最大回撤',
                    ylabel='Max Drawdown',
                    save_path=str(plots_dir / 'industry_max_drawdown.png')
                )

            # 行业收益分布（小提琴图）
            distribution_top_n = int(self.config.get('distribution_plot_top_n', 10))
            if 'industry_prices' in results and not results['industry_prices'].empty:
                returns_simple = self.stats_calc.calc_returns(results['industry_prices'], method='simple')
                if not returns_simple.empty:
                    vol_rank = stats_df['annualized_volatility'].sort_values(ascending=False)
                    selected = vol_rank.head(distribution_top_n).index.tolist()
                    selected_cols = [code for code in results['industry_prices'].columns if stats_label_map.get(code, code) in selected]
                    if selected_cols:
                        plot_returns = returns_simple[selected_cols].dropna(how='all')
                        if not plot_returns.empty:
                            label_map = self._build_label_map(plot_returns.columns.tolist())
                            plot_returns = plot_returns.rename(columns=label_map)
                            plot_data = plot_returns.melt(var_name='Industry', value_name='Return')
                            font_prop = get_chinese_font()
                            plt.figure(figsize=(14, 6))
                            sns.violinplot(
                                data=plot_data,
                                x='Industry',
                                y='Return',
                                inner='quartile',
                                cut=0
                            )
                            plt.title('行业收益分布（波动Top）', fontproperties=font_prop)
                            plt.xlabel('Industry', fontproperties=font_prop)
                            plt.ylabel('Return', fontproperties=font_prop)
                            plt.xticks(rotation=45)
                            ax = plt.gca()
                            for label in ax.get_xticklabels():
                                label.set_fontproperties(font_prop)
                            for label in ax.get_yticklabels():
                                label.set_fontproperties(font_prop)
                            plt.grid(axis='y', alpha=0.3)
                            plt.savefig(plots_dir / 'industry_return_violin.png', dpi=300, bbox_inches='tight')
                            plt.close()

        # 3. 相对强弱
        if 'relative_strength' in results and not results['relative_strength'].empty:
            relative_strength_plot = results['relative_strength']
            relative_strength_plot = order_by_rs(relative_strength_plot, rs_latest)
            rs_label_map = self._build_label_map(relative_strength_plot.columns.tolist())
            relative_strength_plot = relative_strength_plot.rename(columns=rs_label_map)

            self.visualizer.plot_time_series(
                relative_strength_plot,
                title='行业相对强弱 (vs 基准)',
                ylabel='Relative Strength',
                save_path=str(plots_dir / 'relative_strength.png'),
                legend_outside=True,
                legend_position='bottom',
                legend_ncol=6,
                legend_fontsize=7
            )

            # Top/Bottom 相对强弱
            latest_rs = results['relative_strength'].iloc[-1].dropna()
            if not latest_rs.empty:
                top_codes = latest_rs.sort_values(ascending=False).head(plot_top_n).index
                bottom_codes = latest_rs.sort_values(ascending=True).head(plot_bottom_n).index
                focus_codes = list(top_codes) + [c for c in bottom_codes if c not in top_codes]
                focus_df = results['relative_strength'][focus_codes]
                focus_df = order_by_rs(focus_df, rs_latest)
                focus_df = focus_df.rename(columns=rs_label_map)
                self.visualizer.plot_time_series(
                    focus_df,
                    title=f'行业相对强弱 Top {len(top_codes)} / Bottom {len(bottom_codes)}',
                    ylabel='Relative Strength',
                    save_path=str(plots_dir / 'relative_strength_top_bottom.png'),
                    legend_outside=True,
                    legend_position='bottom',
                    legend_ncol=6,
                    legend_fontsize=7
                )

        # 3.1 相对收益与累计相对收益
        if relative_rank_df is not None and not relative_rank_df.empty:
            def plot_relative_series(pivot: pd.DataFrame, title: str, ylabel: str, filename: str) -> None:
                if pivot.empty:
                    return
                pivot = pivot.sort_index()
                latest = pivot.iloc[-1].dropna()
                if latest.empty:
                    return
                top_codes = latest.sort_values(ascending=False).head(plot_top_n).index
                bottom_codes = latest.sort_values(ascending=True).head(plot_bottom_n).index
                focus_codes = list(top_codes) + [c for c in bottom_codes if c not in top_codes]
                focus_df = pivot[focus_codes]
                label_map = self._build_label_map(focus_df.columns.tolist())
                focus_df = focus_df.rename(columns=label_map)
                self.visualizer.plot_time_series(
                    focus_df,
                    title=title,
                    ylabel=ylabel,
                    save_path=str(plots_dir / filename),
                    legend_outside=True,
                    legend_position='bottom',
                    legend_ncol=6,
                    legend_fontsize=7
                )

            rolling_pivot = relative_rank_df.pivot(
                index='date',
                columns='industry_code',
                values='rolling_relative_return'
            )
            cumulative_pivot = relative_rank_df.pivot(
                index='date',
                columns='industry_code',
                values='cumulative_relative_return'
            )
            plot_relative_series(
                rolling_pivot,
                f'行业滚动相对收益 Top {plot_top_n} / Bottom {plot_bottom_n}',
                'Rolling Relative Return',
                'industry_relative_return.png'
            )
            plot_relative_series(
                cumulative_pivot,
                f'行业累计相对收益 Top {plot_top_n} / Bottom {plot_bottom_n}',
                'Cumulative Relative Return',
                'industry_cumulative_relative_return.png'
            )

        # 3.2 相对强弱排名/分位热力图
        if relative_rank_df is not None and not relative_rank_df.empty:
            pivot = relative_rank_df.pivot(index='date', columns='industry_code', values='percentile')
            pivot = pivot.resample('ME').last().dropna(how='all')
            if not pivot.empty:
                avg_percentile = pivot.mean().sort_values(ascending=False)
                heatmap_n = int(self.config.get('relative_rank_heatmap_top_n', 12))
                selected = avg_percentile.head(heatmap_n).index.tolist()
                pivot = pivot[selected]
                label_map = self._build_label_map(pivot.columns.tolist())
                pivot = pivot.rename(columns=label_map)
                font_prop = get_chinese_font()
                plt.figure(figsize=(14, 6))
                sns.heatmap(pivot.T, cmap='YlGnBu', vmin=0, vmax=1, cbar=True)
                window = int(self.config.get('relative_rank_window', 20))
                plt.title(f'行业相对强弱分位热力图（滚动{window}日）', fontproperties=font_prop)
                plt.xlabel('Date', fontproperties=font_prop)
                plt.ylabel('Industry', fontproperties=font_prop)
                ax = plt.gca()
                for label in ax.get_xticklabels():
                    label.set_fontproperties(font_prop)
                for label in ax.get_yticklabels():
                    label.set_fontproperties(font_prop)
                plt.savefig(plots_dir / 'industry_relative_rank_heatmap.png', dpi=300, bbox_inches='tight')
                plt.close()

        # 3.3 轮动动量热力图（多窗口）
        if 'rotation_signals' in results and not results['rotation_signals'].empty:
            rot_df = results['rotation_signals'].copy()
            rot_df['date'] = pd.to_datetime(rot_df['date'])
            rot_df['industry_code'] = rot_df['industry_code'].astype(str)
            window_values = sorted(rot_df['momentum_window'].dropna().unique().tolist())
            if not window_values:
                window_values = [None]
            for window in window_values:
                window_df = rot_df if window is None else rot_df[rot_df['momentum_window'] == window]
                pivot = window_df.pivot(index='date', columns='industry_code', values='percentile')
                pivot = pivot.dropna(how='all').sort_index()
                if pivot.empty:
                    continue
                avg_percentile = pivot.mean().sort_values(ascending=False)
                heatmap_n = int(self.config.get('rotation_heatmap_top_n', 12))
                selected = avg_percentile.head(heatmap_n).index.tolist()
                pivot = pivot[selected]
                label_map = self._build_label_map(pivot.columns.tolist())
                pivot = pivot.rename(columns=label_map)
                font_prop = get_chinese_font()
                plt.figure(figsize=(14, 6))
                sns.heatmap(pivot.T, cmap='coolwarm', vmin=0, vmax=1, cbar=True)
                title = '行业轮动动量分位热力图'
                suffixes = ['industry_rotation_heatmap.png']
                if window is not None:
                    title = f'行业轮动动量分位热力图（{int(window)}日）'
                    if len(window_values) > 1:
                        suffixes = [f'industry_rotation_heatmap_w{int(window)}.png']
                        if window == window_values[0]:
                            suffixes.append('industry_rotation_heatmap.png')
                plt.title(title, fontproperties=font_prop)
                plt.xlabel('Date', fontproperties=font_prop)
                plt.ylabel('Industry', fontproperties=font_prop)
                ax = plt.gca()
                for label in ax.get_xticklabels():
                    label.set_fontproperties(font_prop)
                for label in ax.get_yticklabels():
                    label.set_fontproperties(font_prop)
                for suffix in suffixes:
                    plt.savefig(plots_dir / suffix, dpi=300, bbox_inches='tight')
                plt.close()

        # 4. 行业相对夏普率
        if 'relative_sharpe' in results and not results['relative_sharpe'].empty:
            relative_sharpe = results['relative_sharpe'].dropna()
            if not relative_sharpe.empty:
                rs_sharpe_map = self._build_label_map(relative_sharpe.index.tolist())
                rs_sharpe_plot = relative_sharpe.rename(index=rs_sharpe_map)
                self.visualizer.plot_bar(
                    rs_sharpe_plot.sort_values(ascending=False),
                    title='行业相对夏普率（相对强弱日收益）',
                    ylabel='Relative Sharpe Ratio',
                    save_path=str(plots_dir / 'industry_relative_sharpe.png')
                )

        # 5. 行业内个股分布（可选）
        if 'within_industry' in results and not results['within_industry'].empty:
            within_df = results['within_industry'].copy()
            if 'industry' in within_df.columns:
                label_map = self._build_label_map(within_df['industry'].astype(str).tolist())
                within_df['industry_label'] = within_df['industry'].astype(str).map(label_map)
            else:
                within_df['industry_label'] = within_df.index.astype(str)

            if 'dispersion' in within_df.columns:
                plot_df = within_df.sort_values('dispersion', ascending=False)
                series = pd.Series(plot_df['dispersion'].values, index=plot_df['industry_label'])
                self.visualizer.plot_bar(
                    series,
                    title='行业内个股离散度',
                    ylabel='Dispersion (Q75-Q25)',
                    save_path=str(plots_dir / 'industry_within_dispersion.png')
                )

            if 'win_rate' in within_df.columns:
                plot_df = within_df.sort_values('win_rate', ascending=False)
                series = pd.Series(plot_df['win_rate'].values, index=plot_df['industry_label'])
                self.visualizer.plot_bar(
                    series,
                    title='行业内个股胜率',
                    ylabel='Win Rate',
                    save_path=str(plots_dir / 'industry_within_win_rate.png')
                )

            if 'concentration' in within_df.columns:
                plot_df = within_df.sort_values('concentration', ascending=False)
                series = pd.Series(plot_df['concentration'].values, index=plot_df['industry_label'])
                self.visualizer.plot_bar(
                    series,
                    title='行业内个股集中度',
                    ylabel='Concentration (Median/Mean)',
                    save_path=str(plots_dir / 'industry_within_concentration.png')
                )
            
    def save_results(self, results: dict, output_dir: Path):
        """保存分析结果"""
        import json
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if 'stats' in results:
            results['stats'].to_csv(output_dir / 'industry_stats.csv', index=False)
            
        if 'rotation' in results and not results['rotation'].empty:
            results['rotation'].to_csv(output_dir / 'industry_rotation.csv', index=False)

        if 'rotation_signals' in results and not results['rotation_signals'].empty:
            results['rotation_signals'].to_csv(output_dir / 'industry_rotation_signals.csv', index=False)
            
        if 'relative_strength' in results and not results['relative_strength'].empty:
            results['relative_strength'].to_csv(output_dir / 'industry_relative_strength.csv')

        if 'relative_sharpe' in results and not results['relative_sharpe'].empty:
            results['relative_sharpe'].to_csv(output_dir / 'industry_relative_sharpe.csv')

        if 'relative_rank' in results and not results['relative_rank'].empty:
            results['relative_rank'].to_csv(output_dir / 'industry_relative_rank.csv', index=False)

        if 'within_industry' in results and not results['within_industry'].empty:
            results['within_industry'].to_csv(output_dir / 'industry_within_industry.csv', index=False)
        
        # 保存显著性检验结果
        if 'significance' in results and results['significance']:
            sig_results = results['significance']
            
            # 保存整体检验结果
            summary = {}
            if sig_results.get('anova'):
                anova = sig_results['anova']
                summary['anova'] = {
                    'f_statistic': float(anova['f_statistic']),
                    'p_value': float(anova['p_value']),
                    'significant': bool(anova['significant'])
                }
            if sig_results.get('kruskal'):
                kruskal = sig_results['kruskal']
                summary['kruskal'] = {
                    'h_statistic': float(kruskal['h_statistic']),
                    'p_value': float(kruskal['p_value']),
                    'significant': bool(kruskal['significant'])
                }
            
            with open(output_dir / 'significance_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # 保存两两比较结果
            if sig_results.get('pairwise'):
                pairwise_df = pd.DataFrame(sig_results['pairwise'])
                pairwise_df.to_csv(output_dir / 'significance_pairwise.csv', index=False)
            
        self.logger.info(f"结果已保存到: {output_dir}")
        
    def run(self):
        """运行完整分析流程"""
        self.logger.info("开始行业维度分析...")
        
        # 1. 加载数据
        data = self.load_data()
        
        if data['industry'].empty:
            self.logger.error("未加载到行业数据，退出分析")
            return
            
        # 2. 基础统计
        industry_stats = self.calc_industry_stats(data['industry'], data.get('benchmark'))
        
        # 3. 轮动分析
        rotation_results = self.analyze_rotation(data['industry'])
        rotation_signals = self.calc_rotation_signals(data['industry'])

        # 3.5 年度收益率
        annual_returns = self.calc_annual_returns(data['industry'])
        
        # 4. 相对强弱
        relative_strength = pd.DataFrame()
        relative_sharpe = pd.Series(dtype=float)
        relative_rank = pd.DataFrame()
        if 'benchmark' in data:
            relative_strength = self.calc_relative_strength(
                data['industry'], 
                data['benchmark']
            )
            relative_sharpe = self.calc_relative_sharpe(relative_strength)
            relative_rank = self.calc_relative_rank(data['industry'], data['benchmark'])
        
        # 5. 显著性检验
        significance_results = self.test_significance(data['industry'])

        # 6. 行业内个股分析（可选）
        within_industry = pd.DataFrame()
        if self.config.get('within_industry', {}).get('enable', False):
            mapping = self.data_loader.load_stock_industry_mapping()
            within_industry = self.analyze_within_industry(mapping)
        
        # 结果汇总
        # 归一化：除以每个序列的第一个非空值
        normalized_prices = data['industry'].copy()
        for col in normalized_prices.columns:
            first_idx = normalized_prices[col].first_valid_index()
            if first_idx is not None:
                normalized_prices[col] = normalized_prices[col] / normalized_prices.loc[first_idx, col]

        results = {
            'industry_prices': normalized_prices,
            'stats': industry_stats,
            'rotation': rotation_results,
            'rotation_signals': rotation_signals,
            'annual_returns': annual_returns,
            'relative_strength': relative_strength,
            'relative_sharpe': relative_sharpe,
            'relative_rank': relative_rank,
            'within_industry': within_industry,
            'significance': significance_results
        }
        
        # 5. 输出
        output_dir = Path(self.config['output_dir'])
        self.generate_plots(results, output_dir)
        self.save_results(results, output_dir)

        # 自动生成摘要
        try:
            summary_script = project_root / "scripts" / "research" / "industry_auto_summary.py"
            output_file = project_root / "scripts" / "research" / "research" / "result.md"
            if summary_script.exists():
                import subprocess
                subprocess.run(
                    [sys.executable, str(summary_script),
                     "--results-dir", str(output_dir),
                     "--output-file", str(output_file)],
                    check=False
                )
                self.logger.info(f"已生成分析摘要: {output_file}")
            else:
                self.logger.warning("未找到自动摘要脚本，跳过摘要生成")
        except Exception as exc:
            self.logger.warning(f"自动摘要生成失败: {exc}")
        
        self.logger.info("行业维度分析完成！")
        return results

def main():
    import argparse
    
    import datetime
    
    today = datetime.datetime.now().strftime('%Y%m%d')
    parser = argparse.ArgumentParser(description='行业维度分析')
    parser.add_argument('--start-date', type=str, default='20100101', help='开始日期')
    parser.add_argument('--end-date', type=str, default=today, help='结束日期')
    parser.add_argument('--output-dir', type=str, default='results/industry_analysis', help='输出目录')
    
    args = parser.parse_args()
    
    # 默认配置
    config = {
        'data_range': {
            'start_date': args.start_date,
            'end_date': args.end_date
        },
        'output_dir': args.output_dir,
        'benchmark': '000300.SH',
        'industries': [],  # 空列表表示加载所有行业
        'rotation': {
            'momentum_windows': [20, 60],
            'top_n': 3
        },
        'rotation_heatmap_windows': [20, 60],
        'rotation_heatmap_window': 60,
        'rotation_heatmap_freq': 'ME',
        'rotation_signal_high': 0.8,
        'rotation_signal_low': 0.2,
        'distribution_plot_top_n': 10,
        'relative_rank_heatmap_top_n': 12,
        'rotation_heatmap_top_n': 12,
        'relative_rank_window': 60,
        'within_industry': {
            'enable': True,
            'min_stocks': 10,
            'sample_n': 50
        }
    }
    
    analyzer = IndustryAnalyzer(config)
    analyzer.run()

if __name__ == '__main__':
    main()
