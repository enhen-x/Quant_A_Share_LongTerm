import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Optional
import warnings

# 设置中文字体 - 添加更多备选字体
def setup_chinese_font():
    """配置中文字体"""
    import matplotlib.font_manager as fm
    import os
    
    # 候选字体列表（按优先级排序）
    # 注意：Matplotlib在Windows上通常可以直接使用字体名称
    chinese_fonts = [
        'Microsoft YaHei',      # 微软雅黑
        'SimHei',               # 黑体
        'SimSun',               # 宋体
        'KaiTi',                # 楷体
        'FangSong',             # 仿宋
        'DengXian',             # 等线
        'STSong',               # 华文宋体
        'STKaiti',              # 华文楷体
        'Arial Unicode MS',     # Arial Unicode (跨平台)
    ]
    
    # 优先尝试从字体文件直接加载，避免字体名未注册导致方块
    font_files = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\msyhl.ttc",
        r"C:\Windows\Fonts\msyhui.ttf",
        r"C:\Windows\Fonts\NotoSansSC-Regular.otf",
        r"C:\Windows\Fonts\NotoSerifSC-Regular.otf",
    ]

    loaded_fonts = []
    for font_file in font_files:
        if os.path.exists(font_file):
            try:
                fm.fontManager.addfont(font_file)
                font_name = fm.FontProperties(fname=font_file).get_name()
                loaded_fonts.append(font_name)
            except Exception:
                continue

    # 获取系统所有可用字体名称
    system_fonts = set([f.name for f in fm.fontManager.ttflist])
    
    selected_font = None
    candidate_fonts = []
    for font in loaded_fonts + chinese_fonts:
        if font in system_fonts and font not in candidate_fonts:
            candidate_fonts.append(font)
            if selected_font is None:
                selected_font = font
            
    if selected_font:
        print(f"Visualization: 已自动选择中文字体: {selected_font}")
        # Force the first font as the default family to avoid square glyphs.
        plt.rcParams['font.family'] = selected_font
        fallback_fonts = [selected_font] + [f for f in candidate_fonts if f != selected_font]
        plt.rcParams['font.sans-serif'] = fallback_fonts
        plt.rcParams['axes.unicode_minus'] = False
    else:
        # 如果通过名称找不到，尝试回退到默认列表设置
        print("Visualization: 未在系统字体列表中找到常用中文字体，尝试使用默认列表配置...")
        plt.rcParams['font.sans-serif'] = chinese_fonts
        plt.rcParams['axes.unicode_minus'] = False
    
    # 忽略字体警告
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*font.*')
    warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*')
    
    # 设置日志级别以减少字体警告
    import logging
    logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# 初始化字体配置
setup_chinese_font()

def get_chinese_font():
    """获取中文字体属性（优先使用系统字体文件）"""
    import os
    import matplotlib.font_manager as fm

    font_files = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\msyhl.ttc",
        r"C:\Windows\Fonts\msyhui.ttf",
        r"C:\Windows\Fonts\NotoSansSC-Regular.otf",
        r"C:\Windows\Fonts\NotoSerifSC-Regular.otf",
    ]
    for font_file in font_files:
        if os.path.exists(font_file):
            return fm.FontProperties(fname=font_file)
    return None

