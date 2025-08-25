"""
商品カテゴリ分類モジュールのテストコード

TDD方式でのテスト作成（T050）
全テストが失敗することを確認後、T051で実装を行う。
"""

import pytest
from unittest.mock import Mock, patch
from src.categorizer import ProductCategorizer, CategoryResult


class TestProductCategorizer:
    """商品カテゴリ分類モジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.categorizer = ProductCategorizer()

    def test_initialization(self):
        """ProductCategorizerの初期化テスト"""
        categorizer = ProductCategorizer()
        assert categorizer is not None
        assert hasattr(categorizer, 'categorize_product')
        assert hasattr(categorizer, 'categorize_by_keywords') 
        assert hasattr(categorizer, 'categorize_by_llm')
        assert hasattr(categorizer, 'batch_categorize')
        expected_categories = ["食品", "日用品", "医薬品・化粧品", "衣料品", "家電・雑貨", "その他"]
        assert categorizer.CATEGORIES == expected_categories

    def test_categorize_product_basic(self):
        """基本的な商品カテゴリ分類テスト"""
        result = self.categorizer.categorize_product("きゅうり3本")
        
        assert isinstance(result, CategoryResult)
        assert result.category in self.categorizer.CATEGORIES
        assert 0.0 <= result.confidence <= 1.0
        assert result.method in ["keyword", "llm", "hybrid", "llm_fallback"]
        
        # きゅうりは食品カテゴリに分類されるべき
        assert result.category == "食品"

    def test_categorize_by_keywords_food(self):
        """キーワードベース食品分類テスト"""
        food_products = [
            "きゅうり3本",
            "サントリー天然水2L",
            "パン",
            "牛乳",
            "りんご"
        ]
        
        for product in food_products:
            result = self.categorizer.categorize_by_keywords(product)
            assert isinstance(result, CategoryResult)
            assert result.category == "食品"
            assert result.method == "keyword"
            assert result.confidence > 0.5

    def test_categorize_by_keywords_daily_goods(self):
        """キーワードベース日用品分類テスト"""
        daily_products = [
            "洗剤",
            "ティッシュ",
            "トイレットペーパー",
            "石鹸",
            "歯ブラシ"
        ]
        
        for product in daily_products:
            result = self.categorizer.categorize_by_keywords(product)
            assert isinstance(result, CategoryResult)
            assert result.category == "日用品"
            assert result.method == "keyword"
            assert result.confidence > 0.5

    def test_categorize_by_llm_basic(self):
        """LLMベース分類基本テスト"""
        result = self.categorizer.categorize_by_llm("サントリー プレミアムモルツ 350ml")
        
        assert isinstance(result, CategoryResult)
        assert result.category in self.categorizer.CATEGORIES
        assert 0.0 <= result.confidence <= 1.0
        assert result.method in ["openai", "anthropic", "llm_fallback", "llm_error", "keyword_error"]

    def test_batch_categorize_basic(self):
        """バッチカテゴリ分類基本テスト"""
        product_list = [
            "きゅうり3本",
            "洗剤",
            "風邪薬",
            "Tシャツ",
            "電池"
        ]
        
        results = self.categorizer.batch_categorize(product_list)
        
        assert isinstance(results, list)
        assert len(results) == len(product_list)
        
        # 各結果の検証
        for i, result in enumerate(results):
            assert isinstance(result, CategoryResult)
            assert result.category in self.categorizer.CATEGORIES
            assert 0.0 <= result.confidence <= 1.0
        
        # 期待されるカテゴリ
        expected_categories = ["食品", "日用品", "医薬品・化粧品", "衣料品", "家電・雑貨"]
        actual_categories = [r.category for r in results]
        
        # 少なくとも一部は期待されるカテゴリに分類される
        assert any(cat in expected_categories for cat in actual_categories)

    def test_configuration_settings(self):
        """設定項目テスト"""
        custom_config = {
            'classification_method': 'hybrid',
            'llm_provider': 'openai',
            'confidence_threshold': 0.8,
            'use_mock': False,
            'keyword_strictness': 'medium'
        }
        
        categorizer = ProductCategorizer(config=custom_config)
        assert categorizer.config == custom_config

    def test_category_result_dataclass(self):
        """CategoryResultデータクラステスト"""
        result = CategoryResult(
            category="食品",
            confidence=0.95,
            method="keyword"
        )
        
        assert result.category == "食品"
        assert result.confidence == 0.95
        assert result.method == "keyword"