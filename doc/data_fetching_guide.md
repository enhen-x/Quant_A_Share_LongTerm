# 数据获取指南

本文档说明如何获取项目所需的补充数据。

## 📋 数据需求概览

### P0 - 必需数据（深度分析必备）

| 数据类型 | 用途 | 脚本 | 预计时间 |
|---------|------|------|----------|
| 股票市值数据 | 市值维度分析、流动性分析 | `fetch_daily_basic.py` | 30-60分钟 |
| 行业分类数据 | 行业维度分析 | `fetch_industry_data.py` | 5分钟 |
| 行业指数数据 | 行业相对偏移率计算 | `fetch_industry_data.py` | 10-20分钟 |

### P1 - 重要数据（增强分析深度）

| 数据类型 | 用途 | 脚本 | 预计时间 |
|---------|------|------|----------|
| 股票财务数据 | 基本面特征分析 | `fetch_financial_data.py` | 待实现 |
| 指数成分股 | 指数成分股分析 | `fetch_index_weight.py` | 待实现 |

### P3 - 衍生数据（需计算）

| 数据类型 | 用途 | 脚本 | 预计时间 |
|---------|------|------|----------|
| 滚动分布统计 | 时间一致性分析 | `calc_rolling_stats.py` | 待实现 |
| Beta系数 | 市场敏感度分析 | `calc_beta.py` | 待实现 |
| 相关性矩阵 | 聚类分析 | `calc_correlation.py` | 待实现 |

---

## 🚀 快速开始

### 方案A：一键获取（推荐）

```bash
# 1. 测试API连接
python scripts/data/test_fetch.py

# 2. 一键获取所有P0数据
python scripts/data/fetch_all_additional_data.py --priority P0

# 3. 验证数据完整性
python scripts/research/data_gap_analysis.py
```

### 方案B：分步获取

```bash
# 1. 测试API连接
python scripts/data/test_fetch.py

# 2. 获取市值数据
python scripts/data/fetch_daily_basic.py --mode update

# 3. 获取行业数据
python scripts/data/fetch_industry_data.py --task all

# 4. 验证数据完整性
python scripts/research/data_gap_analysis.py
```

---

## 📖 详细说明

### 1. 测试API连接

在获取大量数据前，先测试API是否正常：

```bash
python scripts/data/test_fetch.py
```

**测试内容**：
- ✓ 读取股票基础信息
- ✓ 读取交易日历
- ✓ 测试市值数据API
- ✓ 测试行业指数API

**预期输出**：
```
================================================================================
测试结果汇总
================================================================================
股票基础信息: ✓ 通过
交易日历: ✓ 通过
市值数据API: ✓ 通过
行业指数API: ✓ 通过

================================================================================
✓ 所有测试通过，可以开始获取数据
```

---

### 2. 获取市值数据

#### 2.1 增量更新（推荐）

自动检测现有数据，只更新缺失的日期：

```bash
python scripts/data/fetch_daily_basic.py --mode update
```

#### 2.2 按日期获取

指定日期范围获取：

```bash
python scripts/data/fetch_daily_basic.py --mode date --start_date 20100101 --end_date 20241231
```

#### 2.3 按股票获取

按股票代码并行获取（适合增量更新）：

```bash
python scripts/data/fetch_daily_basic.py --mode stock --start_date 20240101 --end_date 20241231
```

**数据字段**：
- `total_mv`: 总市值（万元）
- `circ_mv`: 流通市值（万元）
- `turnover_rate`: 换手率（%）
- `pe`: 市盈率（动态）
- `pe_ttm`: 市盈率（TTM）
- `pb`: 市净率
- `ps`: 市销率（动态）
- `ps_ttm`: 市销率（TTM）

**输出位置**：
- `data/meta/daily_basic/daily_basic_all.parquet` - 合并文件
- `data/meta/daily_basic/{ts_code}.parquet` - 按股票分组

**预计时间**：
- 增量更新（最近1个月）：5-10分钟
- 全量获取（2010-2024）：30-60分钟

---

### 3. 获取行业数据

#### 3.1 获取全部行业数据

```bash
python scripts/data/fetch_industry_data.py --task all
```

#### 3.2 只获取行业分类

```bash
python scripts/data/fetch_industry_data.py --task classification
```

#### 3.3 只获取行业指数

```bash
python scripts/data/fetch_industry_data.py --task indices --start_date 20100101
```

#### 3.4 只建立映射关系

