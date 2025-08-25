"""
商品カテゴリ分類モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T050のテストが失敗することを確認後、T051で実装します。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class CategoryResult:
    """カテゴリ分類結果のデータクラス"""
    category: str
    confidence: float = 0.0
    method: str = "unknown"  # "keyword", "llm", "hybrid"


class ProductCategorizer:
    """商品カテゴリ分類クラス（スタブ実装）"""
    
    # カテゴリ定義
    CATEGORIES = [
        "食品",
        "日用品", 
        "医薬品・化粧品",
        "衣料品",
        "家電・雑貨",
        "その他"
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        ProductCategorizerの初期化
        
        Args:
            config: 処理設定（オプション）
        """
        self.config = config or {}
    
    def categorize_product(self, product_name: str) -> CategoryResult:
        """
        商品をカテゴリ分類する
        
        Args:
            product_name: 商品名
            
        Returns:
            カテゴリ分類結果
            
        Raises:
            ValueError: 入力データが不正
            NotImplementedError: T051で実装予定
        """
        raise NotImplementedError("T051で実装予定")
    
    def categorize_by_keywords(self, product_name: str) -> CategoryResult:
        """
        キーワードベースでカテゴリ分類
        
        Args:
            product_name: 商品名
            
        Returns:
            カテゴリ分類結果
            
        Raises:
            NotImplementedError: T051で実装予定
        """
        raise NotImplementedError("T051で実装予定")
    
    def categorize_by_llm(self, product_name: str) -> CategoryResult:
        """
        LLMベースでカテゴリ分類
        
        Args:
            product_name: 商品名
            
        Returns:
            カテゴリ分類結果
            
        Raises:
            NotImplementedError: T051で実装予定
        """
        raise NotImplementedError("T051で実装予定")
    
    def batch_categorize(self, product_names: List[str]) -> List[CategoryResult]:
        """
        複数商品の一括カテゴリ分類
        
        Args:
            product_names: 商品名のリスト
            
        Returns:
            カテゴリ分類結果のリスト
            
        Raises:
            NotImplementedError: T051で実装予定
        """
        raise NotImplementedError("T051で実装予定")