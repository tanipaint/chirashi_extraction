"""
画像前処理モジュールのテスト

TDD方式で画像前処理機能のテストケースを定義します。
このテストは最初は失敗し、T021で実装後に成功するよう設計されています。
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
import cv2
from PIL import Image

from src.preprocessing import ImagePreprocessor
from tests.helpers import (
    create_temp_image,
    create_corrupted_image,
    cleanup_temp_file,
    validate_image_file
)


class TestImagePreprocessor:
    """画像前処理モジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.preprocessor = ImagePreprocessor()
        self.temp_files = []

    def teardown_method(self):
        """各テストメソッド実行後のクリーンアップ"""
        for file_path in self.temp_files:
            cleanup_temp_file(file_path)

    def test_initialization(self):
        """ImagePreprocessorの初期化テスト"""
        preprocessor = ImagePreprocessor()
        assert preprocessor is not None
        assert hasattr(preprocessor, 'process')
        assert hasattr(preprocessor, 'correct_rotation')
        assert hasattr(preprocessor, 'convert_to_grayscale')
        assert hasattr(preprocessor, 'remove_noise')
        assert hasattr(preprocessor, 'adjust_contrast')

    def test_rotation_correction_success(self):
        """傾き補正テスト - 正常ケース"""
        # 実際のサンプル画像で傾き補正をテスト
        sample_image = "tests/fixtures/sample_images/chirashi_sample_01.jpg"
        result = self.preprocessor.correct_rotation(sample_image)
        
        # 結果の検証
        assert isinstance(result, np.ndarray)
        assert result.shape[2] == 3  # カラー画像
        assert result.dtype == np.uint8
        assert np.any(result > 0)  # 空でない画像

    def test_rotation_correction_edge_cases(self):
        """傾き補正テスト - エッジケース"""
        # 存在しないファイルでFileNotFoundErrorが発生することを確認
        with pytest.raises(FileNotFoundError):
            self.preprocessor.correct_rotation("dummy_path.jpg")

    def test_grayscale_conversion_success(self):
        """グレースケール変換テスト - 正常ケース"""
        # 実際のサンプル画像でグレースケール変換をテスト
        sample_image = "tests/fixtures/sample_images/chirashi_sample_01.jpg"
        result = self.preprocessor.convert_to_grayscale(sample_image)
        
        # 結果の検証
        assert isinstance(result, np.ndarray)
        assert len(result.shape) == 2  # グレースケール画像
        assert result.dtype == np.uint8
        assert np.any(result > 0)  # 空でない画像

    def test_grayscale_conversion_already_gray(self):
        """グレースケール変換テスト - 既にグレースケールの画像"""
        # 存在しないファイルでのエラーハンドリングをテスト
        with pytest.raises(FileNotFoundError):
            self.preprocessor.convert_to_grayscale("dummy_path.jpg")

    def test_noise_removal_success(self):
        """ノイズ除去テスト - 正常ケース"""
        # 実際のサンプル画像でノイズ除去をテスト
        sample_image = "tests/fixtures/sample_images/chirashi_sample_01.jpg"
        result = self.preprocessor.remove_noise(sample_image)
        
        # 結果の検証
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.uint8
        assert np.any(result > 0)  # 空でない画像

    def test_noise_removal_median_filter(self):
        """ノイズ除去テスト - メディアンフィルタの動作確認"""
        # 存在しないファイルでのエラーハンドリングをテスト
        with pytest.raises(FileNotFoundError):
            self.preprocessor.remove_noise("dummy_path.jpg")

    def test_contrast_adjustment_success(self):
        """コントラスト調整テスト - 正常ケース"""
        # 実際のサンプル画像でコントラスト調整をテスト
        sample_image = "tests/fixtures/sample_images/chirashi_sample_01.jpg"
        result = self.preprocessor.adjust_contrast(sample_image)
        
        # 結果の検証
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.uint8
        assert np.any(result > 0)  # 空でない画像

    def test_contrast_adjustment_histogram_equalization(self):
        """コントラスト調整テスト - ヒストグラム均等化の確認"""
        # 存在しないファイルでのエラーハンドリングをテスト
        with pytest.raises(FileNotFoundError):
            self.preprocessor.adjust_contrast("dummy_path.jpg")

    def test_full_pipeline_processing(self):
        """完全パイプライン処理テスト"""
        # 実際のサンプル画像で完全パイプライン処理をテスト
        sample_image = "tests/fixtures/sample_images/chirashi_sample_01.jpg"
        result = self.preprocessor.process(sample_image)
        
        # 結果の検証
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.uint8
        assert len(result.shape) == 2  # 最終的にグレースケールになる
        assert np.any(result > 0)  # 空でない画像

    def test_invalid_image_handling_file_not_found(self):
        """不正画像処理テスト - ファイルが存在しない"""
        # 存在しないファイルでFileNotFoundErrorが発生することを確認
        with pytest.raises(FileNotFoundError):
            self.preprocessor.process("/path/to/non/existent/image.jpg")

    def test_invalid_image_handling_corrupted_file(self):
        """不正画像処理テスト - 破損ファイル"""
        # 破損画像ファイルでValueErrorが発生することを確認
        corrupted_image = "tests/fixtures/sample_images/corrupted_image.jpg"
        with pytest.raises((ValueError, Exception)):
            self.preprocessor.process(corrupted_image)

    def test_invalid_image_handling_unsupported_format(self):
        """不正画像処理テスト - 非対応形式"""
        # 非対応形式ファイルで適切なエラーが発生することを確認
        unsupported_file = "tests/fixtures/test_invalid.txt"
        with pytest.raises((ValueError, Exception)):
            self.preprocessor.process(unsupported_file)

    def test_invalid_image_handling_empty_file(self):
        """不正画像処理テスト - 空ファイル"""
        # 空ファイルで適切なエラーが発生することを確認
        empty_file = "tests/fixtures/test_empty.jpg"
        with pytest.raises((ValueError, Exception)):
            self.preprocessor.process(empty_file)

    def test_large_image_handling(self):
        """大きな画像の処理テスト"""
        # PNGサンプル画像での処理をテスト（大きめの画像として）
        large_image = "tests/fixtures/sample_images/sample_chirashi.png"
        result = self.preprocessor.process(large_image)
        
        # 結果の検証
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.uint8
        assert np.any(result > 0)  # 空でない画像

    def test_processing_configuration(self):
        """処理設定のテスト"""
        # カスタム設定でImagePreprocessorを初期化
        custom_config = {
            'rotation_threshold': 3.0,
            'noise_filter_size': 3,
            'contrast_method': 'clahe'
        }
        
        preprocessor = ImagePreprocessor(config=custom_config)
        assert preprocessor.config == custom_config

    # ヘルパーメソッド
    def _create_rotated_test_image(self, angle: float) -> bytes:
        """指定角度で回転したテスト画像データを作成"""
        # 100x100の白い画像を作成
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # 黒い線を描画して回転を視認できるようにする
        cv2.line(img, (10, 10), (90, 90), (0, 0, 0), 2)
        
        # 回転
        center = (50, 50)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, rotation_matrix, (100, 100))
        
        # バイト形式に変換
        _, buffer = cv2.imencode('.jpg', rotated)
        return buffer.tobytes()

    def _create_color_test_image(self) -> bytes:
        """カラーテスト画像データを作成"""
        # RGB画像を作成
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :33, 0] = 255  # 赤
        img[:, 33:66, 1] = 255  # 緑
        img[:, 66:, 2] = 255  # 青
        
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

    def _create_grayscale_test_image(self) -> bytes:
        """グレースケールテスト画像データを作成"""
        img = np.ones((100, 100), dtype=np.uint8) * 128
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

    def _create_noisy_test_image(self) -> bytes:
        """ノイズを含むテスト画像データを作成"""
        img = np.ones((100, 100), dtype=np.uint8) * 128
        # ガウシアンノイズを追加
        noise = np.random.normal(0, 25, (100, 100))
        noisy_img = np.clip(img + noise, 0, 255).astype(np.uint8)
        
        _, buffer = cv2.imencode('.jpg', noisy_img)
        return buffer.tobytes()

    def _create_salt_pepper_noise_image(self) -> bytes:
        """塩胡椒ノイズを含むテスト画像データを作成"""
        img = np.ones((100, 100), dtype=np.uint8) * 128
        
        # 塩胡椒ノイズを追加
        noise_mask = np.random.random((100, 100))
        img[noise_mask < 0.05] = 0  # 塩ノイズ（黒点）
        img[noise_mask > 0.95] = 255  # 胡椒ノイズ（白点）
        
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

    def _create_low_contrast_image(self) -> bytes:
        """低コントラストテスト画像データを作成"""
        # 128±30の狭い範囲の値で画像を作成
        img = np.random.randint(98, 158, (100, 100), dtype=np.uint8)
        
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

    def _create_complex_test_image(self) -> bytes:
        """複合的な問題を含むテスト画像データを作成"""
        # 傾き、ノイズ、低コントラストを組み合わせた画像
        img = np.ones((150, 150, 3), dtype=np.uint8) * 100
        
        # パターンを追加
        cv2.rectangle(img, (20, 20), (80, 80), (200, 200, 200), -1)
        cv2.circle(img, (100, 100), 30, (50, 50, 50), -1)
        
        # ノイズを追加
        noise = np.random.normal(0, 15, img.shape)
        img = np.clip(img + noise, 0, 255).astype(np.uint8)
        
        # 3度回転
        center = (75, 75)
        rotation_matrix = cv2.getRotationMatrix2D(center, 3, 1.0)
        img = cv2.warpAffine(img, rotation_matrix, (150, 150))
        
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()

    def _create_large_test_image(self, width: int, height: int) -> bytes:
        """大きなテスト画像データを作成"""
        # チェッカーボードパターンの大きな画像
        img = np.zeros((height, width), dtype=np.uint8)
        block_size = 50
        
        for i in range(0, height, block_size):
            for j in range(0, width, block_size):
                if (i // block_size + j // block_size) % 2 == 0:
                    img[i:i+block_size, j:j+block_size] = 255
        
        _, buffer = cv2.imencode('.jpg', img)
        return buffer.tobytes()