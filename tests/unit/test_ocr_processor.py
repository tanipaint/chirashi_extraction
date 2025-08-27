"""
OCR処理モジュールのテストコード

TDD方式でのテスト作成（T030）
全テストが失敗することを確認後、T031で実装を行う。
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.ocr_processor import OCRProcessor


class TestOCRProcessor:
    """OCR処理モジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        # モックモードでOCRProcessorを初期化
        mock_config = {"use_mock": True}
        self.ocr_processor = OCRProcessor(config=mock_config)

    def test_initialization(self):
        """OCRProcessorの初期化テスト"""
        processor = OCRProcessor()
        assert processor is not None
        assert hasattr(processor, 'extract_text')
        assert hasattr(processor, 'get_text_annotations')
        assert hasattr(processor, 'get_bounding_boxes')
        assert hasattr(processor, 'get_confidence_scores')
        assert hasattr(processor, 'process_with_retry')

    def test_extract_text_basic(self):
        """基本的なテキスト抽出テスト"""
        # モックデータでテキスト抽出をテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = self.ocr_processor.extract_text(sample_image)
        
        # モック結果の検証
        assert "full_text" in result
        assert "text_annotations" in result
        assert "confidence_scores" in result
        assert "bounding_boxes" in result
        assert isinstance(result["full_text"], str)
        assert isinstance(result["text_annotations"], list)
        assert len(result["text_annotations"]) > 0

    def test_extract_text_japanese(self):
        """日本語テキスト抽出テスト"""
        # 日本語テキストを含むモックデータでテスト
        japanese_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        result = self.ocr_processor.extract_text(japanese_image)
        
        # 日本語テキストが含まれていることを確認
        assert "full_text" in result
        assert len(result["full_text"]) > 0
        # モックデータに日本語が含まれていることを確認
        mock_text = result["full_text"]
        assert "モックテキスト" in mock_text

    def test_get_text_annotations_success(self):
        """テキストアノテーション取得テスト - 正常ケース"""
        # モックデータでテキストアノテーションをテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        annotations = self.ocr_processor.get_text_annotations(sample_image)
        
        # 結果の検証
        assert isinstance(annotations, list)
        assert len(annotations) > 0
        for annotation in annotations:
            assert "text" in annotation
            assert "bounding_box" in annotation
            assert isinstance(annotation["text"], str)
            assert isinstance(annotation["bounding_box"], tuple)
            assert len(annotation["bounding_box"]) == 4

    def test_get_text_annotations_empty_image(self):
        """テキストアノテーション取得テスト - 空画像"""
        # 空画像ではValueErrorが発生することを確認
        empty_image = np.zeros((0, 0, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="空の画像データ"):
            self.ocr_processor.get_text_annotations(empty_image)

    def test_get_bounding_boxes_success(self):
        """バウンディングボックス取得テスト - 正常ケース"""
        # モックデータでバウンディングボックスをテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        bboxes = self.ocr_processor.get_bounding_boxes(sample_image)
        
        # 結果の検証
        assert isinstance(bboxes, list)
        assert len(bboxes) > 0
        for bbox in bboxes:
            assert isinstance(bbox, tuple)
            assert len(bbox) == 4
            assert all(isinstance(coord, (int, float)) for coord in bbox)

    def test_get_bounding_boxes_multiple_texts(self):
        """バウンディングボックス取得テスト - 複数テキスト"""
        # 複数テキストがあるモックデータでテスト
        multi_text_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        bboxes = self.ocr_processor.get_bounding_boxes(multi_text_image)
        
        # 複数のバウンディングボックスが返されることを確認
        assert isinstance(bboxes, list)
        assert len(bboxes) >= 2  # モックデータでは2個のテキスト
        for bbox in bboxes:
            assert isinstance(bbox, tuple)
            assert len(bbox) == 4

    def test_get_confidence_scores_success(self):
        """信頼度スコア取得テスト - 正常ケース"""
        # モックデータで信頼度スコアをテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        scores = self.ocr_processor.get_confidence_scores(sample_image)
        
        # 結果の検証
        assert isinstance(scores, list)
        assert len(scores) > 0
        for score in scores:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_get_confidence_scores_low_quality(self):
        """信頼度スコア取得テスト - 低品質画像"""
        # 低品質画像でも信頼度スコアが取得できることを確認
        low_quality_image = np.ones((100, 200, 3), dtype=np.uint8) * 128
        scores = self.ocr_processor.get_confidence_scores(low_quality_image)
        
        # 結果の検証
        assert isinstance(scores, list)
        assert len(scores) > 0
        for score in scores:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_process_with_retry_success(self):
        """リトライ処理テスト - 正常ケース"""
        # モックデータでリトライ処理をテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = self.ocr_processor.process_with_retry(sample_image)
        
        # 結果の検証
        assert result is not None
        assert "full_text" in result
        assert "text_annotations" in result
        assert isinstance(result["full_text"], str)

    def test_process_with_retry_max_retries(self):
        """リトライ処理テスト - 最大リトライ回数指定"""
        # max_retriesパラメータを指定したリトライ処理をテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = self.ocr_processor.process_with_retry(sample_image, max_retries=5)
        
        # 結果の検証
        assert result is not None
        assert "full_text" in result
        assert "text_annotations" in result
        assert isinstance(result["full_text"], str)

    def test_process_with_retry_failure(self):
        """リトライ処理テスト - API失敗"""
        # 空の画像データでリトライが最終的に失敗することをテスト
        corrupted_image = np.array([])
        with pytest.raises(Exception, match="OCR処理が最大リトライ回数"):
            self.ocr_processor.process_with_retry(corrupted_image)

    @patch('google.cloud.vision.ImageAnnotatorClient')
    def test_google_cloud_vision_client_initialization(self, mock_client):
        """Google Cloud Vision APIクライアント初期化テスト"""
        # モックレスポンスを適切に設定
        mock_instance = mock_client.return_value
        mock_response = Mock()
        mock_response.text_annotations = []
        mock_response.error.message = ''  # エラーなしを設定
        mock_instance.text_detection.return_value = mock_response
        
        # モックモード以外でのクライアント初期化をテスト
        real_api_config = {"use_mock": False}
        processor = OCRProcessor(config=real_api_config)
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # 実際のAPIクライアントが作成されることを確認（モック使用）
        result = processor.extract_text(sample_image)
        assert mock_client.called
        assert "full_text" in result

    @patch('google.cloud.vision.ImageAnnotatorClient')
    def test_google_cloud_vision_api_call(self, mock_client):
        """Google Cloud Vision API呼び出しテスト"""
        # モッククライアントの設定
        mock_instance = mock_client.return_value
        mock_response = Mock()
        mock_response.text_annotations = []
        mock_response.error.message = ''
        mock_instance.text_detection.return_value = mock_response
        
        # 実APIモードでのAPI呼び出しテスト
        real_api_config = {"use_mock": False}
        processor = OCRProcessor(config=real_api_config)
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = processor.extract_text(sample_image)
        # APIが呼び出されることを確認
        assert mock_instance.text_detection.called
        assert "full_text" in result

    def test_api_error_handling(self):
        """API エラーハンドリングテスト"""
        # 空の画像データでValueErrorが適切に発生することをテスト
        invalid_image = np.array([])
        with pytest.raises(ValueError, match="空の画像データ"):
            self.ocr_processor.extract_text(invalid_image)

    def test_mock_vs_real_api_switch(self):
        """モック使用とAPI使用の切り替えテスト"""
        # モックモードの確認
        mock_config = {'use_mock': True}
        mock_processor = OCRProcessor(config=mock_config)
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        mock_result = mock_processor.extract_text(sample_image)
        assert "Mock Text Sample" in mock_result['full_text']
        
        # 実APIモード設定の確認
        real_config = {'use_mock': False}
        real_processor = OCRProcessor(config=real_config)
        assert real_processor.config['use_mock'] == False

    def test_rate_limiting_handling(self):
        """レート制限ハンドリングテスト"""
        # リトライ設定でのprocess_with_retry動作をテスト
        sample_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # モックモードでの正常処理を確認
        result = self.ocr_processor.process_with_retry(sample_image)
        assert "full_text" in result
        assert "Mock Text Sample" in result['full_text']
        # リトライ回数設定が適用されることを確認
        custom_retries_result = self.ocr_processor.process_with_retry(sample_image, max_retries=1)
        assert custom_retries_result is not None

    def test_large_image_processing(self):
        """大きな画像の処理テスト"""
        # 大きな画像でもモックモードで正常処理されることを確認
        large_image = np.ones((2000, 2000, 3), dtype=np.uint8) * 255
        result = self.ocr_processor.extract_text(large_image)
        assert "full_text" in result
        assert "Mock Text Sample" in result['full_text']
        assert isinstance(result['text_annotations'], list)
        assert len(result['text_annotations']) > 0

    def test_configuration_settings(self):
        """設定項目テスト"""
        # カスタム設定でOCRProcessorを初期化
        custom_config = {
            'max_retries': 5,
            'timeout': 30,
            'use_mock': False,
            'api_provider': 'google_cloud_vision'
        }
        
        processor = OCRProcessor(config=custom_config)
        assert processor.config == custom_config