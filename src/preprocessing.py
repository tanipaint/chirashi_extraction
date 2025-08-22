"""
画像前処理モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T020のテストが失敗することを確認後、T021で実装します。
"""

import numpy as np
from typing import Dict, Any, Optional


class ImagePreprocessor:
    """画像前処理クラス（スタブ実装）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        ImagePreprocessorの初期化
        
        Args:
            config: 処理設定（オプション）
        """
        self.config = config or {}
    
    def process(self, image_path: str) -> np.ndarray:
        """
        画像前処理のメインエントリーポイント
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            処理済み画像（numpy array）
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T021で実装予定")
    
    def correct_rotation(self, image_path: str) -> np.ndarray:
        """
        傾き補正処理
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            補正済み画像（numpy array）
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T021で実装予定")
    
    def convert_to_grayscale(self, image_path: str) -> np.ndarray:
        """
        グレースケール変換処理
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            グレースケール画像（numpy array）
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T021で実装予定")
    
    def remove_noise(self, image_path: str) -> np.ndarray:
        """
        ノイズ除去処理
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            ノイズ除去済み画像（numpy array）
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T021で実装予定")
    
    def adjust_contrast(self, image_path: str) -> np.ndarray:
        """
        コントラスト調整処理
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            コントラスト調整済み画像（numpy array）
            
        Raises:
            NotImplementedError: まだ実装されていません
        """
        raise NotImplementedError("T021で実装予定")