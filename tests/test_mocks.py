"""
モック機能のテスト

conftest.pyで定義されたフィクスチャとヘルパー関数の動作確認
"""

import pytest
from tests.helpers import (
    assert_extraction_result_structure,
    create_mock_ocr_response,
    create_mock_llm_response,
    MockAPIManager
)


class TestMockFixtures:
    """モックフィクスチャのテスト"""
    
    def test_mock_vision_client_fixture(self, mock_vision_client):
        """Vision APIモックの動作確認"""
        # モックレスポンスを取得
        response = mock_vision_client.document_text_detection("dummy_image")
        
        # レスポンス構造の確認
        assert hasattr(response, 'text_annotations')
        assert hasattr(response, 'full_text_annotation')
        assert len(response.text_annotations) > 0
        assert response.full_text_annotation.text != ""
        
        # 最初のアノテーションの確認
        first_annotation = response.text_annotations[0]
        assert hasattr(first_annotation, 'description')
        assert hasattr(first_annotation, 'bounding_poly')
        assert len(first_annotation.bounding_poly.vertices) > 0
    
    def test_mock_openai_client_fixture(self, mock_openai_client):
        """OpenAI APIモックの動作確認"""
        # モックレスポンスを取得
        response = mock_openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}]
        )
        
        # レスポンス構造の確認
        assert len(response.choices) > 0
        assert hasattr(response.choices[0], 'message')
        assert hasattr(response.choices[0].message, 'content')
        assert hasattr(response, 'usage')
        assert response.usage.total_tokens > 0
    
    def test_mock_anthropic_client_fixture(self, mock_anthropic_client):
        """Anthropic APIモックの動作確認"""
        # モックレスポンスを取得
        response = mock_anthropic_client.messages.create(
            model="claude-3-5-sonnet",
            messages=[{"role": "user", "content": "test"}]
        )
        
        # レスポンス構造の確認
        assert len(response.content) > 0
        assert hasattr(response.content[0], 'text')
        assert hasattr(response, 'usage')
        assert response.usage.input_tokens > 0
    
    def test_fixture_data_loading(self, expected_extraction_result, expected_ocr_response):
        """フィクスチャデータの読み込み確認"""
        # 抽出結果データの確認
        assert isinstance(expected_extraction_result, list)
        assert len(expected_extraction_result) > 0
        assert_extraction_result_structure(expected_extraction_result)
        
        # OCRレスポンスデータの確認
        assert isinstance(expected_ocr_response, dict)
        assert "text_annotations" in expected_ocr_response
        assert "full_text_annotation" in expected_ocr_response
    
    def test_sample_image_paths(self, sample_image_path, corrupted_image_path):
        """サンプル画像パスの確認"""
        assert sample_image_path.exists()
        assert corrupted_image_path.exists()
        assert sample_image_path.suffix.lower() == ".jpg"
        assert corrupted_image_path.suffix.lower() == ".jpg"


class TestHelperFunctions:
    """ヘルパー関数のテスト"""
    
    def test_create_mock_ocr_response(self):
        """OCRレスポンスモック作成の確認"""
        text_content = "テスト商品\n100円"
        annotations = [
            {
                "description": "テスト商品",
                "bounding_poly": {
                    "vertices": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 100, "y": 20}, {"x": 0, "y": 20}]
                }
            }
        ]
        
        mock_response = create_mock_ocr_response(text_content, annotations)
        
        assert mock_response.full_text_annotation.text == text_content
        assert len(mock_response.text_annotations) == 1
        assert mock_response.text_annotations[0].description == "テスト商品"
    
    def test_create_mock_llm_response_openai(self):
        """OpenAI LLMレスポンスモック作成の確認"""
        content = '{"product": "test", "price": 100}'
        mock_response = create_mock_llm_response(content, "gpt-4o")
        
        assert len(mock_response.choices) == 1
        assert mock_response.choices[0].message.content == content
        assert mock_response.usage.total_tokens > 0
    
    def test_create_mock_llm_response_anthropic(self):
        """Anthropic LLMレスポンスモック作成の確認"""
        content = '{"product": "test", "price": 100}'
        mock_response = create_mock_llm_response(content, "claude-3-5-sonnet")
        
        assert len(mock_response.content) == 1
        assert mock_response.content[0].text == content
        assert mock_response.usage.input_tokens > 0
    
    def test_assert_extraction_result_structure_valid(self):
        """有効な抽出結果構造のアサーション"""
        valid_result = [
            {
                "product": "テスト商品",
                "price_incl_tax": 100,
                "price_excl_tax": 90,
                "unit": "1個",
                "category": "食品",
                "confidence": 0.95
            }
        ]
        
        # 例外が発生しないことを確認
        assert_extraction_result_structure(valid_result)
    
    def test_assert_extraction_result_structure_invalid(self):
        """無効な抽出結果構造のアサーション"""
        invalid_result = [
            {
                "product": "テスト商品",
                # price_incl_tax が欠落
                "category": "食品",
                "confidence": 0.95
            }
        ]
        
        # AssertionErrorが発生することを確認
        with pytest.raises(AssertionError):
            assert_extraction_result_structure(invalid_result)


class TestMockAPIManager:
    """MockAPIManagerのテスト"""
    
    def test_mock_api_manager_initialization(self):
        """MockAPIManager初期化の確認"""
        manager = MockAPIManager()
        
        assert manager.vision_mock is None
        assert manager.openai_mock is None
        assert manager.anthropic_mock is None
    
    def test_setup_vision_mock(self):
        """Vision APIモックセットアップの確認"""
        manager = MockAPIManager()
        response_data = {
            "full_text_annotation": {"text": "テスト"},
            "text_annotations": []
        }
        
        mock = manager.setup_vision_mock(response_data)
        
        assert mock is not None
        assert manager.vision_mock is not None
        assert mock.full_text_annotation.text == "テスト"
    
    def test_reset_all_mocks(self):
        """全モックリセットの確認"""
        manager = MockAPIManager()
        
        # モックをセットアップ
        manager.setup_vision_mock({"full_text_annotation": {"text": "test"}, "text_annotations": []})
        manager.setup_openai_mock("test content")
        
        # リセット実行
        manager.reset_all_mocks()
        
        # リセットが実行されることを確認（例外が発生しないことを確認）
        assert True  # リセット処理が正常に完了


@pytest.mark.integration
class TestEnvironmentControl:
    """環境変数制御のテスト"""
    
    def test_mock_disabled_flag(self, mock_apis_disabled):
        """APIモック無効化フラグの確認"""
        # 環境変数の値に応じてbool値が返されることを確認
        assert isinstance(mock_apis_disabled, bool)
    
    def test_mock_config_loading(self, mock_config):
        """モック設定読み込みの確認"""
        assert isinstance(mock_config, dict)
        assert "max_image_size_mb" in mock_config
        assert "ocr_retry_count" in mock_config
        assert mock_config["max_image_size_mb"] == 10