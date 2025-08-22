"""
テスト設定とフィクスチャ定義

このファイルは、pytest実行時に自動的に読み込まれ、
全てのテストで使用可能なフィクスチャを提供します。
"""

import json
import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path


# フィクスチャデータのベースパス
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_IMAGES_DIR = FIXTURES_DIR / "sample_images"
EXPECTED_OUTPUTS_DIR = FIXTURES_DIR / "expected_outputs"


def load_fixture_json(filename: str) -> dict:
    """フィクスチャJSONファイルを読み込む"""
    file_path = EXPECTED_OUTPUTS_DIR / filename
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def mock_vision_client():
    """Google Cloud Vision API クライアントのモック"""
    mock_client = Mock()
    
    # OCRレスポンスのサンプルデータを読み込み
    ocr_response = load_fixture_json("ocr_response_sample_01.json")
    
    # document_text_detection メソッドのモック
    mock_response = Mock()
    mock_response.text_annotations = []
    mock_response.full_text_annotation.text = ocr_response["full_text_annotation"]["text"]
    
    # text_annotationsの構築
    for annotation in ocr_response["text_annotations"]:
        mock_annotation = Mock()
        mock_annotation.description = annotation["description"]
        mock_annotation.bounding_poly.vertices = []
        
        for vertex in annotation["bounding_poly"]["vertices"]:
            mock_vertex = Mock()
            mock_vertex.x = vertex.get("x", 0)
            mock_vertex.y = vertex.get("y", 0)
            mock_annotation.bounding_poly.vertices.append(mock_vertex)
        
        mock_response.text_annotations.append(mock_annotation)
    
    mock_client.document_text_detection.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_openai_client():
    """OpenAI API クライアントのモック"""
    mock_client = Mock()
    
    # LLMレスポンスのサンプルデータを読み込み
    llm_response = load_fixture_json("llm_response_sample.json")
    
    # chat.completions.create メソッドのモック
    mock_response = Mock()
    mock_response.choices = []
    
    choice = Mock()
    choice.message.content = llm_response["openai_response"]["choices"][0]["message"]["content"]
    choice.finish_reason = "stop"
    mock_response.choices.append(choice)
    
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 120
    mock_response.usage.total_tokens = 270
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_anthropic_client():
    """Anthropic Claude API クライアントのモック"""
    mock_client = Mock()
    
    # LLMレスポンスのサンプルデータを読み込み
    llm_response = load_fixture_json("llm_response_sample.json")
    
    # messages.create メソッドのモック
    mock_response = Mock()
    mock_response.content = []
    
    content = Mock()
    content.text = llm_response["anthropic_response"]["content"][0]["text"]
    mock_response.content.append(content)
    
    mock_response.stop_reason = "end_turn"
    mock_response.usage.input_tokens = 145
    mock_response.usage.output_tokens = 115
    
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_apis_disabled():
    """環境変数でAPIモックを無効化するかどうかを制御"""
    return os.getenv("DISABLE_API_MOCKS", "false").lower() == "true"


@pytest.fixture
def sample_image_path():
    """テスト用画像ファイルのパスを提供"""
    return SAMPLE_IMAGES_DIR / "chirashi_sample_01.jpg"


@pytest.fixture
def corrupted_image_path():
    """破損画像ファイルのパスを提供"""
    return SAMPLE_IMAGES_DIR / "corrupted_image.jpg"


@pytest.fixture
def expected_extraction_result():
    """期待される抽出結果を提供"""
    return load_fixture_json("extraction_result_01.json")


@pytest.fixture
def expected_ocr_response():
    """期待されるOCRレスポンスを提供"""
    return load_fixture_json("ocr_response_sample_01.json")


@pytest.fixture
def error_responses():
    """エラーレスポンス集を提供"""
    return load_fixture_json("error_responses.json")


@pytest.fixture(autouse=True)
def setup_test_environment(mock_apis_disabled):
    """
    テスト環境の自動セットアップ
    環境変数に基づいてAPIモックの有効/無効を制御
    """
    if not mock_apis_disabled:
        # APIモックが有効な場合のパッチ設定
        with patch.dict(os.environ, {"USE_MOCK_APIS": "true"}):
            yield
    else:
        # APIモックが無効な場合（実際のAPIを使用）
        yield


@pytest.fixture
def mock_config():
    """テスト用設定値を提供"""
    return {
        "max_image_size_mb": 10,
        "ocr_retry_count": 3,
        "processing_timeout_seconds": 30,
        "log_level": "INFO",
        "log_format": "json"
    }


# pytest設定
def pytest_configure(config):
    """pytest実行時の設定"""
    # テスト用のマーカーを登録
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring external API"
    )


def pytest_collection_modifyitems(config, items):
    """テスト収集時の処理"""
    # --mock-apis フラグが指定された場合の処理
    if config.getoption("--mock-apis", default=False):
        # 実際のAPIを使用するテストをスキップ
        skip_api = pytest.mark.skip(reason="API tests skipped due to --mock-apis flag")
        for item in items:
            if "api" in item.keywords:
                item.add_marker(skip_api)


def pytest_addoption(parser):
    """pytestコマンドラインオプションの追加"""
    parser.addoption(
        "--mock-apis",
        action="store_true",
        default=False,
        help="Run tests with mocked APIs only"
    )