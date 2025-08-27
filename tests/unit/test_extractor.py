"""
商品・価格ペア抽出モジュールのテストコード

TDD方式でのテスト作成（T040）
全テストが失敗することを確認後、T041で実装を行う。
"""

import pytest
from unittest.mock import Mock, patch
from src.extractor import ProductPriceExtractor


class TestProductPriceExtractor:
    """商品・価格ペア抽出モジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.extractor = ProductPriceExtractor()

    def test_initialization(self):
        """ProductPriceExtractorの初期化テスト"""
        extractor = ProductPriceExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'extract_product_price_pairs')
        assert hasattr(extractor, 'detect_price_patterns')
        assert hasattr(extractor, 'identify_product_names')
        assert hasattr(extractor, 'match_spatial_relationships')
        assert hasattr(extractor, 'calculate_confidence_score')

    def test_extract_product_price_pairs_basic(self):
        """基本的な商品・価格ペア抽出テスト"""
        # OCR結果から商品・価格ペアの抽出をテスト
        ocr_result = {
            'text_annotations': [
                {'text': 'きゅうり', 'bounding_box': (10, 10, 80, 30)},
                {'text': '198円', 'bounding_box': (90, 10, 150, 30)}
            ],
            'full_text': 'きゅうり 198円'
        }
        result = self.extractor.extract_product_price_pairs(ocr_result)
        
        # 結果の検証
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 最初のペアの検証
        first_pair = result[0]
        assert 'product' in first_pair
        assert 'price_incl_tax' in first_pair
        assert 'confidence' in first_pair
        assert isinstance(first_pair['confidence'], float)
        assert 0.0 <= first_pair['confidence'] <= 1.0

    def test_detect_price_patterns_basic(self):
        """基本的な価格パターン認識テスト（TDD: 未実装確認）"""
        # TDD第1ステップ: 実装前はNotImplementedErrorが発生することを確認
        text_annotations = [
            {'text': '198円', 'bounding_box': (90, 10, 150, 30)},
            {'text': '298円(税込)', 'bounding_box': (90, 50, 180, 70)}
        ]
        with pytest.raises(NotImplementedError, match="T041で実装予定"):
            self.extractor.detect_price_patterns(text_annotations)

    def test_identify_product_names_basic(self):
        """基本的な商品名識別テスト（TDD: 未実装確認）"""
        # TDD第1ステップ: 実装前はNotImplementedErrorが発生することを確認
        text_annotations = [
            {'text': 'きゅうり', 'bounding_box': (10, 10, 80, 30)},
            {'text': 'サントリー天然水', 'bounding_box': (10, 50, 150, 70)}
        ]
        with pytest.raises(NotImplementedError, match="T041で実装予定"):
            self.extractor.identify_product_names(text_annotations)

    def test_match_spatial_relationships_basic(self):
        """基本的な空間関係マッチングテスト（TDD: 未実装確認）"""
        # TDD第1ステップ: 実装前はNotImplementedErrorが発生することを確認
        product_candidates = [
            {'text': 'きゅうり', 'bounding_box': (10, 10, 80, 30)}
        ]
        price_candidates = [
            {'text': '198円', 'bounding_box': (90, 10, 150, 30)}
        ]
        with pytest.raises(NotImplementedError, match="T041で実装予定"):
            self.extractor.match_spatial_relationships(product_candidates, price_candidates)

    def test_calculate_confidence_score_basic(self):
        """基本的な信頼度スコア計算テスト（TDD: 未実装確認）"""
        # TDD第1ステップ: 実装前はNotImplementedErrorが発生することを確認
        extraction_data = {
            'product_name': 'きゅうり3本',
            'price_incl_tax': 198,
            'spatial_distance': 15.5,
            'text_clarity': 0.95,
            'pattern_match_confidence': 0.98
        }
        with pytest.raises(NotImplementedError, match="T041で実装予定"):
            self.extractor.calculate_confidence_score(extraction_data)

    def test_configuration_settings(self):
        """設定項目テスト"""
        # カスタム設定でProductPriceExtractorを初期化
        custom_config = {
            'llm_provider': 'openai',
            'max_spatial_distance': 100,
            'min_confidence_threshold': 0.7,
            'use_mock': False,
            'price_pattern_strictness': 'high'
        }
        
        extractor = ProductPriceExtractor(config=custom_config)
        assert extractor.config == custom_config