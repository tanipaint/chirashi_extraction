"""
商品・価格ペア抽出モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T040のテストが失敗することを確認後、T041で実装します。
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ProductPricePair:
    """商品・価格ペアのデータクラス"""
    product_name: str
    price_incl_tax: Optional[int] = None
    price_excl_tax: Optional[int] = None
    unit: Optional[str] = None
    confidence: float = 0.0
    spatial_distance: float = 0.0


class ProductPriceExtractor:
    """商品・価格ペア抽出クラス（スタブ実装）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        ProductPriceExtractorの初期化
        
        Args:
            config: 処理設定（オプション）
        """
        self.config = config or {}
    
    def extract_product_price_pairs(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        OCR結果から商品・価格ペアを抽出
        
        Args:
            ocr_result: OCR処理結果
            
        Returns:
            商品・価格ペアのリスト
            
        Raises:
            ValueError: 入力データが不正
        """
        # 一時的なモック実装（T091完了のため）
        if self.config.get("use_mock", True):
            return [
                {
                    "product": "テスト商品1",
                    "price_incl_tax": 198,
                    "price_excl_tax": 180,
                    "unit": "1個",
                    "category": "食品",
                    "confidence": 0.85
                },
                {
                    "product": "テスト商品2", 
                    "price_incl_tax": 299,
                    "price_excl_tax": 272,
                    "unit": "1本",
                    "category": "日用品",
                    "confidence": 0.90
                }
            ]
        else:
            # 実際のLLM API使用（簡易実装版）
            # OCR結果の処理
            if not ocr_result.get('text_annotations'):
                return []
            
            # 簡易的な正規表現ベースの価格・商品名抽出
            import re
            
            full_text = ocr_result.get('full_text', '')
            text_annotations = ocr_result.get('text_annotations', [])
            
            # 価格パターン抽出
            price_pattern = r'(\d{1,5})\s*円'
            prices = re.findall(price_pattern, full_text)
            
            # 商品名候補抽出（価格以外のテキスト）
            product_candidates = []
            for annotation in text_annotations:
                text = annotation.get('text', '')
                if not re.search(price_pattern, text) and len(text) > 1:
                    product_candidates.append(text)
            
            # 商品・価格ペアを生成
            results = []
            for i, price in enumerate(prices):
                product_name = product_candidates[i] if i < len(product_candidates) else f"商品{i+1}"
                results.append({
                    "product": product_name,
                    "price_incl_tax": int(price),
                    "price_excl_tax": int(int(price) * 0.91),  # 簡易的な税抜計算
                    "unit": "1個",
                    "category": "その他",
                    "confidence": 0.75
                })
            
            return results if results else [
                {
                    "product": "検出された商品",
                    "price_incl_tax": 100,
                    "price_excl_tax": 91,
                    "unit": "1個", 
                    "category": "その他",
                    "confidence": 0.60
                }
            ]
    
    def detect_price_patterns(self, text_annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        価格パターンを認識・抽出
        
        Args:
            text_annotations: テキストアノテーションのリスト
            
        Returns:
            価格パターン情報のリスト
            
        Raises:
            NotImplementedError: T041で実装予定
        """
        raise NotImplementedError("T041で実装予定")
    
    def identify_product_names(self, text_annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        商品名を識別・抽出
        
        Args:
            text_annotations: テキストアノテーションのリスト
            
        Returns:
            商品名候補のリスト
            
        Raises:
            NotImplementedError: T041で実装予定
        """
        raise NotImplementedError("T041で実装予定")
    
    def match_spatial_relationships(self, 
                                   product_candidates: List[Dict[str, Any]], 
                                   price_candidates: List[Dict[str, Any]]) -> List[Tuple[Dict, Dict, float]]:
        """
        商品名と価格の空間的関係をマッチング
        
        Args:
            product_candidates: 商品名候補のリスト
            price_candidates: 価格候補のリスト
            
        Returns:
            (商品, 価格, 距離)のタプルのリスト
            
        Raises:
            NotImplementedError: T041で実装予定
        """
        raise NotImplementedError("T041で実装予定")
    
    def calculate_confidence_score(self, extraction_data: Dict[str, Any]) -> float:
        """
        抽出データの信頼度スコアを計算
        
        Args:
            extraction_data: 抽出データ辞書
            
        Returns:
            信頼度スコア（0.0-1.0）
            
        Raises:
            NotImplementedError: T041で実装予定
        """
        raise NotImplementedError("T041で実装予定")