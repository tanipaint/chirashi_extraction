"""
OCR処理モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T030のテストが失敗することを確認後、T031で実装します。
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
import time
from google.cloud import vision
from google.api_core import exceptions as gcp_exceptions


class OCRProcessor:
    """OCR処理クラス（スタブ実装）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        OCRProcessorの初期化
        
        Args:
            config: 処理設定（オプション）
        """
        self.config = config or {}
    
    def extract_text(self, image_data: np.ndarray) -> Dict[str, Any]:
        """
        画像からテキストを抽出
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            抽出結果辞書（text, annotations, confidence等）
            
        Raises:
            ValueError: 画像データが不正
            Exception: API呼び出し失敗
        """
        try:
            # モックモードのチェック
            if self.config.get('use_mock', False):
                return self._extract_text_mock(image_data)
            
            # 画像データの検証
            if image_data.size == 0:
                raise ValueError("空の画像データです")
            
            # Google Cloud Vision API クライアントを初期化
            client = vision.ImageAnnotatorClient()
            
            # 画像データをバイト形式に変換
            image_bytes = self._convert_to_bytes(image_data)
            
            # Vision API 用の Image オブジェクトを作成
            image = vision.Image(content=image_bytes)
            
            # テキスト検出を実行
            response = client.text_detection(image=image)
            
            # エラーチェック
            if response.error.message:
                raise Exception(f'API Error: {response.error.message}')
            
            # 結果を整理
            result = {
                'full_text': '',
                'text_annotations': [],
                'confidence_scores': [],
                'bounding_boxes': []
            }
            
            if response.text_annotations:
                # 全体テキスト（最初のアノテーション）
                result['full_text'] = response.text_annotations[0].description
                
                # 各テキストアノテーションを処理
                for annotation in response.text_annotations[1:]:  # 最初は全体テキストなのでスキップ
                    vertices = annotation.bounding_poly.vertices
                    
                    # バウンディングボックスを算出
                    xs = [v.x for v in vertices]
                    ys = [v.y for v in vertices]
                    bbox = (min(xs), min(ys), max(xs), max(ys))
                    
                    result['text_annotations'].append({
                        'text': annotation.description,
                        'bounding_box': bbox,
                        'vertices': [(v.x, v.y) for v in vertices]
                    })
                    
                    result['bounding_boxes'].append(bbox)
                    
                    # 信頼度スコア（簡易算出）
                    confidence = self._calculate_confidence(annotation)
                    result['confidence_scores'].append(confidence)
            
            return result
            
        except gcp_exceptions.GoogleAPICallError as e:
            logging.error(f'Google Cloud Vision API error: {e}')
            raise Exception(f'OCR API呼び出しエラー: {e}')
        except Exception as e:
            logging.error(f'OCR processing error: {e}')
            raise
    
    def get_text_annotations(self, image_data: np.ndarray) -> List[Dict[str, Any]]:
        """
        テキストアノテーション（位置情報含む）を取得
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            アノテーション情報のリスト
            
        Raises:
            ValueError: 画像データが不正
            Exception: API呼び出し失敗
        """
        try:
            result = self.extract_text(image_data)
            return result['text_annotations']
        except Exception as e:
            logging.error(f'Text annotations extraction error: {e}')
            raise
    
    def get_bounding_boxes(self, image_data: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        バウンディングボックス座標を取得
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            バウンディングボックス座標のリスト [(x1, y1, x2, y2), ...]
            
        Raises:
            ValueError: 画像データが不正
            Exception: API呼び出し失敗
        """
        try:
            result = self.extract_text(image_data)
            return result['bounding_boxes']
        except Exception as e:
            logging.error(f'Bounding boxes extraction error: {e}')
            raise
    
    def get_confidence_scores(self, image_data: np.ndarray) -> List[float]:
        """
        信頼度スコアを取得
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            信頼度スコアのリスト
            
        Raises:
            ValueError: 画像データが不正
            Exception: API呼び出し失敗
        """
        try:
            result = self.extract_text(image_data)
            return result['confidence_scores']
        except Exception as e:
            logging.error(f'Confidence scores extraction error: {e}')
            raise
    
    def process_with_retry(self, image_data: np.ndarray, max_retries: int = 3) -> Dict[str, Any]:
        """
        リトライ機能付きOCR処理
        
        Args:
            image_data: 処理する画像データ（numpy array）
            max_retries: 最大リトライ回数
            
        Returns:
            抽出結果辞書
            
        Raises:
            ValueError: 画像データが不正
            Exception: 最大リトライ回数を超過したAPI失敗
        """
        retry_count = 0
        last_error = None
        
        # 設定からリトライ回数を取得（デフォルトを上書き）
        max_retries = self.config.get('max_retries', max_retries)
        retry_delay = self.config.get('retry_delay', 1.0)  # リトライ間隔（秒）
        
        while retry_count <= max_retries:
            try:
                logging.info(f'OCR processing attempt {retry_count + 1}/{max_retries + 1}')
                result = self.extract_text(image_data)
                
                # 成功した場合は結果を返す
                if result['text_annotations'] or result['full_text']:
                    logging.info('OCR processing succeeded')
                    return result
                else:
                    logging.warning('OCR returned empty result, retrying...')
                    
            except gcp_exceptions.ResourceExhausted as e:
                # レート制限エラーの場合は長めに待機
                logging.warning(f'Rate limit exceeded, waiting longer: {e}')
                time.sleep(retry_delay * 5)  # 通常の5倍待機
                last_error = e
                
            except (gcp_exceptions.GoogleAPICallError, Exception) as e:
                logging.warning(f'OCR attempt {retry_count + 1} failed: {e}')
                last_error = e
                
                # 最後のリトライでなければ待機
                if retry_count < max_retries:
                    time.sleep(retry_delay)
            
            retry_count += 1
        
        # 全てのリトライが失敗した場合
        logging.error(f'OCR processing failed after {max_retries + 1} attempts')
        raise Exception(f'OCR処理が最大リトライ回数({max_retries + 1}回)を超過しました: {last_error}')
    
    # ヘルパーメソッド
    def _convert_to_bytes(self, image_data: np.ndarray) -> bytes:
        """画像データをバイト形式に変換"""
        try:
            # OpenCVを使用してJPEG形式にエンコード
            success, buffer = cv2.imencode('.jpg', image_data)
            if not success:
                raise ValueError('画像のエンコードに失敗しました')
            return buffer.tobytes()
        except Exception as e:
            logging.error(f'Image encoding error: {e}')
            raise ValueError(f'画像変換エラー: {e}')
    
    def _calculate_confidence(self, annotation) -> float:
        """信頼度スコアを算出（簡易版）"""
        try:
            # Google Cloud Vision APIは直接的な信頼度スコアを提供しないため、
            # テキストの特徴に基づいて簡易的に算出
            text = annotation.description
            vertices = annotation.bounding_poly.vertices
            
            # 基本信頼度（0.7から始まる）
            confidence = 0.7
            
            # テキストの長さによる補正
            if len(text) >= 3:
                confidence += 0.1
            if len(text) >= 6:
                confidence += 0.05
            
            # バウンディングボックスの安定性チェック
            if len(vertices) == 4:
                confidence += 0.05
            
            # 英数字が含まれている場合
            if any(c.isalnum() for c in text):
                confidence += 0.05
            
            # 上限を1.0に設定
            return min(confidence, 1.0)
            
        except Exception:
            return 0.5  # デフォルト値
    
    def _extract_text_mock(self, image_data: np.ndarray) -> Dict[str, Any]:
        """モックモード用のテキスト抽出"""
        # 画像データのバリデーション（実際の処理と同じ）
        if image_data.size == 0:
            raise ValueError("空の画像データです")
        
        # モックデータを返す
        return {
            'full_text': 'Mock Text Sample モックテキスト',
            'text_annotations': [
                {
                    'text': 'Mock',
                    'bounding_box': (10, 10, 50, 30),
                    'vertices': [(10, 10), (50, 10), (50, 30), (10, 30)]
                },
                {
                    'text': 'Text',
                    'bounding_box': (60, 10, 100, 30),
                    'vertices': [(60, 10), (100, 10), (100, 30), (60, 30)]
                }
            ],
            'confidence_scores': [0.95, 0.90],
            'bounding_boxes': [(10, 10, 50, 30), (60, 10, 100, 30)]
        }