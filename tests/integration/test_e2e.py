"""
E2E (End-to-End) Test Suite for Chirashi Extraction System

このファイルは実際のAPIを使用したエンドツーエンドテストを実装します。
- 実際のGoogle Cloud Vision API使用
- 実際のLLM API使用  
- 90%精度目標の検証
- 性能要件（5秒/画像、100枚/時間）の検証

TDD第1ステップ: 先にテストを作成し、NotImplementedErrorを確認する
"""

import pytest
import os
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch
import tempfile
from datetime import datetime

from src.pipeline import ChirashiPipeline


class TestE2EChirashiExtraction:
    """実際のAPIを使用したE2Eテストスイート"""
    
    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        # 実際のAPI使用設定（モックを無効化）
        self.real_api_config = {
            "use_mock": False,
            "ocr_provider": "google",
            "llm_provider": "openai", 
            "confidence_threshold": 0.7,
            "max_processing_time": 30,
            "enable_logging": True,
            "log_level": "INFO"
        }
        
        # テスト用画像パス
        self.test_image_path = "docs/images/chirashi_sample_01.jpg"
        
        # 出力ディレクトリ
        self.output_dir = tempfile.mkdtemp(prefix="e2e_test_")
        
        # パフォーマンステスト用のバッチサイズ
        self.batch_test_size = 10
        
    def teardown_method(self):
        """各テストメソッド実行後のクリーンアップ"""
        # テスト用出力ファイルの削除
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
    
    @pytest.mark.skipif(
        os.getenv("SKIP_REAL_API_TESTS", "true").lower() == "true",
        reason="実際のAPIテストはSKIP_REAL_API_TESTS=falseで有効化"
    )
    def test_real_google_cloud_vision_api_integration(self):
        """実際のGoogle Cloud Vision APIを使用した統合テスト
        
        受け入れ条件:
        - Google Cloud Vision APIからテキスト抽出が成功する
        - バウンディングボックス情報が取得できる
        - 信頼度スコアが取得できる
        - APIエラー時の適切なエラーハンドリング
        """
        # 事前条件：環境変数が設定されている
        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), "Google API認証情報が設定されていません"
        assert os.getenv("GOOGLE_CLOUD_PROJECT_ID"), "Google Cloud プロジェクトIDが設定されていません"
        
        # パイプライン初期化（実際のAPI使用）
        pipeline = ChirashiPipeline(config=self.real_api_config)
        
        # テスト画像の存在確認
        assert os.path.exists(self.test_image_path), f"テスト画像が存在しません: {self.test_image_path}"
        
        # 実際のOCR処理実行
        result = pipeline.process_single_image(
            image_path=self.test_image_path,
            output_path=os.path.join(self.output_dir, "vision_test.json")
        )
        
        # 結果検証
        assert result is not None, "OCR処理結果がNoneです"
        assert "extracted_data" in result, "extracted_dataキーが結果に含まれていません"
        assert len(result["extracted_data"]) > 0, "抽出されたデータが0件です"
        
        # データ構造検証
        for item in result["extracted_data"]:
            assert "product" in item, "商品名が含まれていません"
            assert "price_incl_tax" in item, "税込価格が含まれていません"
            assert "confidence" in item, "信頼度が含まれていません"
            assert isinstance(item["confidence"], float), "信頼度が数値ではありません"
            assert 0 <= item["confidence"] <= 1, "信頼度が0-1の範囲外です"
    
    @pytest.mark.skipif(
        os.getenv("SKIP_REAL_API_TESTS", "true").lower() == "true",
        reason="実際のAPIテストはSKIP_REAL_API_TESTS=falseで有効化"
    )
    def test_real_llm_api_integration(self):
        """実際のLLM API（OpenAI/Anthropic）を使用した統合テスト
        
        受け入れ条件:
        - LLM APIから商品・価格ペア抽出が成功する
        - カテゴリ分類が正しく動作する
        - プロンプトテンプレートが適切に動作する
        - APIレート制限への対応
        """
        # 事前条件：APIキーが設定されている
        api_key_exists = (
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY")
        )
        assert api_key_exists, "LLM API認証情報が設定されていません"
        
        # パイプライン初期化
        pipeline = ChirashiPipeline(config=self.real_api_config)
        
        # 実際のLLM処理実行
        result = pipeline.process_single_image(
            image_path=self.test_image_path,
            output_path=os.path.join(self.output_dir, "llm_test.json")
        )
        
        # LLM処理結果検証
        assert result is not None, "LLM処理結果がNoneです"
        assert "extracted_data" in result, "extracted_dataが含まれていません"
        
        # カテゴリ分類検証
        categories = ["食品", "日用品", "医薬品・化粧品", "衣料品", "家電・雑貨", "その他"]
        for item in result["extracted_data"]:
            assert "category" in item, "カテゴリが含まれていません"
            assert item["category"] in categories, f"無効なカテゴリ: {item['category']}"
    
    @pytest.mark.skipif(
        os.getenv("SKIP_REAL_API_TESTS", "true").lower() == "true",
        reason="実際のAPIテストはSKIP_REAL_API_TESTS=falseで有効化"
    )
    def test_accuracy_target_verification(self):
        """90%精度目標の検証テスト
        
        受け入れ条件:
        - 複数のテスト画像で90%以上の抽出精度を達成
        - 商品名・価格ペアの正確性検証
        - 手動検証済みの期待結果との比較
        - 精度計算ロジックの妥当性確認
        """
        # テスト用のゴールデンデータ（手動検証済み期待結果）
        golden_data_path = "tests/fixtures/expected_outputs/golden_standard.json"
        
        # ゴールデンデータが存在しない場合はスキップ
        if not os.path.exists(golden_data_path):
            pytest.skip("ゴールデンスタンダードデータが存在しないため精度テストをスキップします")
        
        # ゴールデンデータ読み込み
        with open(golden_data_path, 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
        
        pipeline = ChirashiPipeline(config=self.real_api_config)
        
        # 複数画像での精度検証
        total_items = 0
        correct_items = 0
        
        for test_case in golden_data.get("test_cases", []):
            image_path = test_case["image_path"]
            expected_items = test_case["expected_items"]
            
            if not os.path.exists(image_path):
                continue
                
            # 実際の抽出実行
            result = pipeline.process_single_image(
                image_path=image_path,
                output_path=os.path.join(self.output_dir, f"accuracy_test_{Path(image_path).stem}.json")
            )
            
            # 精度計算
            extracted_items = result.get("extracted_data", [])
            matches = self._calculate_accuracy(extracted_items, expected_items)
            
            total_items += len(expected_items)
            correct_items += matches
        
        # 精度検証
        if total_items > 0:
            accuracy = correct_items / total_items
            assert accuracy >= 0.90, f"精度目標未達成: {accuracy:.2%} < 90%"
            
            # 詳細ログ出力
            print(f"精度検証結果: {accuracy:.2%} ({correct_items}/{total_items})")
    
    @pytest.mark.skipif(
        os.getenv("SKIP_REAL_API_TESTS", "true").lower() == "true",
        reason="実際のAPIテストはSKIP_REAL_API_TESTS=falseで有効化"
    )
    def test_performance_requirements(self):
        """性能要件検証テスト（5秒/画像、100枚/時間）
        
        受け入れ条件:
        - 単一画像処理が5秒以内で完了
        - バッチ処理で100枚/時間の処理能力を達成
        - メモリ使用量が適切な範囲内
        - CPU使用率が過度でない
        """
        pipeline = ChirashiPipeline(config=self.real_api_config)
        
        # 単一画像処理時間測定
        start_time = time.time()
        result = pipeline.process_single_image(
            image_path=self.test_image_path,
            output_path=os.path.join(self.output_dir, "performance_single.json")
        )
        single_processing_time = time.time() - start_time
        
        # 5秒以内の処理時間検証
        assert single_processing_time <= 5.0, f"単一画像処理時間が5秒を超過: {single_processing_time:.2f}秒"
        
        # バッチ処理性能テスト（小規模）
        batch_images = [self.test_image_path] * self.batch_test_size
        
        start_time = time.time()
        batch_result = pipeline.process_batch(
            image_paths=batch_images,
            output_dir=self.output_dir
        )
        batch_processing_time = time.time() - start_time
        
        # バッチ処理結果検証
        assert batch_result is not None, "バッチ処理結果がNoneです"
        assert "success_count" in batch_result, "success_countが含まれていません"
        
        # 100枚/時間の処理能力検証（スケール推定）
        images_per_hour = (self.batch_test_size / batch_processing_time) * 3600
        assert images_per_hour >= 100, f"処理能力が100枚/時間を下回る: {images_per_hour:.1f}枚/時間"
        
        # パフォーマンス結果ログ出力
        print(f"単一画像処理時間: {single_processing_time:.2f}秒")
        print(f"バッチ処理能力: {images_per_hour:.1f}枚/時間")
    
    @pytest.mark.skipif(
        os.getenv("SKIP_REAL_API_TESTS", "true").lower() == "true",
        reason="実際のAPIテストはSKIP_REAL_API_TESTS=falseで有効化"
    )
    def test_full_pipeline_integration(self):
        """完全なパイプライン統合テスト
        
        受け入れ条件:
        - 画像入力からCSV/JSON出力までの完全フロー実行
        - 各モジュール間のデータ受け渡し検証
        - エラー処理・ログ出力の妥当性確認
        - 最終出力ファイルの妥当性検証
        """
        pipeline = ChirashiPipeline(config=self.real_api_config)
        
        # 完全なパイプライン実行
        json_output_path = os.path.join(self.output_dir, "full_pipeline.json")
        csv_output_path = os.path.join(self.output_dir, "full_pipeline.csv")
        
        # JSON出力テスト
        json_result = pipeline.process_single_image(
            image_path=self.test_image_path,
            output_path=json_output_path
        )
        
        # CSV出力テスト（設定変更）
        pipeline.configure({"output_format": "csv"})
        csv_result = pipeline.process_single_image(
            image_path=self.test_image_path,
            output_path=csv_output_path
        )
        
        # ファイル生成確認
        assert os.path.exists(json_output_path), "JSON出力ファイルが生成されていません"
        assert os.path.exists(csv_output_path), "CSV出力ファイルが生成されていません"
        
        # ファイル内容検証
        with open(json_output_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            assert isinstance(json_data, list), "JSON出力形式が不正です"
            assert len(json_data) > 0, "JSON出力が空です"
        
        # CSV内容検証（基本的なフォーマット確認）
        with open(csv_output_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
            assert "商品名" in csv_content, "CSVヘッダーに商品名が含まれていません"
            assert "税込価格" in csv_content, "CSVヘッダーに税込価格が含まれていません"
    
    def _calculate_accuracy(self, extracted_items: List[Dict[str, Any]], 
                           expected_items: List[Dict[str, Any]]) -> int:
        """抽出結果と期待結果の精度計算ヘルパーメソッド
        
        Args:
            extracted_items: 実際の抽出結果
            expected_items: 期待される抽出結果
            
        Returns:
            int: マッチした項目数
        """
        matches = 0
        
        for expected_item in expected_items:
            expected_product = expected_item.get("product", "").strip().lower()
            expected_price = expected_item.get("price_incl_tax")
            
            # 部分マッチング（商品名の類似性と価格の一致）
            for extracted_item in extracted_items:
                extracted_product = extracted_item.get("product", "").strip().lower()
                extracted_price = extracted_item.get("price_incl_tax")
                
                # 商品名の類似性チェック（簡易版）
                product_similarity = self._calculate_similarity(expected_product, extracted_product)
                price_match = abs(expected_price - extracted_price) <= 1 if expected_price and extracted_price else False
                
                # マッチング条件（商品名70%以上類似 かつ 価格が±1円以内）
                if product_similarity >= 0.7 and price_match:
                    matches += 1
                    break
        
        return matches
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """文字列類似度計算ヘルパーメソッド（簡易版）
        
        Args:
            text1: 比較文字列1
            text2: 比較文字列2
            
        Returns:
            float: 類似度（0.0-1.0）
        """
        if not text1 or not text2:
            return 0.0
        
        # 簡易的なレーベンシュタイン距離による類似度計算
        len1, len2 = len(text1), len(text2)
        if len1 == 0: return 0.0 if len2 > 0 else 1.0
        if len2 == 0: return 0.0
        
        # 完全一致
        if text1 == text2:
            return 1.0
        
        # 部分文字列マッチング
        if text1 in text2 or text2 in text1:
            return 0.8
        
        # 共通文字数による類似度（簡易版）
        common_chars = sum(1 for char in text1 if char in text2)
        similarity = common_chars / max(len1, len2)
        
        return similarity


# テスト実行時の環境変数設定例
"""
実際のAPIテストを実行する場合は以下の環境変数を設定:

export SKIP_REAL_API_TESTS=false
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export GOOGLE_CLOUD_PROJECT_ID=your-project-id
export OPENAI_API_KEY=your-openai-api-key

または

export ANTHROPIC_API_KEY=your-anthropic-api-key
"""