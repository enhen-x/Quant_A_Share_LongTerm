# Quant_A_Share_LongTerm

> 长线 A 股数据分析与选股系统

## 项目定位

面向**长线价值投资**的 A 股数据分析系统，与 `Quant_A_Share_V2.0`（短线量化交易）形成互补。

| 维度 | 短线项目 | 本项目 (长线) |
|------|----------|---------------|
| 投资周期 | 4-5 个交易日 | 3 个月 ~ 1 年+ |
| 核心逻辑 | 技术面 + 机器学习 | 基本面 + 宏观周期 + 行业趋势 |
| 换手频率 | 每周调仓 | 季度/半年调仓 |
| 数据源 | Baostock / Akshare | **Tushare Pro** |

## 核心功能

- 📊 **多维数据整合**: 基本面、宏观经济、行业产业链、市场情绪
- 💰 **估值模型**: DCF、PB-ROE、PEG 等经典估值方法
- 🔄 **周期研判**: 宏观经济周期、行业景气度分析
- 🎯 **因子选股**: 估值、质量、成长、动量、股息多因子
- 📈 **回测验证**: Backtrader 事件驱动回测框架
- 📑 **投资建议**: 可视化报告与决策解释

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 Tushare Token
# 编辑 config/main.yaml，填入你的 token

# 3. 更新数据
python scripts/data/update_all.py

# 4. 构建因子
python scripts/factor/build_factors.py

# 5. 运行选股
python scripts/strategy/run_screening.py
```

## 目录结构

```
├── config/          # 配置文件
├── data/            # 数据存储
├── src/             # 核心代码
│   ├── data_source/ # 数据源封装
│   ├── factors/     # 因子计算
│   ├── valuation/   # 估值模型
│   ├── cycle/       # 周期分析
│   ├── position/    # 仓位管理
│   ├── strategy/    # 策略逻辑
│   ├── backtest_bt/ # 回测框架
│   ├── advisor/     # 投资建议
│   └── explainer/   # 决策解释
├── scripts/         # 入口脚本
├── notebooks/       # 研究笔记
├── reports/         # 输出报告
└── figures/         # 图表输出
```

## 文档

详细架构设计请参考 [architecture_LongTerm.md](./architecture_LongTerm.md)

## License

MIT
