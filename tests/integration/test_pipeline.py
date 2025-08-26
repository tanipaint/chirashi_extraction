"""
パイプライン統合テストコード

TDD方式でのテスト作成（T080）
全テストが失敗することを確認後、T081で実装を行う。
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from src.pipeline import ChirashiPipeline


class TestChirashiPipeline:
    """パイプライン統合テストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        # モックモードでパイプラインを初期化
        mock_config = {
            "use_mock": True,
            "confidence_threshold": 0.5
        }
        self.pipeline = ChirashiPipeline(config=mock_config)
        self.sample_image_path = "tests/fixtures/sample_images/chirashi_sample_01.jpg"
        self.sample_pdf_path = "tests/fixtures/sample_images/sample_chirashi.pdf"

    def test_initialization(self):
        """ChirashiPipelineの初期化テスト"""
        pipeline = ChirashiPipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'process_single_image')
        assert hasattr(pipeline, 'process_batch')
        assert hasattr(pipeline, 'configure')

    def test_process_single_image_jpg(self):
        """単一JPG画像処理のE2Eテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "result.json")
            
            result = self.pipeline.process_single_image(
                image_path=self.sample_image_path,
                output_path=output_path,
                output_format="json"
            )
            
            # 処理結果の検証
            assert result is not None
            assert isinstance(result, list)
            assert len(result) > 0
            
            # 出力ファイルの存在確認
            assert os.path.exists(output_path)
            
            # データ構造の検証
            first_item = result[0]
            assert "product" in first_item
            assert "price_incl_tax" in first_item
            assert "category" in first_item
            assert "confidence" in first_item

    def test_process_batch_images(self):
        """バッチ処理テスト（複数画像）"""
        image_paths = [
            "tests/fixtures/sample_images/chirashi_sample_01.jpg",
            "tests/fixtures/sample_images/sample_chirashi.jpg"
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            results = self.pipeline.process_batch(
                image_paths=image_paths,
                output_dir=temp_dir,
                output_format="json"
            )
            
            # バッチ処理結果の検証
            assert results is not None
            assert isinstance(results, dict)
            assert len(results) == len(image_paths)

    def test_error_propagation_missing_file(self):
        """エラー伝播テスト（存在しないファイル）"""
        missing_file_path = "tests/fixtures/sample_images/nonexistent.jpg"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "error_result.json")
            
            with pytest.raises(FileNotFoundError):
                self.pipeline.process_single_image(
                    image_path=missing_file_path,
                    output_path=output_path,
                    output_format="json"
                )

    def test_performance_single_image_under_5_seconds(self):
        """パフォーマンステスト（5秒以内）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "performance_test.json")
            
            start_time = time.time()
            
            result = self.pipeline.process_single_image(
                image_path=self.sample_image_path,
                output_path=output_path,
                output_format="json"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 5秒以内の処理時間を確認
            assert processing_time < 5.0
            assert result is not None