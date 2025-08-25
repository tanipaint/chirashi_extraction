"""
商品・価格ペア抽出モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T040のテストが失敗することを確認後、T041で実装します。
"""

import re
import json
import logging
import math
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import anthropic


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
    """商品・価格ペア抽出クラス（完全実装）"""
    
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
        try:
            # モックモードのチェック
            if self.config.get('use_mock', False):
                return self._extract_pairs_mock(ocr_result)
            
            # 入力検証
            if not ocr_result or 'text_annotations' not in ocr_result:
                raise ValueError('Invalid OCR result: missing text_annotations')
            
            text_annotations = ocr_result['text_annotations']
            if not text_annotations:
                return []
            
            # ステップ1: 価格パターンを検出
            price_candidates = self.detect_price_patterns(text_annotations)
            logging.info(f'Detected {len(price_candidates)} price candidates')
            
            # ステップ2: 商品名を識別
            product_candidates = self.identify_product_names(text_annotations)
            logging.info(f'Identified {len(product_candidates)} product candidates')
            
            # ステップ3: 空間的マッチング
            spatial_matches = self.match_spatial_relationships(product_candidates, price_candidates)
            logging.info(f'Found {len(spatial_matches)} spatial matches')
            
            # ステップ4: Anthropic APIによる高精度抽出（オプション）
            enhanced_pairs = []
            if self.config.get('use_llm', True) and spatial_matches:
                try:
                    enhanced_pairs = self._enhance_with_anthropic(ocr_result, spatial_matches)
                except Exception as e:
                    logging.warning(f'LLM enhancement failed, using spatial matches: {e}')
                    enhanced_pairs = spatial_matches
            else:
                enhanced_pairs = spatial_matches
            
            # ステップ5: 結果の整形と信頼度計算
            result_pairs = []
            for match in enhanced_pairs:
                if isinstance(match, tuple) and len(match) == 3:
                    product, price, distance = match
                else:
                    # LLMからの結果の場合
                    product = match.get('product', {})
                    price = match.get('price', {})
                    distance = match.get('spatial_distance', 0)
                
                # 信頼度スコアを計算
                extraction_data = {
                    'product_name': product.get('text', ''),
                    'price_incl_tax': price.get('price_value'),
                    'spatial_distance': distance,
                    'text_clarity': (product.get('confidence', 0.5) + price.get('confidence', 0.5)) / 2,
                    'pattern_match_confidence': price.get('confidence', 0.5)
                }
                
                confidence = self.calculate_confidence_score(extraction_data)
                
                # 最小信頼度閾値をクリア
                min_threshold = self.config.get('min_confidence_threshold', 0.4)
                if confidence >= min_threshold:
                    result_pairs.append({
                        'product': product.get('text', ''),
                        'price_incl_tax': price.get('price_value'),
                        'price_excl_tax': self._calculate_tax_exclusive_price(price.get('price_value')),
                        'unit': self._extract_unit(product.get('text', '')),
                        'confidence': confidence,
                        'spatial_distance': distance
                    })
            
            # 信頼度順でソート
            result_pairs.sort(key=lambda x: x['confidence'], reverse=True)
            
            logging.info(f'Successfully extracted {len(result_pairs)} product-price pairs')
            return result_pairs
            
        except Exception as e:
            logging.error(f'Product-price pair extraction error: {e}')
            raise ValueError(f'Failed to extract product-price pairs: {e}')
    
    def detect_price_patterns(self, text_annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        価格パターンを認識・抽出
        
        Args:
            text_annotations: テキストアノテーションのリスト
            
        Returns:
            価格パターン情報のリスト
        """
        try:
            # 価格パターンの正規表現定義
            patterns = {
                'tax_inclusive': r'(\d{1,5})\s*円\s*\(?税込\)?|税込\s*(\d{1,5})\s*円',
                'tax_exclusive': r'(\d{1,5})\s*円\s*\(?税抜\)?|税抜\s*(\d{1,5})\s*円',
                'simple_price': r'(\d{1,5})\s*円',
                'unit_price': r'(\d+)(g|kg|ml|L|本|個)当たり\s*(\d{1,5})\s*円|(\d{1,5})\s*円\s*/(\d+)(g|kg|ml|L|本|個)',
                'set_price': r'(\d+)\s*(本|個|袋|パック)\s*セット\s*(\d{1,5})\s*円|(\d{1,5})\s*円\s*\((\d+)\s*(本|個|袋|パック)\)',
                'discount_price': r'特価\s*(\d{1,5})\s*円|セール\s*(\d{1,5})\s*円|\d+%\s*OFF\s*(\d{1,5})\s*円'
            }
            
            price_candidates = []
            
            for annotation in text_annotations:
                text = annotation['text']
                bbox = annotation['bounding_box']
                
                # 各パターンでマッチを試行
                for pattern_type, pattern in patterns.items():
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    
                    for match in matches:
                        # マッチした価格を抽出
                        price_value = None
                        groups = match.groups()
                        
                        # グループから数値を抽出
                        for group in groups:
                            if group and group.isdigit():
                                price_value = int(group)
                                break
                        
                        if price_value and 10 <= price_value <= 999999:  # 価格の妥当性チェック
                            price_candidates.append({
                                'text': match.group(),
                                'price_value': price_value,
                                'pattern_type': pattern_type,
                                'bounding_box': bbox,
                                'confidence': self._calculate_pattern_confidence(pattern_type, text)
                            })
            
            return price_candidates
            
        except Exception as e:
            logging.error(f'Price pattern detection error: {e}')
            return []
    
    def identify_product_names(self, text_annotations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        商品名を識別・抽出
        
        Args:
            text_annotations: テキストアノテーションのリスト
            
        Returns:
            商品名候補のリスト
        """
        try:
            # 価格パターンを除外するための正規表現
            price_patterns = [
                r'\d+\s*円',
                r'税込|税抜',
                r'%\s*OFF',
                r'特価|セール',
                r'^\d+$',  # 数字のみ
                r'^[0-9%]+$'  # 数字と%のみ
            ]
            
            # 商品名として適さないパターン
            exclude_patterns = [
                r'^[0-9]+$',  # 数字のみ
                r'^[a-zA-Z0-9]+$',  # 英数字のみ
                r'^[\s\-_]+$',  # 記号のみ
                r'^.{1,2}$',  # 2文字以下
                r'^(月|火|水|木|金|土|日)$',  # 曜日
                r'^(AM|PM|\d{1,2}:\d{2})$',  # 時刻
                r'^(新聞|チラシ|広告|店名|店舗)$'  # 非商品単語
            ]
            
            product_candidates = []
            
            for annotation in text_annotations:
                text = annotation['text'].strip()
                bbox = annotation['bounding_box']
                
                # 価格パターンを含む場合はスキップ
                is_price = any(re.search(pattern, text, re.IGNORECASE) for pattern in price_patterns)
                if is_price:
                    continue
                
                # 除外パターンに該当する場合はスキップ
                is_excluded = any(re.search(pattern, text, re.IGNORECASE) for pattern in exclude_patterns)
                if is_excluded:
                    continue
                
                # 商品名としての信頼度を計算
                confidence = self._calculate_product_name_confidence(text)
                
                if confidence >= 0.3:  # 最小信頼度閾値
                    product_candidates.append({
                        'text': text,
                        'bounding_box': bbox,
                        'confidence': confidence,
                        'length': len(text),
                        'has_japanese': bool(re.search(r'[ひらがなカタカナ漢字]', text)),
                        'has_brand_indicators': self._has_brand_indicators(text)
                    })
            
            # 信頼度順でソート
            product_candidates.sort(key=lambda x: x['confidence'], reverse=True)
            
            return product_candidates
            
        except Exception as e:
            logging.error(f'Product name identification error: {e}')
            return []
    
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
        """
        try:
            if not product_candidates or not price_candidates:
                return []
            
            matches = []
            max_distance = self.config.get('max_spatial_distance', 150)
            
            for product in product_candidates:
                prod_bbox = product['bounding_box']
                prod_center = (
                    (prod_bbox[0] + prod_bbox[2]) / 2,
                    (prod_bbox[1] + prod_bbox[3]) / 2
                )
                
                best_price = None
                best_distance = float('inf')
                
                for price in price_candidates:
                    price_bbox = price['bounding_box']
                    price_center = (
                        (price_bbox[0] + price_bbox[2]) / 2,
                        (price_bbox[1] + price_bbox[3]) / 2
                    )
                    
                    # ユークリッド距離を計算
                    distance = math.sqrt(
                        (prod_center[0] - price_center[0]) ** 2 +
                        (prod_center[1] - price_center[1]) ** 2
                    )
                    
                    # レイアウトパターンによる重み調整
                    layout_weight = self._calculate_layout_weight(prod_bbox, price_bbox)
                    adjusted_distance = distance * layout_weight
                    
                    if adjusted_distance < max_distance and adjusted_distance < best_distance:
                        best_distance = adjusted_distance
                        best_price = price
                
                if best_price:
                    matches.append((product, best_price, best_distance))
            
            # 距離順でソート
            matches.sort(key=lambda x: x[2])
            
            return matches
            
        except Exception as e:
            logging.error(f'Spatial relationship matching error: {e}')
            return []
    
    def calculate_confidence_score(self, extraction_data: Dict[str, Any]) -> float:
        """
        抽出データの信頼度スコアを計算
        
        Args:
            extraction_data: 抽出データ辞書
            
        Returns:
            信頼度スコア（0.0-1.0）
        """
        try:
            score = 0.0
            weight_sum = 0.0
            
            # 商品名の品質 (重み: 0.25)
            if 'product_name' in extraction_data:
                product_name = extraction_data['product_name']
                if len(product_name) >= 3:
                    score += 0.8 * 0.25
                elif len(product_name) >= 2:
                    score += 0.6 * 0.25
                else:
                    score += 0.3 * 0.25
                weight_sum += 0.25
            
            # 価格の妥当性 (重み: 0.2)
            if 'price_incl_tax' in extraction_data:
                price = extraction_data['price_incl_tax']
                if 50 <= price <= 50000:  # 一般的な商品価格帯
                    score += 0.9 * 0.2
                elif 10 <= price <= 100000:
                    score += 0.7 * 0.2
                else:
                    score += 0.4 * 0.2
                weight_sum += 0.2
            
            # 空間距離 (重み: 0.15)
            if 'spatial_distance' in extraction_data:
                distance = extraction_data['spatial_distance']
                if distance <= 30:
                    score += 0.9 * 0.15
                elif distance <= 60:
                    score += 0.7 * 0.15
                elif distance <= 100:
                    score += 0.5 * 0.15
                else:
                    score += 0.2 * 0.15
                weight_sum += 0.15
            
            # テキスト品質 (重み: 0.2)
            if 'text_clarity' in extraction_data:
                clarity = extraction_data['text_clarity']
                score += clarity * 0.2
                weight_sum += 0.2
            
            # パターンマッチ信頼度 (重み: 0.2)
            if 'pattern_match_confidence' in extraction_data:
                pattern_conf = extraction_data['pattern_match_confidence']
                score += pattern_conf * 0.2
                weight_sum += 0.2
            
            # 重み付き平均を計算
            if weight_sum > 0:
                final_score = score / weight_sum
            else:
                final_score = 0.5  # デフォルト値
            
            return min(max(final_score, 0.0), 1.0)  # 0.0-1.0の範囲に制限
            
        except Exception as e:
            logging.error(f'Confidence score calculation error: {e}')
            return 0.5
    
    # ヘルパーメソッド
    def _calculate_pattern_confidence(self, pattern_type: str, text: str) -> float:
        """パターンタイプに基づく信頼度を計算"""
        confidence_map = {
            'tax_inclusive': 0.9,
            'tax_exclusive': 0.85,
            'simple_price': 0.7,
            'unit_price': 0.8,
            'set_price': 0.75,
            'discount_price': 0.8
        }
        
        base_confidence = confidence_map.get(pattern_type, 0.5)
        
        # テキストの明確性による調整
        if '税込' in text or '税抜' in text:
            base_confidence += 0.1
        if len(text) <= 10:  # 短いテキストは信頼度高
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _calculate_product_name_confidence(self, text: str) -> float:
        """商品名の信頼度を計算"""
        confidence = 0.5
        
        # 日本語を含む場合
        if re.search(r'[ひらがなカタカナ漢字]', text):
            confidence += 0.2
        
        # 適切な長さの場合
        if 3 <= len(text) <= 20:
            confidence += 0.15
        elif 2 <= len(text) <= 30:
            confidence += 0.1
        
        # ブランド名や商品カテゴリを含む場合
        if self._has_brand_indicators(text):
            confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _has_brand_indicators(self, text: str) -> bool:
        """ブランド名や商品カテゴリの指標を含むかチェック"""
        indicators = [
            'サントリー', 'コカ・コーラ', 'アサヒ', 'キリン', 'ポカリ',
            '天然水', 'ミネラル', 'ヨーグルト', 'パン', 'おにぎり',
            '2L', '500ml', '1L', 'kg', 'g', '本', '個', '袋'
        ]
        
        return any(indicator in text for indicator in indicators)
    
    def _calculate_layout_weight(self, prod_bbox: Tuple, price_bbox: Tuple) -> float:
        """レイアウトパターンによる重み調整"""
        prod_center_x = (prod_bbox[0] + prod_bbox[2]) / 2
        prod_center_y = (prod_bbox[1] + prod_bbox[3]) / 2
        price_center_x = (price_bbox[0] + price_bbox[2]) / 2
        price_center_y = (price_bbox[1] + price_bbox[3]) / 2
        
        dx = abs(prod_center_x - price_center_x)
        dy = abs(prod_center_y - price_center_y)
        
        # 横レイアウト（商品名の右に価格）
        if dx > dy and price_center_x > prod_center_x:
            return 0.8  # 重み軽減（距離を短く評価）
        
        # 縦レイアウト（商品名の下に価格）
        elif dy > dx and price_center_y > prod_center_y:
            return 0.9  # 重み軽減
        
        # その他のレイアウト
        return 1.2  # 重み増加（距離を長く評価）
    
    def _calculate_tax_exclusive_price(self, tax_inclusive_price: Optional[int]) -> Optional[int]:
        """税込価格から税抜価格を計算"""
        if tax_inclusive_price is None:
            return None
        
        # 日本の消費税10%で計算
        tax_rate = 0.10
        return int(tax_inclusive_price / (1 + tax_rate))
    
    def _extract_unit(self, product_text: str) -> Optional[str]:
        """商品テキストから単位を抽出"""
        unit_patterns = [
            r'(\d+)(本|個|袋|パック|缶|瓶)',
            r'(\d+)(g|kg|ml|L)',
            r'([0-9.]+)(L|ml)'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, product_text)
            if match:
                return match.group(1) + match.group(2)
        
        return None
    
    def _enhance_with_anthropic(self, ocr_result: Dict[str, Any], spatial_matches: List) -> List[Dict[str, Any]]:
        """Anthropic APIによる抽出結果の向上"""
        try:
            # Anthropic APIクライアントの初期化
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logging.warning('ANTHROPIC_API_KEY not found, skipping LLM enhancement')
                return spatial_matches
            
            client = anthropic.Anthropic(api_key=api_key)
            
            # プロンプトテンプレートの作成
            full_text = ocr_result.get('full_text', '')
            spatial_info = [{
                'product': match[0]['text'] if isinstance(match, tuple) else match.get('product', {}).get('text', ''),
                'price': match[1]['price_value'] if isinstance(match, tuple) else match.get('price', {}).get('price_value')
            } for match in spatial_matches[:5]]  # 上位5件のみ
            
            prompt = self._create_anthropic_prompt(full_text, spatial_info)
            
            # Claude APIを呼び出し
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # レスポンスをパース
            response_text = response.content[0].text
            enhanced_pairs = json.loads(response_text)
            
            logging.info(f'LLM enhanced {len(enhanced_pairs)} pairs')
            return enhanced_pairs.get('products', [])
            
        except Exception as e:
            logging.error(f'Anthropic API enhancement error: {e}')
            return spatial_matches
    
    def _create_anthropic_prompt(self, full_text: str, spatial_matches: List[Dict]) -> str:
        """Anthropic API用のプロンプトテンプレートを作成"""
        return f"""
あなたは日本のスーパーマーケットのチラシから商品名と価格を抽出する専門システムです。

以下のOCRテキストから商品名と価格のペアを正確に抽出してください：

OCRテキスト:
{full_text[:1000]}  # 長すぎる場合は切り詰め

初期マッチング結果（参考）:
{json.dumps(spatial_matches, ensure_ascii=False, indent=2)}

要求事項：
1. 商品名と価格が明確にペアとなっているもののみ抽出
2. 価格は円単位の数値で抽出
3. 税込・税抜の区別がある場合は税込価格を優先
4. 不明確なペアは除外
5. 結果はJSON形式で出力

出力形式：
{{
  "products": [
    {{
      "product": {{
        "text": "商品名"
      }},
      "price": {{
        "price_value": 価格（数値）
      }},
      "spatial_distance": 0
    }}
  ]
}}
"""
    
    def _extract_pairs_mock(self, ocr_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """モックモード用の商品・価格ペア抽出"""
        return [
            {
                'product': 'きゅうり3本',
                'price_incl_tax': 198,
                'price_excl_tax': 180,
                'unit': '3本',
                'confidence': 0.95,
                'spatial_distance': 15.5
            },
            {
                'product': 'サントリー天然水2L',
                'price_incl_tax': 98,
                'price_excl_tax': 89,
                'unit': '2L',
                'confidence': 0.92,
                'spatial_distance': 18.2
            }
        ]