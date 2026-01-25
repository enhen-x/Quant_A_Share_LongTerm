# 综合分析报告脚本实现方案

## 脚本信息
- **文件名**: `scripts/research/comprehensive_report.py`
- **优先级**: P2
- **预计开发时间**: 2-3天
- **依赖**: 所有分析模块的结果、报告生成库 (Jinja2, WeasyPrint/Plotly)

---

## 功能概述

汇总上述所有专题分析的结果，生成一份结构化、可视化丰富的综合研究报告，提供宏观到微观的全景视角。

---

## 核心功能模块

### 1. 结果汇总与整合
**功能描述**: 从各个子模块的输出目录中读取CSV和图表文件

**数据源**:
- `results/industry_analysis/`
- `results/market_cap_analysis/`
- `results/volatility_analysis/`
- ...

**处理**:
- 检查结果完整性
- 提取关键摘要数据（如“本月表现最佳行业”、“当前市场平均相关性”）

---

### 2. 报告模板系统
**功能描述**: 定义报告的结构和样式

**技术栈**:
- **HTML/Jinja2**: 用于生成网页版报告，易于排版和交互
- **Markdown**: 用于生成简报
- **PDF**: 基于HTML转换，用于正式归档

**章节结构**:
1. **市场概览**: 关键指数表现、市场情绪指标
2. **行业透视**: 领涨/领跌行业、轮动信号
3. **风格分析**: 大小盘风格、价值/成长风格(如有)
4. **风险监控**: 波动率分析、相关性预警
5. **聚类发现**: 值得关注的股票群组
6. **投资建议**: 基于数据的自动生成建议

---

### 3. 交互式仪表板 (可选高级功能)
**功能描述**: 构建Web仪表板，允许用户动态筛选数据

**技术栈**: Plotly Dash / Streamlit

**功能**:
- 行业收益率的时间范围选择
- 个股相关性网络的缩放和查询
- 波动率分布的动态过滤

---

### 4. 自动摘要生成
**功能描述**: 基于规则或NLP生成文字解读

**逻辑示例**:
- IF `market_avg_corr > 0.6` THEN "市场系统性风险较高，建议降低仓位或分散资产类型"
- IF `small_cap_premium > 0` THEN "近期小盘股表现优于大盘股，存在市值下沉效应"

---

## 数据流程

```
[各模块Results] ──> [数据读取器] ──> [摘要生成器] ──> [模板引擎(Jinja2)] ──> [HTML报告]
                                                                      │
                                                                      └─> [PDF转换器] ──> [PDF报告]
```

## 代码结构

```python
class ReportGenerator:
    def load_all_results(self, root_dir):
        """加载所有分析结果"""
        pass
        
    def generate_summary_text(self, data):
        """生成文字摘要"""
        pass
        
    def render_html(self, data, template_path):
        """渲染HTML"""
        pass
        
    def export_pdf(self, html_content, output_path):
        """导出PDF"""
        pass
```

## 目录结构示例

```
scripts/research/templates/
├── base.html
├── styles.css
├── industry_section.html
└── ...

results/comprehensive_report/
├── report_20240101.html
├── report_20240101.pdf
└── assets/ (复制的图片)
```
