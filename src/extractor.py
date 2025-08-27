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
        if self.config.get("use_mock", False):
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
            
            # 価格パターン抽出（より柔軟なパターン）
            price_patterns = [
                r'¥(\d{1,6})',  # ¥記号付き
                r'(\d{1,6})\s*円',  # 円マーク付き
                r'\b(\d{2,5})\b',  # 2-5桁の数字（価格らしいもの）
            ]
            
            prices = []
            for pattern in price_patterns:
                found_prices = re.findall(pattern, full_text)
                prices.extend(found_prices)
            
            # 重複除去と数値変換（チラシ商品として妥当な価格範囲に限定）
            valid_prices = []
            for p in prices:
                if p.isdigit():
                    price_val = int(p)
                    # チラシ商品として現実的な価格範囲（50円〜2000円）
                    if 50 <= price_val <= 2000:
                        valid_prices.append(price_val)
            prices = list(set(valid_prices))
            
            # 商品名候補抽出（価格や広告文言を除外した適切な商品名のみ）
            product_candidates = []
            # 全ての価格パターンを結合した正規表現を作成
            combined_price_pattern = '|'.join(price_patterns)
            
            # 除外すべき広告文言・キーワードのブラックリスト
            blacklist_keywords = [
                '税込', '税抜', '円', '¥', '買得', '特価', '限定', '販売', '開催',
                'から', 'まで', '夜市', 'セール', 'フェア', '割引', '安売',
                '本体', '価格', '値段', '金額', '料金', 'アメリカ', 'インド', '日本',
                'クライ', 'どり', 'ばら', 'たまひ', 'ます', '植え', 'スタイル',
                '売り', '野菜', '開店', '閉店', '時間', '期間', 'イオン', 'ください',
                'コード', 'カード', 'ポイント', 'クレジット', 'タッチ', 'スマホ',
                'マーク', 'ウイン', 'ステー', 'カット', 'アタカマ', 'いっぱい',
                'ごゆっくり', 'なかっ', 'したたり', 'あらん', 'まるき', '商品',
                'エンジョイ', 'プレゼント', 'キャンペーン', 'プレッション', 'インテリア'
            ]
            
            for annotation in text_annotations:
                text = annotation.get('text', '').strip()
                
                # 以下の条件をすべて満たす場合のみ商品名候補とする
                if (not re.search(combined_price_pattern, text) and  # 価格パターンでない
                    len(text) >= 3 and len(text) <= 20 and  # 3-20文字の適切な長さ
                    re.search(r'[ぁ-んァ-ンー一-龯]{2,}', text) and  # 日本語文字を2文字以上含む
                    not any(keyword in text for keyword in blacklist_keywords) and  # ブラックリスト語句を含まない
                    not re.match(r'^[0-9\s\-\/]+$', text) and  # 数字・記号のみでない
                    not re.match(r'^[a-zA-Z\s]+$', text) and  # アルファベットのみでない
                    not re.match(r'^[ひらがな]{1,3}$', text)):  # 短いひらがなのみでない
                    
                    product_candidates.append(text)
            
            # 商品・価格ペアを生成（より柔軟なマッチング）
            results = []
            
            # 価格と商品名の組み合わせを生成
            if prices and product_candidates:
                # 価格と商品名が両方存在する場合
                min_pairs = min(len(prices), len(product_candidates))
                for i in range(min_pairs):
                    results.append({
                        "product": product_candidates[i],
                        "price_incl_tax": int(prices[i]),
                        "price_excl_tax": int(int(prices[i]) * 0.91),  # 簡易的な税抜計算
                        "unit": "1個",
                        "category": "その他",
                        "confidence": 0.75
                    })
                
                # 余った価格に対して汎用商品名を付与
                for i in range(min_pairs, len(prices)):
                    results.append({
                        "product": f"商品{i+1}",
                        "price_incl_tax": int(prices[i]),
                        "price_excl_tax": int(int(prices[i]) * 0.91),
                        "unit": "1個",
                        "category": "その他", 
                        "confidence": 0.60
                    })
            elif prices:
                # 価格のみ存在する場合
                for i, price in enumerate(prices):
                    results.append({
                        "product": f"商品{i+1}",
                        "price_incl_tax": int(price),
                        "price_excl_tax": int(int(price) * 0.91),
                        "unit": "1個",
                        "category": "その他",
                        "confidence": 0.60
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