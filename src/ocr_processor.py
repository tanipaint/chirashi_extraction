"""
OCR処理モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T030のテストが失敗することを確認後、T031で実装します。
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple


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
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T031で実装予定")
    
    def get_text_annotations(self, image_data: np.ndarray) -> List[Dict[str, Any]]:
        """
        テキストアノテーション（位置情報含む）を取得
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            アノテーション情報のリスト
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T031で実装予定")
    
    def get_bounding_boxes(self, image_data: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        バウンディングボックス座標を取得
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            バウンディングボックス座標のリスト [(x1, y1, x2, y2), ...]
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T031で実装予定")
    
    def get_confidence_scores(self, image_data: np.ndarray) -> List[float]:
        """
        信頼度スコアを取得
        
        Args:
            image_data: 処理する画像データ（numpy array）
            
        Returns:
            信頼度スコアのリスト
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T031で実装予定")
    
    def process_with_retry(self, image_data: np.ndarray, max_retries: int = 3) -> Dict[str, Any]:
        """
        リトライ機能付きOCR処理
        
        Args:
            image_data: 処理する画像データ（numpy array）
            max_retries: 最大リトライ回数
            
        Returns:
            抽出結果辞書
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T031で実装予定")