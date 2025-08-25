"""
データ検証モジュールのテストコード

TDD方式でのテスト作成（T060）
全テストが失敗することを確認後、T061で実装を行う。
"""

import pytest
from src.validator import ProductValidator, ValidationResult


class TestProductValidator:
    """データ検証モジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.validator = ProductValidator()

    def test_initialization(self):
        """ProductValidatorの初期化テスト"""
        validator = ProductValidator()
        assert validator is not None
        assert hasattr(validator, 'validate_product_data')
        assert hasattr(validator, 'validate_price_range')
        assert hasattr(validator, 'validate_product_name')
        assert hasattr(validator, 'validate_tax_relationship')
        assert hasattr(validator, 'calculate_confidence_score')

    def test_validate_price_range_valid(self):
        """価格妥当性検証テスト - 有効範囲"""
        valid_prices = [1, 100, 1000, 50000, 999999]
        
        for price in valid_prices:
            result = self.validator.validate_price_range(price)
            assert isinstance(result, ValidationResult)
            assert result.is_valid == True
            assert result.error_message is None

    def test_validate_price_range_invalid(self):
        """価格妥当性検証テスト - 無効範囲"""
        invalid_prices = [-1, 0, 1000000, 1500000, None]
        
        for price in invalid_prices:
            result = self.validator.validate_price_range(price)
            assert isinstance(result, ValidationResult)
            assert result.is_valid == False
            assert result.error_message is not None

    def test_validate_product_name_valid(self):
        """商品名存在確認テスト - 有効な商品名"""
        valid_names = [
            "きゅうり3本",
            "サントリー天然水2L", 
            "食パン",
            "洗剤 アタック",
            "Tシャツ Mサイズ"
        ]
        
        for name in valid_names:
            result = self.validator.validate_product_name(name)
            assert isinstance(result, ValidationResult)
            assert result.is_valid == True
            assert result.error_message is None

    def test_validate_product_name_invalid(self):
        """商品名存在確認テスト - 無効な商品名"""
        invalid_names = [
            "",
            "   ",
            None,
            "   \t\n   ",  # 空白文字のみ
        ]
        
        for name in invalid_names:
            result = self.validator.validate_product_name(name)
            assert isinstance(result, ValidationResult)
            assert result.is_valid == False
            assert result.error_message is not None

    def test_validate_tax_relationship_valid(self):
        """税込・税抜関係性チェックテスト - 正常な関係"""
        valid_cases = [
            (110, 100),    # 税込110円、税抜100円
            (198, 180),    # 税込198円、税抜180円
            (1080, 1000),  # 税込1080円、税抜1000円
            (500, None),   # 税込のみ
            (None, 450),   # 税抜のみ
        ]
        
        for price_incl_tax, price_excl_tax in valid_cases:
            result = self.validator.validate_tax_relationship(price_incl_tax, price_excl_tax)
            assert isinstance(result, ValidationResult)
            assert result.is_valid == True
            assert result.error_message is None

    def test_validate_tax_relationship_invalid(self):
        """税込・税抜関係性チェックテスト - 異常な関係"""
        invalid_cases = [
            (100, 110),    # 税込 < 税抜（異常）
            (200, 200),    # 税込 = 税抜（異常）
            (0, 100),      # 税込0円（異常）
            (100, 0),      # 税抜0円（異常）
            (None, None),  # 両方None（異常）
        ]
        
        for price_incl_tax, price_excl_tax in invalid_cases:
            result = self.validator.validate_tax_relationship(price_incl_tax, price_excl_tax)
            assert isinstance(result, ValidationResult)
            assert result.is_valid == False
            assert result.error_message is not None

    def test_calculate_confidence_score_high(self):
        """信頼度スコア計算テスト - 高信頼度ケース"""
        # 高品質データのサンプル
        product_data = {
            'product': 'きゅうり3本',
            'price_incl_tax': 198,
            'price_excl_tax': 180,
            'unit': '3本',
            'category': '食品',
            'ocr_confidence': 0.95,
            'extraction_confidence': 0.90,
            'categorization_confidence': 0.85
        }
        
        score = self.validator.calculate_confidence_score(product_data)
        assert isinstance(score, float)
        assert 0.8 <= score <= 1.0  # 高信頼度

    def test_calculate_confidence_score_low(self):
        """信頼度スコア計算テスト - 低信頼度ケース"""
        # 低品質データのサンプル
        product_data = {
            'product': 'あいまいな商品名',
            'price_incl_tax': 50000,  # 高額商品
            'price_excl_tax': None,   # 税抜なし
            'unit': None,             # 単位なし
            'category': 'その他',
            'ocr_confidence': 0.60,
            'extraction_confidence': 0.55,
            'categorization_confidence': 0.45
        }
        
        score = self.validator.calculate_confidence_score(product_data)
        assert isinstance(score, float)
        assert 0.0 <= score <= 0.6  # 低信頼度

    def test_validate_product_data_comprehensive(self):
        """商品データ総合検証テスト"""
        # 正常なデータケース
        valid_data = {
            'product': 'きゅうり3本',
            'price_incl_tax': 198,
            'price_excl_tax': 180,
            'unit': '3本',
            'category': '食品'
        }
        
        result = self.validator.validate_product_data(valid_data)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.confidence_score >= 0.7

    def test_validate_product_data_with_errors(self):
        """商品データ総合検証テスト - エラーケース"""
        # 異常なデータケース
        invalid_data = {
            'product': '',           # 商品名なし
            'price_incl_tax': -100,  # 負の価格
            'price_excl_tax': 200,   # 税込 < 税抜
            'unit': None,
            'category': 'その他'
        }
        
        result = self.validator.validate_product_data(invalid_data)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.validation_errors) > 0
        assert result.confidence_score < 0.3

    def test_validation_result_dataclass(self):
        """ValidationResultデータクラステスト"""
        result = ValidationResult(
            is_valid=True,
            confidence_score=0.85,
            validation_errors=[],
            error_message=None
        )
        
        assert result.is_valid == True
        assert result.confidence_score == 0.85
        assert result.validation_errors == []
        assert result.error_message is None