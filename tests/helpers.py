"""
テスト用ヘルパー関数

テストで共通的に使用される関数群を提供します。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock


def create_temp_image(content: bytes = b"fake_image_data") -> Path:
    """一時的な画像ファイルを作成"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(content)
        return Path(f.name)


def create_corrupted_image() -> Path:
    """破損した画像ファイルを作成"""
    return create_temp_image(b"This is not a valid image file")


def cleanup_temp_file(file_path: Path) -> None:
    """一時ファイルをクリーンアップ"""
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass


def assert_extraction_result_structure(result: List[Dict[str, Any]]) -> None:
    """抽出結果の構造が正しいかアサーション"""
    assert isinstance(result, list), "Result should be a list"
    
    for item in result:
        assert isinstance(item, dict), "Each item should be a dictionary"
        
        # 必須フィールドの確認
        required_fields = ["product", "price_incl_tax", "category", "confidence"]
        for field in required_fields:
            assert field in item, f"Required field '{field}' is missing"
        
        # データ型の確認
        assert isinstance(item["product"], str), "product should be string"
        assert isinstance(item["price_incl_tax"], int), "price_incl_tax should be integer"
        assert isinstance(item["category"], str), "category should be string"
        assert isinstance(item["confidence"], (int, float)), "confidence should be numeric"
        
        # 値の範囲確認
        assert 0 <= item["confidence"] <= 1, "confidence should be between 0 and 1"
        assert item["price_incl_tax"] >= 0, "price_incl_tax should be non-negative"
        
        # オプショナルフィールドの確認
        if "price_excl_tax" in item and item["price_excl_tax"] is not None:
            assert isinstance(item["price_excl_tax"], int), "price_excl_tax should be integer"
            assert item["price_excl_tax"] >= 0, "price_excl_tax should be non-negative"
        
        if "unit" in item:
            assert isinstance(item["unit"], str), "unit should be string"


def assert_valid_categories(categories: List[str]) -> None:
    """カテゴリが有効な値かアサーション"""
    valid_categories = ["食品", "日用品", "医薬品・化粧品", "衣料品", "家電・雑貨", "その他"]
    
    for category in categories:
        assert category in valid_categories, f"Invalid category: {category}"


def create_mock_ocr_response(
    text_content: str,
    annotations: Optional[List[Dict[str, Any]]] = None
) -> Mock:
    """モックOCRレスポンスを作成"""
    mock_response = Mock()
    mock_response.full_text_annotation.text = text_content
    mock_response.text_annotations = []
    
    if annotations:
        for annotation in annotations:
            mock_annotation = Mock()
            mock_annotation.description = annotation.get("description", "")
            mock_annotation.bounding_poly.vertices = []
            
            for vertex in annotation.get("bounding_poly", {}).get("vertices", []):
                mock_vertex = Mock()
                mock_vertex.x = vertex.get("x", 0)
                mock_vertex.y = vertex.get("y", 0)
                mock_annotation.bounding_poly.vertices.append(mock_vertex)
            
            mock_response.text_annotations.append(mock_annotation)
    
    return mock_response


def create_mock_llm_response(content: str, model: str = "gpt-4o") -> Mock:
    """モックLLMレスポンスを作成"""
    mock_response = Mock()
    
    if model.startswith("gpt"):
        # OpenAI形式
        choice = Mock()
        choice.message.content = content
        choice.finish_reason = "stop"
        mock_response.choices = [choice]
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 120
        mock_response.usage.total_tokens = 270
    else:
        # Anthropic形式
        content_obj = Mock()
        content_obj.text = content
        mock_response.content = [content_obj]
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 145
        mock_response.usage.output_tokens = 115
    
    return mock_response


def load_test_config() -> Dict[str, Any]:
    """テスト用設定を読み込み"""
    return {
        "max_image_size_mb": int(os.getenv("MAX_IMAGE_SIZE_MB", "10")),
        "ocr_retry_count": int(os.getenv("OCR_RETRY_COUNT", "3")),
        "processing_timeout_seconds": int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "30")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_format": os.getenv("LOG_FORMAT", "json"),
        "use_mock_apis": os.getenv("USE_MOCK_APIS", "true").lower() == "true"
    }


def validate_image_file(file_path: Path) -> bool:
    """画像ファイルが有効かどうかチェック"""
    if not file_path.exists():
        return False
    
    # ファイルサイズチェック
    max_size = 10 * 1024 * 1024  # 10MB
    if file_path.stat().st_size > max_size:
        return False
    
    # 拡張子チェック
    valid_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
    if file_path.suffix.lower() not in valid_extensions:
        return False
    
    return True


def compare_extraction_results(
    actual: List[Dict[str, Any]], 
    expected: List[Dict[str, Any]],
    tolerance: float = 0.1
) -> bool:
    """抽出結果の比較（信頼度に許容誤差を適用）"""
    if len(actual) != len(expected):
        return False
    
    for actual_item, expected_item in zip(actual, expected):
        # 基本フィールドの比較
        for field in ["product", "price_incl_tax", "category"]:
            if actual_item.get(field) != expected_item.get(field):
                return False
        
        # 信頼度の比較（許容誤差あり）
        actual_conf = actual_item.get("confidence", 0)
        expected_conf = expected_item.get("confidence", 0)
        if abs(actual_conf - expected_conf) > tolerance:
            return False
    
    return True


def generate_test_data_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """テストデータの統計情報を生成"""
    if not results:
        return {"total_items": 0}
    
    categories = [item.get("category", "unknown") for item in results]
    confidence_scores = [item.get("confidence", 0) for item in results]
    prices = [item.get("price_incl_tax", 0) for item in results]
    
    return {
        "total_items": len(results),
        "categories": list(set(categories)),
        "avg_confidence": sum(confidence_scores) / len(confidence_scores),
        "min_confidence": min(confidence_scores),
        "max_confidence": max(confidence_scores),
        "avg_price": sum(prices) / len(prices),
        "min_price": min(prices),
        "max_price": max(prices)
    }


class MockAPIManager:
    """APIモックの管理クラス"""
    
    def __init__(self):
        self.vision_mock = None
        self.openai_mock = None
        self.anthropic_mock = None
    
    def setup_vision_mock(self, response_data: Dict[str, Any]) -> Mock:
        """Vision APIモックをセットアップ"""
        self.vision_mock = create_mock_ocr_response(
            response_data["full_text_annotation"]["text"],
            response_data["text_annotations"]
        )
        return self.vision_mock
    
    def setup_openai_mock(self, content: str) -> Mock:
        """OpenAI APIモックをセットアップ"""
        self.openai_mock = create_mock_llm_response(content, "gpt-4o")
        return self.openai_mock
    
    def setup_anthropic_mock(self, content: str) -> Mock:
        """Anthropic APIモックをセットアップ"""
        self.anthropic_mock = create_mock_llm_response(content, "claude-3-5-sonnet")
        return self.anthropic_mock
    
    def reset_all_mocks(self):
        """全てのモックをリセット"""
        for mock in [self.vision_mock, self.openai_mock, self.anthropic_mock]:
            if mock:
                mock.reset_mock()