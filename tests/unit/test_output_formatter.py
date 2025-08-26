"""
出力整形モジュールのテストコード

TDD方式でのテスト作成（T070）
全テストが失敗することを確認後、T071で実装を行う。
"""

import pytest
import json
import pandas as pd
import tempfile
import os
from datetime import datetime
from src.output_formatter import OutputFormatter


class TestOutputFormatter:
    """出力整形モジュールのテストクラス"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.formatter = OutputFormatter()
        self.sample_data = [
            {
                "product": "きゅうり3本",
                "price_incl_tax": 198,
                "price_excl_tax": 180,
                "unit": "3本",
                "category": "食品",
                "confidence": 0.95
            },
            {
                "product": "サントリー天然水 2L",
                "price_incl_tax": 98,
                "price_excl_tax": 90,
                "unit": "1本",
                "category": "食品",
                "confidence": 0.92
            }
        ]

    def test_initialization(self):
        """OutputFormatterの初期化テスト"""
        formatter = OutputFormatter()
        assert formatter is not None
        assert hasattr(formatter, 'to_csv')
        assert hasattr(formatter, 'to_json')
        assert hasattr(formatter, 'generate_filename')

    def test_to_csv_basic(self):
        """基本的なCSV出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output.csv")
            result = self.formatter.to_csv(self.sample_data, output_path)
            assert result is True
            assert os.path.exists(output_path)
            
            # CSVファイルの内容確認
            df = pd.read_csv(output_path)
            assert len(df) == 2
            assert "商品名" in df.columns
            assert "税込価格" in df.columns
            assert df.iloc[0]["商品名"] == "きゅうり3本"

    def test_to_csv_with_custom_path(self):
        """カスタムパス指定CSV出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "custom_output.csv")
            result = self.formatter.to_csv(self.sample_data, output_path)
            assert result is True
            assert os.path.exists(output_path)

    def test_to_csv_empty_data(self):
        """空データでのCSV出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "empty_output.csv")
            empty_data = []
            result = self.formatter.to_csv(empty_data, output_path)
            assert result is True
            assert os.path.exists(output_path)
            
            # 空のCSVファイルでもヘッダーは存在
            df = pd.read_csv(output_path)
            assert len(df) == 0
            assert "商品名" in df.columns

    def test_to_csv_single_item(self):
        """単一アイテムCSV出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "single_output.csv")
            single_item = [self.sample_data[0]]
            result = self.formatter.to_csv(single_item, output_path)
            assert result is True
            assert os.path.exists(output_path)
            
            df = pd.read_csv(output_path)
            assert len(df) == 1

    def test_to_json_basic(self):
        """基本的なJSON出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_output.json")
            result = self.formatter.to_json(self.sample_data, output_path)
            assert result is True
            assert os.path.exists(output_path)
            
            # JSONファイルの内容確認
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert len(data) == 2
            assert data[0]["product"] == "きゅうり3本"

    def test_to_json_with_custom_path(self):
        """カスタムパス指定JSON出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "custom_output.json")
            result = self.formatter.to_json(self.sample_data, output_path)
            assert result is True
            assert os.path.exists(output_path)

    def test_to_json_empty_data(self):
        """空データでのJSON出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "empty_output.json")
            empty_data = []
            result = self.formatter.to_json(empty_data, output_path)
            assert result is True
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data == []

    def test_to_json_single_item(self):
        """単一アイテムJSON出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "single_output.json")
            single_item = [self.sample_data[0]]
            result = self.formatter.to_json(single_item, output_path)
            assert result is True
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert len(data) == 1

    def test_generate_filename_csv(self):
        """CSV用ファイル名生成テスト"""
        filename = self.formatter.generate_filename("csv")
        assert filename.endswith(".csv")
        assert "chirashi_result_" in filename
        assert len(filename.split("_")) >= 3  # prefix_YYYYMMDD_HHMMSS.csv

    def test_generate_filename_json(self):
        """JSON用ファイル名生成テスト"""
        filename = self.formatter.generate_filename("json")
        assert filename.endswith(".json")
        assert "chirashi_result_" in filename

    def test_generate_filename_with_prefix(self):
        """プレフィックス付きファイル名生成テスト"""
        filename = self.formatter.generate_filename("csv", prefix="chirashi_001")
        assert filename.startswith("chirashi_001_")
        assert filename.endswith(".csv")

    def test_generate_filename_invalid_format(self):
        """無効な形式でのファイル名生成テスト"""
        with pytest.raises(ValueError, match="Unsupported format type"):
            self.formatter.generate_filename("invalid_format")

    def test_csv_schema_compliance(self):
        """CSV出力のスキーマ準拠テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "schema_test.csv")
            expected_columns = ["商品名", "税込価格", "税抜価格", "単位", "カテゴリ", "信頼度"]
            result = self.formatter.to_csv(self.sample_data, output_path)
            assert result is True
            
            df = pd.read_csv(output_path)
            for col in expected_columns:
                assert col in df.columns

    def test_json_schema_compliance(self):
        """JSON出力のスキーマ準拠テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "schema_test.json")
            result = self.formatter.to_json(self.sample_data, output_path)
            assert result is True
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # JSONスキーマの確認
            for item in data:
                assert "product" in item
                assert "price_incl_tax" in item
                assert "confidence" in item

    def test_special_characters_handling(self):
        """特殊文字を含むデータの出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            special_data = [
                {
                    "product": "商品名「特殊文字」テスト,改行\n含む",
                    "price_incl_tax": 100,
                    "price_excl_tax": None,
                    "unit": "1個",
                    "category": "その他",
                    "confidence": 0.85
                }
            ]
            
            csv_path = os.path.join(temp_dir, "special_chars.csv")
            json_path = os.path.join(temp_dir, "special_chars.json")
            
            # CSV出力テスト
            result = self.formatter.to_csv(special_data, csv_path)
            assert result is True
            assert os.path.exists(csv_path)
            
            # JSON出力テスト
            result = self.formatter.to_json(special_data, json_path)
            assert result is True
            assert os.path.exists(json_path)

    def test_null_values_handling(self):
        """null値を含むデータの出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            null_data = [
                {
                    "product": "商品名のみ",
                    "price_incl_tax": 100,
                    "price_excl_tax": None,
                    "unit": None,
                    "category": "その他",
                    "confidence": 0.75
                }
            ]
            
            csv_path = os.path.join(temp_dir, "null_values.csv")
            json_path = os.path.join(temp_dir, "null_values.json")
            
            result = self.formatter.to_csv(null_data, csv_path)
            assert result is True
            
            result = self.formatter.to_json(null_data, json_path)
            assert result is True

    def test_large_dataset_handling(self):
        """大量データセットの出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            large_data = []
            for i in range(1000):
                large_data.append({
                    "product": f"商品{i}",
                    "price_incl_tax": 100 + i,
                    "price_excl_tax": 90 + i,
                    "unit": "1個",
                    "category": "その他",
                    "confidence": 0.8
                })
            
            csv_path = os.path.join(temp_dir, "large_dataset.csv")
            json_path = os.path.join(temp_dir, "large_dataset.json")
            
            result = self.formatter.to_csv(large_data, csv_path)
            assert result is True
            
            result = self.formatter.to_json(large_data, json_path)
            assert result is True
            
            # ファイルサイズの確認
            assert os.path.getsize(csv_path) > 0
            assert os.path.getsize(json_path) > 0

    def test_encoding_utf8(self):
        """UTF-8エンコーディングテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            japanese_data = [
                {
                    "product": "日本語商品名テスト",
                    "price_incl_tax": 298,
                    "price_excl_tax": 271,
                    "unit": "100g",
                    "category": "食品",
                    "confidence": 0.90
                }
            ]
            
            csv_path = os.path.join(temp_dir, "utf8_test.csv")
            json_path = os.path.join(temp_dir, "utf8_test.json")
            
            result = self.formatter.to_csv(japanese_data, csv_path)
            assert result is True
            
            result = self.formatter.to_json(japanese_data, json_path)
            assert result is True
            
            # UTF-8エンコーディングの確認
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "日本語商品名テスト" in content