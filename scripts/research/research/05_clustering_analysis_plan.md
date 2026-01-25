# 聚类分析脚本实现方案

## 脚本信息
- **文件名**: `scripts/research/clustering_analysis.py`
- **优先级**: P1
- **预计开发时间**: 1-2天
- **依赖**: 统计计算模块、机器学习库 (scikit-learn)

---

## 功能概述

基于股票的收益率序列或统计特征进行无监督聚类，发现潜在的股票分组（不同于行业分类），识别相似模式的资产。

---

## 核心功能模块

### 1. 特征工程
**功能描述**: 构建用于聚类的特征矩阵

**特征类型**:
- **统计特征**: 均值、标准差、偏度、峰度、夏普比率
- **时间序列特征**: 过去N天的收益率序列（需标准化）
- **技术指标**: RSI, MACD, 波动率, 换手率
- **基本面特征**: (可选) PE, PB, 市值 (需归一化)

**预处理**:
- 去除缺失值
- 标准化 (Z-score)
- 降维 (PCA/t-SNE) - 用于可视化或高维数据处理

---

### 2. 聚类算法实现
**功能描述**: 应用多种聚类算法进行分组

**算法**:
- **K-Means**: 经典算法，适用于凸形簇
- **Hierarchical Clustering (层次聚类)**: 生成树状图，便于观察层级关系
- **DBSCAN**: 基于密度，能发现任意形状的簇，处理噪声
- **TimeSeriesKMeans (tslearn)**: 专门针对时间序列的聚类 (基于DTW距离)

**参数选择**:
- 肘部法则 (Elbow Method) 确定K值
- 轮廓系数 (Silhouette Score) 评估聚类质量

---

### 3. 聚类结果分析
**功能描述**: 解释聚类结果的含义

**分析内容**:
- **簇特征画像**: 每个簇的平均特征（如“高波动高收益簇”、“低估值大盘簇”）
- **行业重叠度**: 聚类结果与申万行业的重合程度 (Confusion Matrix)
- **市值分布**: 每个簇的市值构成

**可视化**:
- 降维散点图 (PCA/t-SNE)
- 雷达图 (展示簇中心特征)
- 树状图 (Dendrogram)

---

## 数据流程

```
[个股数据] ──> [特征提取] ──> [标准化] ──> [降维(可选)] ──> [聚类算法]
                                                            │
[行业/市值数据] ──────────────────────────────────────────> [结果解释] ──> [可视化]
```

## 代码结构

```python
class ClusterAnalyzer:
    def extract_features(self, data):
        """特征工程"""
        pass
        
    def run_clustering(self, features, method='kmeans', n_clusters=10):
        """执行聚类"""
        pass
        
    def evaluate_clusters(self, features, labels):
        """评估聚类效果"""
        pass
        
    def interpret_clusters(self, labels, metadata):
        """解释聚类结果(关联行业/市值)"""
        pass
```

## 输出示例

### cluster_labels.csv
```csv
ts_code,cluster_label
000001.SZ,3
000002.SZ,3
000003.SZ,1
...
```

### cluster_profiles.csv
```csv
cluster,avg_return,avg_volatility,avg_pe,main_industry
0,0.0005,0.015,10.5,银行
1,0.0012,0.035,45.2,电子
...
```
