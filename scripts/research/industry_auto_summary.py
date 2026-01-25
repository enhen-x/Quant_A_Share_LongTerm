import argparse
from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime


def load_industry_name_map(project_root: Path) -> dict:
    candidates = [
        project_root / "data" / "meta" / "industry_classification.parquet",
        project_root / "data" / "meta" / "sw_industry_l1.parquet",
        project_root / "data" / "meta" / "stock_industry_mapping.parquet",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            df = pd.read_parquet(path)
        except Exception:
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
            mapping.update({k.replace(".", "_"): v for k, v in mapping.items() if "." in k})
            if mapping:
                return mapping
    return {}


def label_code(code: str, mapping: dict) -> str:
    code_str = str(code).strip()
    code_key = code_str.replace("_", ".")
    name = mapping.get(code_key) or mapping.get(code_str)
    if not name and "." not in code_key:
        name = mapping.get(f"{code_key}.SI")
    return f"{name}({code_str})" if name else code_str


def format_top_bottom(series: pd.Series, mapping: dict, top_n: int = 5, ascending: bool = False) -> str:
    if series is None or series.empty:
        return "无"
    series = series.dropna()
    if series.empty:
        return "无"
    sorted_series = series.sort_values(ascending=ascending)
    items = sorted_series.head(top_n) if ascending else sorted_series.head(top_n)
    return "、".join([f"{label_code(idx, mapping)}({val:.4f})" for idx, val in items.items()])


def format_list(values, mapping: dict, top_n: int = 5) -> str:
    if not values:
        return "无"
    return "、".join([label_code(code, mapping) for code in values[:top_n]])


def main():
    parser = argparse.ArgumentParser(description="行业分析自动结论摘要")
    parser.add_argument("--results-dir", type=str, default="results/industry_analysis")
    parser.add_argument("--output-file", type=str, default="scripts/research/research/result.md")
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / args.results_dir
    output_file = project_root / args.output_file

    mapping = load_industry_name_map(project_root)

    stats_path = results_dir / "industry_stats.csv"
    relative_sharpe_path = results_dir / "industry_relative_sharpe.csv"
    relative_rank_path = results_dir / "industry_relative_rank.csv"
    rotation_signals_path = results_dir / "industry_rotation_signals.csv"
    within_path = results_dir / "industry_within_industry.csv"
    significance_path = results_dir / "significance_summary.json"
    pairwise_path = results_dir / "significance_pairwise.csv"

    stats = pd.read_csv(stats_path) if stats_path.exists() else pd.DataFrame()
    rel_sharpe = pd.read_csv(relative_sharpe_path, index_col=0).iloc[:, 0] if relative_sharpe_path.exists() else pd.Series(dtype=float)
    rel_rank = pd.read_csv(relative_rank_path) if relative_rank_path.exists() else pd.DataFrame()
    rotation_signals = pd.read_csv(rotation_signals_path) if rotation_signals_path.exists() else pd.DataFrame()
    within_df = pd.read_csv(within_path) if within_path.exists() else pd.DataFrame()

    sig_summary = {}
    if significance_path.exists():
        try:
            sig_summary = json.loads(significance_path.read_text(encoding="utf-8"))
        except Exception:
            sig_summary = {}
    pairwise_df = pd.read_csv(pairwise_path) if pairwise_path.exists() else pd.DataFrame()

    lines = []
    lines.append("# 行业分析自动结论摘要")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    if not stats.empty:
        stats = stats.set_index("industry_code")
        lines.append("## 1. 收益与风险概览")
        if "annualized_return" in stats.columns:
            top_returns = stats["annualized_return"].sort_values(ascending=False).head(args.top_n)
            bottom_returns = stats["annualized_return"].sort_values(ascending=True).head(args.top_n)
            lines.append(f"- 年化收益Top：{format_top_bottom(top_returns, mapping, args.top_n)}")
            lines.append(f"- 年化收益Bottom：{format_top_bottom(bottom_returns, mapping, args.top_n, ascending=True)}")
        if "sharpe_ratio" in stats.columns:
            top_sharpe = stats["sharpe_ratio"].sort_values(ascending=False).head(args.top_n)
            lines.append(f"- 夏普Top：{format_top_bottom(top_sharpe, mapping, args.top_n)}")
        if "max_drawdown" in stats.columns:
            best_dd = stats["max_drawdown"].sort_values(ascending=False).head(args.top_n)
            worst_dd = stats["max_drawdown"].sort_values(ascending=True).head(args.top_n)
            lines.append(f"- 最大回撤最小：{format_top_bottom(best_dd, mapping, args.top_n)}")
            lines.append(f"- 最大回撤最大：{format_top_bottom(worst_dd, mapping, args.top_n, ascending=True)}")
        if "sortino_ratio" in stats.columns:
            top_sortino = stats["sortino_ratio"].sort_values(ascending=False).head(args.top_n)
            lines.append(f"- Sortino Top：{format_top_bottom(top_sortino, mapping, args.top_n)}")
        if "calmar_ratio" in stats.columns:
            top_calmar = stats["calmar_ratio"].sort_values(ascending=False).head(args.top_n)
            lines.append(f"- Calmar Top：{format_top_bottom(top_calmar, mapping, args.top_n)}")
        if "profit_loss_ratio" in stats.columns:
            top_pl = stats["profit_loss_ratio"].sort_values(ascending=False).head(args.top_n)
            lines.append(f"- 盈亏比Top：{format_top_bottom(top_pl, mapping, args.top_n)}")
        lines.append("")

    if rel_sharpe is not None and not rel_sharpe.empty:
        lines.append("## 2. 相对强弱风险调整")
        top_rel_sharpe = rel_sharpe.sort_values(ascending=False).head(args.top_n)
        lines.append(f"- 相对强弱日收益夏普Top：{format_top_bottom(top_rel_sharpe, mapping, args.top_n)}")
        lines.append("")

    def parse_dates(series: pd.Series, fmt: str = None) -> pd.Series:
        if fmt:
            parsed = pd.to_datetime(series.astype(str), format=fmt, errors='coerce')
            if parsed.isna().all():
                parsed = pd.to_datetime(series.astype(str), errors='coerce')
            return parsed
        return pd.to_datetime(series.astype(str), errors='coerce')

    if not rel_rank.empty:
        lines.append("## 3. 相对强弱排名")
        rel_rank['date'] = parse_dates(rel_rank['date'], fmt='%Y%m%d')
        latest_date = rel_rank['date'].max()
        latest = rel_rank[rel_rank['date'] == latest_date]
        if not latest.empty:
            top_rank = latest.sort_values('percentile', ascending=False).head(args.top_n)['industry_code'].tolist()
            bottom_rank = latest.sort_values('percentile', ascending=True).head(args.top_n)['industry_code'].tolist()
            lines.append(f"- 最新日期：{latest_date.strftime('%Y-%m-%d')}")
            lines.append(f"- 分位Top：{format_list(top_rank, mapping, args.top_n)}")
            lines.append(f"- 分位Bottom：{format_list(bottom_rank, mapping, args.top_n)}")
            if 'rolling_relative_return' in latest.columns:
                rolling_series = latest.set_index('industry_code')['rolling_relative_return'].dropna()
                if not rolling_series.empty:
                    top_roll = rolling_series.sort_values(ascending=False).head(args.top_n)
                    bottom_roll = rolling_series.sort_values(ascending=True).head(args.top_n)
                    lines.append(f"- 滚动相对收益Top：{format_top_bottom(top_roll, mapping, args.top_n)}")
                    lines.append(f"- 滚动相对收益Bottom：{format_top_bottom(bottom_roll, mapping, args.top_n, ascending=True)}")
            if 'cumulative_relative_return' in latest.columns:
                cum_series = latest.set_index('industry_code')['cumulative_relative_return'].dropna()
                if not cum_series.empty:
                    top_cum = cum_series.sort_values(ascending=False).head(args.top_n)
                    bottom_cum = cum_series.sort_values(ascending=True).head(args.top_n)
                    lines.append(f"- 累计相对收益Top：{format_top_bottom(top_cum, mapping, args.top_n)}")
                    lines.append(f"- 累计相对收益Bottom：{format_top_bottom(bottom_cum, mapping, args.top_n, ascending=True)}")
        lines.append("")

    if not rotation_signals.empty:
        lines.append("## 4. 轮动信号")
        rotation_signals['date'] = parse_dates(rotation_signals['date'])
        window_values = rotation_signals['momentum_window'].dropna().unique().tolist()
        if not window_values:
            window_values = [None]
        for window in sorted(window_values):
            window_df = rotation_signals if window is None else rotation_signals[rotation_signals['momentum_window'] == window]
            latest_date = window_df['date'].max()
            latest = window_df[window_df['date'] == latest_date]
            if latest.empty:
                continue
            label = f"{int(window)}日" if window is not None else "未标注"
            signals = {
                'strong_to_weak': latest[latest['signal'] == 'strong_to_weak']['industry_code'].tolist(),
                'weak_to_strong': latest[latest['signal'] == 'weak_to_strong']['industry_code'].tolist(),
                'persistent_strong': latest[latest['signal'] == 'persistent_strong']['industry_code'].tolist(),
                'persistent_weak': latest[latest['signal'] == 'persistent_weak']['industry_code'].tolist(),
            }
            lines.append(
                f"- 轮动窗口{label}（{latest_date.strftime('%Y-%m-%d')}）："
                f"强转弱{format_list(signals['strong_to_weak'], mapping, args.top_n)}；"
                f"弱转强{format_list(signals['weak_to_strong'], mapping, args.top_n)}；"
                f"持续强势{format_list(signals['persistent_strong'], mapping, args.top_n)}；"
                f"持续弱势{format_list(signals['persistent_weak'], mapping, args.top_n)}"
            )
        lines.append("")

    if not within_df.empty:
        lines.append("## 5. 行业内结构")
        if "dispersion" in within_df.columns:
            top_disp = within_df.sort_values("dispersion", ascending=False).head(args.top_n)
            items = "、".join([f"{label_code(row['industry'], mapping)}({row['dispersion']:.4f})" for _, row in top_disp.iterrows()])
            lines.append(f"- 离散度最高：{items}")
        if "win_rate" in within_df.columns:
            top_win = within_df.sort_values("win_rate", ascending=False).head(args.top_n)
            items = "、".join([f"{label_code(row['industry'], mapping)}({row['win_rate']:.2%})" for _, row in top_win.iterrows()])
            lines.append(f"- 胜率最高：{items}")
        if "concentration" in within_df.columns:
            top_conc = within_df.sort_values("concentration", ascending=False).head(args.top_n)
            items = "、".join([f"{label_code(row['industry'], mapping)}({row['concentration']:.4f})" for _, row in top_conc.iterrows()])
            lines.append(f"- 集中度最高：{items}")
        lines.append("")

    if sig_summary:
        lines.append("## 6. 显著性检验")
        anova = sig_summary.get("anova")
        kruskal = sig_summary.get("kruskal")
        if anova:
            lines.append(f"- ANOVA: p={anova.get('p_value', float('nan')):.4f}, 显著={anova.get('significant')}")
        if kruskal:
            lines.append(f"- Kruskal-Wallis: p={kruskal.get('p_value', float('nan')):.4f}, 显著={kruskal.get('significant')}")
        if not pairwise_df.empty and "significant_fdr" in pairwise_df.columns:
            sig_count = int(pairwise_df["significant_fdr"].sum())
            lines.append(f"- 两两比较（FDR校正）显著数量：{sig_count}")
        lines.append("- 解读：ANOVA 假设正态与方差齐性；Kruskal-Wallis 为非参数检验。若Kruskal显著而ANOVA不显著，可能说明分布非正态或存在异方差。")
        lines.append("- 注意：两两比较目前只抽样部分组合，结果用于提示方向，非完整穷举。")
        lines.append("")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"写入完成: {output_file}")


if __name__ == "__main__":
    main()
