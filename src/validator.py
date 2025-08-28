"""
データ検証モジュール

TDD方式での完全実装（T061）
T060のテストを通すための完全実装。
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class ValidationResult:
    """検証結果のデータクラス"""
    is_valid: bool
    confidence_score: float = 0.0
    validation_errors: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class ProductValidator:
    """商品データ検証クラス（完全実装）"""
    
    # 価格制限定数
    MIN_PRICE = 1
    MAX_PRICE = 999999
    
    def __init__(self):
        """ProductValidatorの初期化"""
        pass
    
    def validate_product_data(self, product_data: Dict[str, Any]) -> ValidationResult:
        """
        商品データの総合検証
        
        Args:
            product_data: 検証対象の商品データ
            
        Returns:
            総合検証結果
        """
        try:
            print(f"DEBUG: バリデーション開始 - 商品: {product_data.get('product')}")
            validation_errors = []
            
            # 商品名検証
            product_name = product_data.get('product')
            name_result = self.validate_product_name(product_name)
            if not name_result.is_valid:
                validation_errors.append(f"商品名エラー: {name_result.error_message}")
            
            # 税込価格検証
            price_incl_tax = product_data.get('price_incl_tax')
            if price_incl_tax is not None:
                price_result = self.validate_price_range(price_incl_tax)
                if not price_result.is_valid:
                    validation_errors.append(f"税込価格エラー: {price_result.error_message}")
            
            # 税抜価格検証
            price_excl_tax = product_data.get('price_excl_tax')
            if price_excl_tax is not None:
                excl_price_result = self.validate_price_range(price_excl_tax)
                if not excl_price_result.is_valid:
                    validation_errors.append(f"税抜価格エラー: {excl_price_result.error_message}")
            
            # 税込・税抜関係性検証
            tax_result = self.validate_tax_relationship(price_incl_tax, price_excl_tax)
            if not tax_result.is_valid:
                validation_errors.append(f"税込税抜関係エラー: {tax_result.error_message}")
            
            # 信頼度スコア計算
            confidence_score = self.calculate_confidence_score(product_data)
            
            # 総合判定
            is_valid = len(validation_errors) == 0
            
            print(f"DEBUG: バリデーション結果 - 有効:{is_valid}, エラー:{validation_errors}, 信頼度:{confidence_score}")
            
            return ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                validation_errors=validation_errors,
                error_message=None if is_valid else "; ".join(validation_errors)
            )
            
        except Exception as e:
            logging.error(f"Product data validation error: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_errors=[f"検証処理エラー: {str(e)}"],
                error_message=f"検証処理エラー: {str(e)}"
            )
    
    def validate_price_range(self, price: Optional[int]) -> ValidationResult:
        """
        価格妥当性検証
        
        Args:
            price: 検証対象の価格
            
        Returns:
            価格検証結果
        """
        try:
            # None値チェック
            if price is None:
                return ValidationResult(
                    is_valid=False,
                    error_message="価格がNullです"
                )
            
            # 型チェック
            if not isinstance(price, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    error_message="価格は数値である必要があります"
                )
            
            # 範囲チェック（1円 - 999,999円）
            if price < self.MIN_PRICE:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"価格は{self.MIN_PRICE}円以上である必要があります"
                )
            
            if price > self.MAX_PRICE:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"価格は{self.MAX_PRICE}円以下である必要があります"
                )
            
            return ValidationResult(
                is_valid=True,
                error_message=None
            )
            
        except Exception as e:
            logging.error(f"Price validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"価格検証エラー: {str(e)}"
            )
    
    def validate_product_name(self, product_name: Optional[str]) -> ValidationResult:
        """
        商品名存在確認
        
        Args:
            product_name: 検証対象の商品名
            
        Returns:
            商品名検証結果
        """
        try:
            # None値チェック
            if product_name is None:
                return ValidationResult(
                    is_valid=False,
                    error_message="商品名がNullです"
                )
            
            # 型チェック
            if not isinstance(product_name, str):
                return ValidationResult(
                    is_valid=False,
                    error_message="商品名は文字列である必要があります"
                )
            
            # 空文字・空白文字のみチェック
            if not product_name.strip():
                return ValidationResult(
                    is_valid=False,
                    error_message="商品名が空です"
                )
            
            return ValidationResult(
                is_valid=True,
                error_message=None
            )
            
        except Exception as e:
            logging.error(f"Product name validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"商品名検証エラー: {str(e)}"
            )
    
    def validate_tax_relationship(self, price_incl_tax: Optional[int], price_excl_tax: Optional[int]) -> ValidationResult:
        """
        税込・税抜関係性チェック
        
        Args:
            price_incl_tax: 税込価格
            price_excl_tax: 税抜価格
            
        Returns:
            関係性検証結果
        """
        try:
            # 両方Noneの場合はエラー
            if price_incl_tax is None and price_excl_tax is None:
                return ValidationResult(
                    is_valid=False,
                    error_message="税込価格と税抜価格の両方がNullです"
                )
            
            # どちらか一方がNoneの場合はOK
            if price_incl_tax is None or price_excl_tax is None:
                return ValidationResult(
                    is_valid=True,
                    error_message=None
                )
            
            # 型チェック
            if not isinstance(price_incl_tax, (int, float)) or not isinstance(price_excl_tax, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    error_message="価格は数値である必要があります"
                )
            
            # 0円以下チェック
            if price_incl_tax <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="税込価格は1円以上である必要があります"
                )
            
            if price_excl_tax <= 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="税抜価格は1円以上である必要があります"
                )
            
            # 税込 >= 税抜 チェック
            if price_incl_tax < price_excl_tax:
                return ValidationResult(
                    is_valid=False,
                    error_message="税込価格は税抜価格以上である必要があります"
                )
            
            # 税込 = 税抜 の場合は警告のみ（計算誤差を考慮）
            if price_incl_tax == price_excl_tax:
                print(f"DEBUG: 税込と税抜が同額 - 税込:{price_incl_tax}, 税抜:{price_excl_tax}")
                # 計算誤差を考慮して有効とする
                pass
            
            return ValidationResult(
                is_valid=True,
                error_message=None
            )
            
        except Exception as e:
            logging.error(f"Tax relationship validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"税込税抜関係検証エラー: {str(e)}"
            )
    
    def calculate_confidence_score(self, product_data: Dict[str, Any]) -> float:
        """
        信頼度スコア計算
        
        Args:
            product_data: 商品データ
            
        Returns:
            信頼度スコア（0.0-1.0）
        """
        try:
            total_score = 0.0
            weight_sum = 0.0
            
            # OCR信頼度（重み: 0.3）
            ocr_confidence = product_data.get('ocr_confidence', 0.0)
            if isinstance(ocr_confidence, (int, float)):
                total_score += ocr_confidence * 0.3
                weight_sum += 0.3
            
            # 抽出信頼度（重み: 0.25）
            extraction_confidence = product_data.get('extraction_confidence', 0.0)
            if isinstance(extraction_confidence, (int, float)):
                total_score += extraction_confidence * 0.25
                weight_sum += 0.25
            
            # カテゴリ分類信頼度（重み: 0.2）
            categorization_confidence = product_data.get('categorization_confidence', 0.0)
            if isinstance(categorization_confidence, (int, float)):
                total_score += categorization_confidence * 0.2
                weight_sum += 0.2
            
            # データ品質評価（重み: 0.25）
            data_quality_score = self._calculate_data_quality_score(product_data)
            total_score += data_quality_score * 0.25
            weight_sum += 0.25
            
            # 加重平均計算
            if weight_sum > 0:
                final_score = total_score / weight_sum
            else:
                final_score = 0.0
            
            # 0.0-1.0の範囲に正規化
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            logging.error(f"Confidence score calculation error: {e}")
            return 0.0
    
    def _calculate_data_quality_score(self, product_data: Dict[str, Any]) -> float:
        """
        データ品質スコア算出
        
        Args:
            product_data: 商品データ
            
        Returns:
            データ品質スコア（0.0-1.0）
        """
        try:
            score = 0.0
            checks = 0
            
            # 商品名の品質評価
            product_name = product_data.get('product')
            if product_name and isinstance(product_name, str):
                name_length = len(product_name.strip())
                if name_length >= 3:  # 3文字以上
                    score += 1.0
                elif name_length >= 1:  # 1-2文字
                    score += 0.5
                checks += 1
            else:
                score += 0.0
                checks += 1
            
            # 価格の妥当性評価
            price_incl_tax = product_data.get('price_incl_tax')
            if price_incl_tax and isinstance(price_incl_tax, (int, float)):
                if 10 <= price_incl_tax <= 10000:  # 一般的な価格帯
                    score += 1.0
                elif 1 <= price_incl_tax < 10 or 10000 < price_incl_tax <= 100000:
                    score += 0.7
                else:
                    score += 0.3
                checks += 1
            else:
                score += 0.0
                checks += 1
            
            # 単位情報の存在評価
            unit = product_data.get('unit')
            if unit and isinstance(unit, str) and unit.strip():
                score += 1.0
                checks += 1
            else:
                score += 0.2  # 単位がなくても最低点
                checks += 1
            
            # カテゴリ評価
            category = product_data.get('category')
            if category and isinstance(category, str):
                if category != 'その他':
                    score += 1.0
                else:
                    score += 0.3
                checks += 1
            else:
                score += 0.0
                checks += 1
            
            # 税抜価格の存在評価
            price_excl_tax = product_data.get('price_excl_tax')
            if price_excl_tax and isinstance(price_excl_tax, (int, float)):
                score += 1.0
                checks += 1
            else:
                score += 0.5  # 税抜がなくても中程度の点数
                checks += 1
            
            # 平均スコア算出
            if checks > 0:
                return score / checks
            else:
                return 0.0
                
        except Exception as e:
            logging.error(f"Data quality score calculation error: {e}")
            return 0.0