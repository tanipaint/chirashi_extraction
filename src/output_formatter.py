"""
出力整形モジュール

商品データをCSV/JSON形式で出力する機能を提供
"""

import json
import pandas as pd
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional


class OutputFormatter:
    """出力整形クラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化メソッド
        
        Args:
            config: 設定辞書（省略可）
        """
        self.config = config or {}
        
        # CSV出力カラムマッピング定義
        self.csv_columns = {
            "product": "商品名",
            "price_incl_tax": "税込価格", 
            "price_excl_tax": "税抜価格",
            "unit": "単位",
            "category": "カテゴリ",
            "confidence": "信頼度"
        }

    def to_csv(self, data: List[Dict[str, Any]], output_path: str) -> bool:
        """
        データをCSV形式で出力する
        
        Args:
            data: 商品データのリスト
            output_path: 出力ファイルパス
            
        Returns:
            bool: 出力成功時True
        """
        try:
            logging.info(f"Starting CSV output to: {output_path}")
            
            # 空データの場合も空のCSVファイルを作成
            if not data:
                logging.info("Empty data provided, creating empty CSV file")
                empty_df = pd.DataFrame(columns=list(self.csv_columns.values()))
                empty_df.to_csv(output_path, index=False, encoding='utf-8')
                return True
            
            # DataFrameに変換
            df = pd.DataFrame(data)
            
            # カラム名を日本語に変換
            df_renamed = pd.DataFrame()
            for eng_col, jp_col in self.csv_columns.items():
                if eng_col in df.columns:
                    df_renamed[jp_col] = df[eng_col]
                else:
                    # 欠損カラムはNaNで埋める
                    df_renamed[jp_col] = None
            
            # 出力ディレクトリが存在しない場合は作成（ルートディレクトリの場合はスキップ）
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # CSV出力（UTF-8エンコーディング）
            df_renamed.to_csv(output_path, index=False, encoding='utf-8')
            
            logging.info(f"CSV output completed successfully: {len(data)} records")
            return True
            
        except Exception as e:
            logging.error(f"Error in CSV output: {e}")
            raise

    def to_json(self, data: List[Dict[str, Any]], output_path: str) -> bool:
        """
        データをJSON形式で出力する
        
        Args:
            data: 商品データのリスト
            output_path: 出力ファイルパス
            
        Returns:
            bool: 出力成功時True
        """
        try:
            logging.info(f"Starting JSON output to: {output_path}")
            
            # 出力ディレクトリが存在しない場合は作成（ルートディレクトリの場合はスキップ）
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # JSON出力（UTF-8エンコーディング、日本語文字を適切に処理）
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"JSON output completed successfully: {len(data)} records")
            return True
            
        except Exception as e:
            logging.error(f"Error in JSON output: {e}")
            raise

    def generate_filename(self, format_type: str, prefix: str = "chirashi_result") -> str:
        """
        タイムスタンプ付きファイル名を生成する
        
        Args:
            format_type: ファイル形式（"csv" or "json"）
            prefix: ファイル名のプレフィックス
            
        Returns:
            str: 生成されたファイル名
            
        Raises:
            ValueError: サポートされていない形式の場合
        """
        try:
            # サポートされる形式をチェック
            if format_type.lower() not in ["csv", "json"]:
                raise ValueError(f"Unsupported format type: {format_type}")
            
            # タイムスタンプ生成（YYYYMMDD_HHMMSS形式）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # ファイル名生成
            filename = f"{prefix}_{timestamp}.{format_type.lower()}"
            
            logging.info(f"Generated filename: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Error in filename generation: {e}")
            raise