"""
チラシ抽出パイプライン統合モジュール

全モジュールを統合した処理パイプラインを提供
"""

import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

from src.preprocessing import ImagePreprocessor
from src.ocr_processor import OCRProcessor
from src.extractor import ProductPriceExtractor
from src.categorizer import ProductCategorizer
from src.validator import ProductValidator
from src.output_formatter import OutputFormatter


class ChirashiPipeline:
    """チラシ抽出パイプラインクラス"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化メソッド
        
        Args:
            config: 設定辞書（省略可）
        """
        self.config = config or {}
        
        # デフォルト設定
        self.default_config = {
            "ocr_provider": "google",
            "llm_provider": "anthropic", 
            "confidence_threshold": 0.7,
            "max_processing_time": 30,
            "enable_logging": True,
            "log_level": "INFO",
            "output_format": "json"
        }
        
        # 設定をマージ
        self.config = {**self.default_config, **self.config}
        
        # ロガー設定
        self._setup_logging()
        
        # 各モジュールを初期化
        try:
            self.preprocessor = ImagePreprocessor()
            self.ocr_processor = OCRProcessor(config=self.config)
            self.extractor = ProductPriceExtractor(config=self.config)
            self.categorizer = ProductCategorizer(config=self.config)
            self.validator = ProductValidator()
            self.formatter = OutputFormatter(config=self.config)
            
            logging.info("ChirashiPipeline initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize pipeline modules: {e}")
            raise

    def _setup_logging(self):
        """ログ設定をセットアップ"""
        if self.config.get("enable_logging", True):
            log_level = getattr(logging, self.config.get("log_level", "INFO").upper())
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def process_single_image(
        self,
        image_path: str,
        output_path: str,
        output_format: str = "json"
    ) -> List[Dict[str, Any]]:
        """
        単一画像を処理する
        
        Args:
            image_path: 入力画像パス
            output_path: 出力ファイルパス
            output_format: 出力形式（"json" or "csv"）
            
        Returns:
            List[Dict[str, Any]]: 抽出された商品データのリスト
            
        Raises:
            FileNotFoundError: 画像ファイルが存在しない場合
            ValueError: サポートされていない出力形式の場合
        """
        start_time = datetime.now()
        logging.info(f"Starting single image processing: {image_path}")
        
        try:
            # 入力ファイル存在確認
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # 出力形式バリデーション
            if output_format.lower() not in ["json", "csv"]:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Step 1: 画像前処理
            logging.info("Step 1/6: Image preprocessing")
            preprocessed_image = self.preprocessor.process(image_path)
            
            # Step 2: OCR処理
            logging.info("Step 2/6: OCR processing")
            ocr_result = self.ocr_processor.extract_text(preprocessed_image)
            
            # Step 3: 商品・価格ペア抽出
            logging.info("Step 3/6: Product-price extraction")
            extracted_products = self.extractor.extract_product_price_pairs(ocr_result)
            
            # Step 4: カテゴリ分類
            logging.info("Step 4/6: Category classification")
            categorized_products = []
            for product in extracted_products:
                category_result = self.categorizer.categorize_product(product["product"])
                product["category"] = category_result.category
                product["confidence"] = min(product.get("confidence", 1.0), category_result.confidence)
                categorized_products.append(product)
            
            # Step 5: データ検証
            logging.info("Step 5/6: Data validation")
            validated_products = []
            for product in categorized_products:
                validation_result = self.validator.validate_product_data(product)
                if validation_result.is_valid:
                    # 検証結果の信頼度を反映
                    product["confidence"] = min(product["confidence"], validation_result.confidence_score)
                    validated_products.append(product)
                else:
                    logging.warning(f"Product validation failed: {product.get('product', 'Unknown')} - {validation_result.validation_errors}")
            
            # 信頼度閾値フィルタリング
            confidence_threshold = self.config.get("confidence_threshold", 0.7)
            filtered_products = [
                p for p in validated_products 
                if p.get("confidence", 0) >= confidence_threshold
            ]
            
            # Step 6: 出力整形
            logging.info("Step 6/6: Output formatting")
            if output_format.lower() == "json":
                success = self.formatter.to_json(filtered_products, output_path)
            else:  # csv
                success = self.formatter.to_csv(filtered_products, output_path)
            
            if not success:
                raise RuntimeError(f"Failed to write output file: {output_path}")
            
            # 処理時間計算
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logging.info(f"Processing completed successfully in {processing_time:.2f}s")
            logging.info(f"Extracted {len(filtered_products)} products (filtered from {len(categorized_products)})")
            
            return filtered_products
            
        except Exception as e:
            logging.error(f"Error in single image processing: {e}")
            raise

    def process_batch(
        self,
        image_paths: Optional[List[str]] = None,
        input_dir: Optional[str] = None,
        output_dir: str = "output",
        output_format: str = "json"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        複数画像を一括処理する
        
        Args:
            image_paths: 画像パスのリスト（オプション）
            input_dir: 入力ディレクトリパス（オプション）
            output_dir: 出力ディレクトリパス
            output_format: 出力形式（"json" or "csv"）
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: 画像パス毎の抽出結果
        """
        start_time = datetime.now()
        logging.info("Starting batch processing")
        
        try:
            # 処理対象ファイルリストを生成
            target_files = []
            
            if image_paths:
                target_files = image_paths
            elif input_dir:
                if not os.path.exists(input_dir):
                    raise FileNotFoundError(f"Input directory not found: {input_dir}")
                
                # サポートされる画像形式
                supported_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
                
                for file_path in Path(input_dir).glob("*"):
                    if file_path.suffix.lower() in supported_extensions:
                        target_files.append(str(file_path))
            else:
                raise ValueError("Either image_paths or input_dir must be provided")
            
            if not target_files:
                logging.warning("No valid image files found for processing")
                return {}
            
            # 出力ディレクトリを作成
            os.makedirs(output_dir, exist_ok=True)
            
            # バッチ処理実行
            results = {}
            successful_count = 0
            failed_count = 0
            
            for i, image_path in enumerate(target_files, 1):
                try:
                    logging.info(f"Processing image {i}/{len(target_files)}: {os.path.basename(image_path)}")
                    
                    # 出力ファイル名生成
                    base_name = Path(image_path).stem
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"chirashi_result_{base_name}_{timestamp}.{output_format}"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # 単一画像処理
                    result = self.process_single_image(image_path, output_path, output_format)
                    results[image_path] = result
                    successful_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to process {image_path}: {e}")
                    results[image_path] = []
                    failed_count += 1
                    continue
            
            # 処理時間計算
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            logging.info(f"Batch processing completed in {total_time:.2f}s")
            logging.info(f"Successful: {successful_count}, Failed: {failed_count}")
            
            return results
            
        except Exception as e:
            logging.error(f"Error in batch processing: {e}")
            raise

    def configure(self, config: Dict[str, Any]) -> None:
        """
        パイプライン設定を更新する
        
        Args:
            config: 新しい設定辞書
        """
        logging.info("Updating pipeline configuration")
        
        try:
            # 設定を更新
            self.config.update(config)
            
            # ログレベル更新
            if "log_level" in config:
                log_level = getattr(logging, config["log_level"].upper())
                logging.getLogger().setLevel(log_level)
            
            # 各モジュールの設定も更新
            for module in [self.ocr_processor, self.extractor, self.categorizer, 
                          self.validator, self.formatter]:
                if hasattr(module, 'update_config'):
                    module.update_config(config)
            
            logging.info("Configuration updated successfully")
            
        except Exception as e:
            logging.error(f"Error updating configuration: {e}")
            raise


def main():
    """CLIエントリーポイント"""
    # 環境変数を.envから読み込み
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="チラシ商品価格抽出システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s image.jpg --output result.json
  %(prog)s --batch input_dir/ --output-dir results/
  %(prog)s image.jpg --format csv --confidence 0.8
        """
    )
    
    # 必須引数
    parser.add_argument(
        'input', 
        nargs='?',
        help='入力画像ファイルまたはディレクトリパス'
    )
    
    # オプション引数
    parser.add_argument(
        '--output', '-o',
        help='出力ファイルパス（単一画像処理時）'
    )
    
    parser.add_argument(
        '--output-dir', '-d',
        default='output',
        help='出力ディレクトリパス（バッチ処理時、デフォルト: output）'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv'],
        default='json',
        help='出力形式（デフォルト: json）'
    )
    
    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='バッチ処理モード'
    )
    
    parser.add_argument(
        '--confidence', '-c',
        type=float,
        default=0.7,
        help='信頼度閾値（デフォルト: 0.7）'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='ログレベル（デフォルト: INFO）'
    )
    
    parser.add_argument(
        '--config',
        help='設定ファイルパス（JSON形式）'
    )
    
    args = parser.parse_args()
    
    # 設定読み込み
    config = {
        "confidence_threshold": args.confidence,
        "log_level": args.log_level
    }
    
    if args.config:
        import json
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            config.update(file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return 1
    
    try:
        # パイプライン初期化
        pipeline = ChirashiPipeline(config=config)
        
        if args.batch or os.path.isdir(args.input or ''):
            # バッチ処理
            if not args.input:
                parser.error("Input directory is required for batch processing")
            
            results = pipeline.process_batch(
                input_dir=args.input,
                output_dir=args.output_dir,
                output_format=args.format
            )
            
            print(f"Batch processing completed. Processed {len(results)} files.")
            print(f"Results saved to: {args.output_dir}")
            
        else:
            # 単一画像処理
            if not args.input:
                parser.error("Input image file is required")
            
            if not args.output:
                # 出力ファイル名を自動生成
                base_name = Path(args.input).stem
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                args.output = f"chirashi_result_{base_name}_{timestamp}.{args.format}"
            
            result = pipeline.process_single_image(
                image_path=args.input,
                output_path=args.output,
                output_format=args.format
            )
            
            print(f"Processing completed. Extracted {len(result)} products.")
            print(f"Result saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())