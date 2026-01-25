import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union
from joblib import Parallel, delayed
from scripts.utils.logger import setup_logger

logger = setup_logger("data_loader")

class DataLoader:
    """数据加载工具类"""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.raw_market_dir = self.data_root / "raw" / "market" / "daily"
        self.raw_index_dir = self.data_root / "raw" / "index"
        self.raw_industry_dir = self.data_root / "raw" / "industry"
        self.meta_dir = self.data_root / "meta"
        
    def load_stock_industry_mapping(self) -> pd.DataFrame:
        """加载股票-行业映射数据"""
        filepath = self.meta_dir / "stock_industry_mapping.parquet"
        if not filepath.exists():
            logger.error(f"文件不存在: {filepath}")
            return pd.DataFrame()
        return pd.read_parquet(filepath)
        
    def load_industry_list(self) -> List[str]:
        """获取所有行业指数代码"""
        if not self.raw_industry_dir.exists():
            return []
        files = list(self.raw_industry_dir.glob("*.parquet"))
        return [f.stem for f in files]

    def _load_single_parquet(self, filepath: Path, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """加载单个Parquet文件并按日期过滤"""
        if not filepath.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(filepath)
            if 'trade_date' in df.columns:
                df['trade_date'] = df['trade_date'].astype(str)
                if start_date:
                    df = df[df['trade_date'] >= start_date]
                if end_date:
                    df = df[df['trade_date'] <= end_date]
            return df
        except Exception as e:
            logger.error(f"加载文件失败 {filepath}: {e}")
            return pd.DataFrame()

    def load_industry_data(self, 
                          industry_codes: Optional[List[str]] = None, 
                          start_date: str = None, 
                          end_date: str = None) -> Dict[str, pd.DataFrame]:
        """加载行业指数数据"""
        if industry_codes is None:
            industry_codes = self.load_industry_list()
            
        logger.info(f"正在加载 {len(industry_codes)} 个行业的指数数据...")
        
        def load_task(code):
            filepath = self.raw_industry_dir / f"{code}.parquet"
            df = self._load_single_parquet(filepath, start_date, end_date)
            return code, df

        # 并行加载
        results = Parallel(n_jobs=-1)(
            delayed(load_task)(code) for code in industry_codes
        )
        
        # 过滤掉空数据
        return {code: df for code, df in results if not df.empty}

    def load_benchmark_data(self, 
                           benchmark_code: str = "000300.SH", 
                           start_date: str = None, 
                           end_date: str = None) -> pd.DataFrame:
        """加载基准指数数据"""
        filepath = self.raw_index_dir / f"{benchmark_code}.parquet"
        return self._load_single_parquet(filepath, start_date, end_date)

    def load_stock_daily(self, 
                        ts_codes: List[str], 
                        start_date: str = None, 
                        end_date: str = None) -> Dict[str, pd.DataFrame]:
        """加载个股日线数据"""
        logger.info(f"正在加载 {len(ts_codes)} 只股票的日线数据...")
        
        def load_task(code):
            filepath = self.raw_market_dir / f"{code}.parquet"
            df = self._load_single_parquet(filepath, start_date, end_date)
            return code, df

        results = Parallel(n_jobs=-1)(
            delayed(load_task)(code) for code in ts_codes
        )
        
        return {code: df for code, df in results if not df.empty}

    def combine_prices(self, 
                      data_dict: Dict[str, pd.DataFrame], 
                      col: str = 'close') -> pd.DataFrame:
        """合并多个DataFrame的某一列，生成宽表"""
        combined = pd.DataFrame()
        for code, df in data_dict.items():
            if df.empty:
                continue
            temp = df.set_index('trade_date')[[col]].rename(columns={col: code})
            if combined.empty:
                combined = temp
            else:
                combined = combined.join(temp, how='outer')
        
        return combined.sort_index()