```bash
python scripts/data/fetch_industry_data.py --task mapping
```

**行业分类**：
- 使用申万一级行业分类（28个行业）
- 包含：农林牧渔、采掘、化工、钢铁、有色金属、电子、家用电器、食品饮料等

**输出位置**：
- `data/meta/industry_classification.parquet` - 行业分类
- `data/meta/stock_industry_mapping.parquet` - 股票行业映射
- `data/raw/industry/{index_code}.parquet` - 行业指数（按行业）
- `data/raw/industry/industry_indices_all.parquet` - 行业指数（合并）

**预计时间**：
- 行业分类：1-2分钟
- 行业指数（2010-2024）：10-20分钟

---

### 4. 验证数据完整性

获取数据后，运行验证脚本检查：

```bash
python scripts/research/data_gap_analysis.py
```

**验证内容**：
- ✓ 基础数据（股票信息、交易日历）
- ✓ 行情数据（日线、指数）
- ✓ 偏移率数据
- ✓ 分布统计数据
- ✓ 市值数据
- ✓ 行业数据

---

## ⚠️ 注意事项

### 1. Tushare积分要求

| 接口 | 所需积分 | 说明 |
|------|---------|------|
| `daily_basic` | 120分 | 市值数据 |
| `index_daily` | 2000分 | 指数数据 |
| `stock_basic` | 0分 | 股票基础信息 |

**检查积分**：登录 [Tushare官网](https://tushare.pro) 查看

### 2. 限流说明

- **每分钟调用次数限制**：根据积分等级不同
- **建议**：使用脚本内置的并发控制，避免超限
- **如果遇到限流**：等待1分钟后重试

### 3. 数据存储空间

| 数据类型 | 预计大小 |
|---------|----------|
| 市值数据（2010-2024） | ~2GB |
| 行业指数（2010-2024） | ~50MB |
| 合计 | ~2.5GB |

**建议**：确保至少有5GB可用空间

### 4. 网络连接

- 需要稳定的网络连接
- 如果中断，可以重新运行脚本（支持断点续传）

---

## 🔧 故障排查

### 问题1：Token无效

**错误信息**：
```
HTTPError: 401 Client Error: Unauthorized
```

**解决方法**：
1. 检查 `config/main.yaml` 中的 `tushare.token`
2. 确认Token是否正确（登录Tushare官网查看）
3. 确认Token是否过期

### 问题2：积分不足

**错误信息**：
```
抱歉，您每分钟最多访问该接口X次
```

**解决方法**：
1. 等待1分钟后重试
2. 降低并发数（修改脚本中的 `MAX_WORKERS`）
3. 升级Tushare积分

### 问题3：数据为空

**错误信息**：
```
未获取到数据
```

**解决方法**：
1. 检查日期范围是否正确
2. 检查股票代码是否有效
3. 检查该日期是否为交易日

### 问题4：网络超时

**错误信息**：
```
Timeout Error
```

**解决方法**：
1. 检查网络连接
2. 增加超时时间（修改 `config/main.yaml` 中的 `tushare.timeout`）
3. 使用代理（如果在国外）

---

## 📊 数据质量检查

获取数据后，建议进行质量检查：

```python
import pandas as pd

# 检查市值数据
df = pd.read_parquet('data/meta/daily_basic/daily_basic_all.parquet')

print(f"总记录数: {len(df)}")
print(f"股票数量: {df['ts_code'].nunique()}")
print(f"日期范围: {df['trade_date'].min()} ~ {df['trade_date'].max()}")
print(f"\n缺失值统计:")
print(df.isnull().sum())
print(f"\n市值统计:")
print(df['total_mv'].describe())
```

---

## 🎯 下一步

数据获取完成后，可以进行：

1. **深度分析**：
   ```bash
   python scripts/research/industry_analysis.py
   python scripts/research/market_cap_analysis.py
   ```

2. **计算衍生数据**：
   ```bash
   python scripts/calculation/calc_rolling_stats.py
   python scripts/calculation/calc_beta.py
   ```

3. **生成分析报告**：
   ```bash
   python scripts/research/comprehensive_report.py
   ```

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件：`logs/fetch_*.log`
2. 运行测试脚本：`python scripts/data/test_fetch.py`
3. 查看Tushare文档：https://tushare.pro/document/2

---

## 📝 更新日志

- 2026-01-24: 创建数据获取指南
- 2026-01-24: 添加市值数据和行业数据获取脚本