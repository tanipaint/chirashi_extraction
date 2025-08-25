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
        """基本的な商品カテゴリ分類テスト（TDD: 未実装確認）"""
        with pytest.raises(NotImplementedError, match="T051で実装予定"):
            self.categorizer.categorize_product("きゅうり3本")

    def test_categorize_by_keywords_food(self):
        """キーワードベース食品分類テスト（TDD: 未実装確認）"""
        food_products = [
            "きゅうり3本",
            "サントリー天然水2L",
            "パン",
            "牛乳",
            "りんご"
        ]
        
        for product in food_products:
            with pytest.raises(NotImplementedError, match="T051で実装予定"):
                self.categorizer.categorize_by_keywords(product)

    def test_categorize_by_keywords_daily_goods(self):
        """キーワードベース日用品分類テスト（TDD: 未実装確認）"""
        daily_products = [
            "洗剤",
            "ティッシュ",
            "トイレットペーパー",
            "石鹸",
            "歯ブラシ"
        ]
        
        for product in daily_products:
            with pytest.raises(NotImplementedError, match="T051で実装予定"):
                self.categorizer.categorize_by_keywords(product)

    def test_categorize_by_llm_basic(self):
        """LLMベース分類基本テスト（TDD: 未実装確認）"""
        with pytest.raises(NotImplementedError, match="T051で実装予定"):
            self.categorizer.categorize_by_llm("サントリー プレミアムモルツ 350ml")

    def test_batch_categorize_basic(self):
        """バッチカテゴリ分類基本テスト（TDD: 未実装確認）"""
        product_list = [
            "きゅうり3本",
            "洗剤",
            "風邪薬",
            "Tシャツ",
            "電池"
        ]
        
        with pytest.raises(NotImplementedError, match="T051で実装予定"):
            self.categorizer.batch_categorize(product_list)

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