class Visualizer:
    """可视化工具类"""
    
    def __init__(self, style: str = 'seaborn-v0_8'):
        try:
            plt.style.use(style)
        except:
            plt.style.use('ggplot')
            
    def plot_distribution(self, 
                         data: pd.Series, 
                         title: str, 
                         save_path: Optional[str] = None):
        """绘制分布图 (直方图 + KDE)"""
        plt.figure(figsize=(10, 6))
        sns.histplot(data, kde=True, stat="density")
        font_prop = get_chinese_font()
        plt.title(title, fontproperties=font_prop)
        plt.xlabel('Value', fontproperties=font_prop)
        plt.ylabel('Density', fontproperties=font_prop)
        
        if save_path:
            self.save_figure(save_path)
        else:
            plt.show()
        plt.close()
        
    def plot_time_series(self, 
                        data: pd.DataFrame, 
                        title: str, 
                        ylabel: str = '',
                        save_path: Optional[str] = None,
                        legend_outside: bool = False,
                        legend_ncol: Optional[int] = None,
                        legend_fontsize: int = 9,
                        legend_position: str = 'right'):
        """绘制时间序列图"""
        font_prop = get_chinese_font()
        plt.figure(figsize=(12, 6))
        for col in data.columns:
            plt.plot(pd.to_datetime(data.index), data[col], label=col)
            
        plt.title(title, fontproperties=font_prop)
        plt.xlabel('Date', fontproperties=font_prop)
        plt.ylabel(ylabel, fontproperties=font_prop)
        plt.grid(True, alpha=0.3)

        if legend_outside:
            if legend_ncol is None:
                # Keep legend compact for many series.
                legend_ncol = min(4, max(1, int(np.ceil(len(data.columns) / 8))))
            if legend_position == 'bottom':
                plt.legend(
                    loc='upper center',
                    bbox_to_anchor=(0.5, -0.12),
                    borderaxespad=0.0,
                    ncol=legend_ncol,
                    fontsize=legend_fontsize,
                    prop=font_prop
                )
                plt.tight_layout(rect=[0, 0.12, 1, 1])
            else:
                plt.legend(
                    loc='center left',
                    bbox_to_anchor=(1.02, 0.5),
                    borderaxespad=0.0,
                    ncol=legend_ncol,
                    fontsize=legend_fontsize,
                    prop=font_prop
                )
                plt.tight_layout(rect=[0, 0, 0.85, 1])
        else:
            plt.legend(prop=font_prop)
        
        if save_path:
            self.save_figure(save_path)
        else:
            plt.show()
        plt.close()
        
    def plot_heatmap(self, 
                    data: pd.DataFrame, 
                    title: str, 
                    save_path: Optional[str] = None):
        """绘制热力图"""
        font_prop = get_chinese_font()
        plt.figure(figsize=(12, 10))
        sns.heatmap(data, cmap='coolwarm', center=0, annot=False)
        plt.title(title, fontproperties=font_prop)
        
        if save_path:
            self.save_figure(save_path)
        else:
            plt.show()
        plt.close()
        
    def plot_bar(self,
                data: pd.Series,
                title: str,
                xlabel: str = '',
                ylabel: str = '',
                save_path: Optional[str] = None):
        """绘制条形图"""
        plt.figure(figsize=(12, 6))
        data.plot(kind='bar')
        font_prop = get_chinese_font()
        plt.title(title, fontproperties=font_prop)
        plt.xlabel(xlabel, fontproperties=font_prop)
        plt.ylabel(ylabel, fontproperties=font_prop)
        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        ax = plt.gca()
        for label in ax.get_xticklabels():
            label.set_fontproperties(font_prop)
        for label in ax.get_yticklabels():
            label.set_fontproperties(font_prop)
        
        if save_path:
            self.save_figure(save_path)
        else:
            plt.show()
        plt.close()

    def plot_grouped_bar(self,
                        data: pd.DataFrame,
                        title: str,
                        xlabel: str = '',
                        ylabel: str = '',
                        save_path: Optional[str] = None,
                        legend_outside: bool = False,
                        legend_ncol: Optional[int] = None,
                        legend_fontsize: int = 9,
                        legend_position: str = 'right'):
        """绘制分组条形图"""
        font_prop = get_chinese_font()
        ax = data.plot(kind='bar', figsize=(12, 6))
        plt.title(title, fontproperties=font_prop)
        plt.xlabel(xlabel, fontproperties=font_prop)
        plt.ylabel(ylabel, fontproperties=font_prop)
        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        for label in ax.get_xticklabels():
            label.set_fontproperties(font_prop)
        for label in ax.get_yticklabels():
            label.set_fontproperties(font_prop)

        if legend_outside:
            if legend_ncol is None:
                legend_ncol = min(4, max(1, int(np.ceil(len(data.columns) / 6))))
            if legend_position == 'bottom':
                ax.legend(
                    loc='upper center',
                    bbox_to_anchor=(0.5, -0.12),
                    borderaxespad=0.0,
                    ncol=legend_ncol,
                    fontsize=legend_fontsize,
                    prop=font_prop
                )
                plt.tight_layout(rect=[0, 0.12, 1, 1])
            else:
                ax.legend(
                    loc='center left',
                    bbox_to_anchor=(1.02, 0.5),
                    borderaxespad=0.0,
                    ncol=legend_ncol,
                    fontsize=legend_fontsize,
                    prop=font_prop
                )
                plt.tight_layout(rect=[0, 0, 0.85, 1])
        else:
            ax.legend(fontsize=legend_fontsize, prop=font_prop)
        
        if save_path:
            self.save_figure(save_path)
        else:
            plt.show()
        plt.close()

    def save_figure(self, path: str):
        """保存图表"""
        # 确保目录存在
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(path, dpi=300, bbox_inches='tight')
