"""
画像前処理モジュール

TDD方式での実装のため、まず最小限のスタブを定義。
T020のテストが失敗することを確認後、T021で実装します。
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional, Union
import os
import logging


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
        全ての前処理をパイプライン形式で実行
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            処理済み画像（numpy array）
            
        Raises:
            FileNotFoundError: 画像ファイルが存在しない
            ValueError: 画像ファイルが不正
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            logging.info(f"Starting image preprocessing for: {image_path}")
            
            # ステップ1: 傾き補正
            corrected_image = self._process_with_array(self.correct_rotation(image_path))
            
            # ステップ2: ノイズ除去（カラー画像で実行）
            denoised_image = self._apply_noise_removal(corrected_image)
            
            # ステップ3: コントラスト調整（カラー画像で実行）
            contrast_adjusted = self._apply_contrast_adjustment(denoised_image)
            
            # ステップ4: グレースケール変換（最終段階）
            final_image = self._apply_grayscale_conversion(contrast_adjusted)
            
            logging.info(f"Image preprocessing completed for: {image_path}")
            return final_image
            
        except Exception as e:
            logging.error(f"Error in image preprocessing: {e}")
            raise ValueError(f"Failed to process image: {e}")
    
    def _process_with_array(self, image_array: np.ndarray) -> np.ndarray:
        """配列として渡された画像をそのまま返す（内部処理用）"""
        return image_array
    
    def _apply_noise_removal(self, image_array: np.ndarray) -> np.ndarray:
        """画像配列に対してノイズ除去を適用"""
        filter_size = self.config.get('noise_filter_size', 5)
        denoised = cv2.medianBlur(image_array, filter_size)
        denoised = cv2.GaussianBlur(denoised, (3, 3), 0)
        return denoised
    
    def _apply_contrast_adjustment(self, image_array: np.ndarray) -> np.ndarray:
        """画像配列に対してコントラスト調整を適用"""
        contrast_method = self.config.get('contrast_method', 'clahe')
        
        if contrast_method == 'clahe':
            if len(image_array.shape) == 3:
                lab = cv2.cvtColor(image_array, cv2.COLOR_BGR2LAB)
                l_channel = lab[:, :, 0]
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l_channel = clahe.apply(l_channel)
                lab[:, :, 0] = l_channel
                enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(image_array)
        elif contrast_method == 'histogram':
            if len(image_array.shape) == 3:
                enhanced = cv2.cvtColor(image_array, cv2.COLOR_BGR2YUV)
                enhanced[:, :, 0] = cv2.equalizeHist(enhanced[:, :, 0])
                enhanced = cv2.cvtColor(enhanced, cv2.COLOR_YUV2BGR)
            else:
                enhanced = cv2.equalizeHist(image_array)
        else:
            alpha = self.config.get('contrast_alpha', 1.2)
            beta = self.config.get('contrast_beta', 10)
            enhanced = cv2.convertScaleAbs(image_array, alpha=alpha, beta=beta)
        
        return enhanced
    
    def _apply_grayscale_conversion(self, image_array: np.ndarray) -> np.ndarray:
        """画像配列に対してグレースケール変換を適用"""
        if len(image_array.shape) == 2:
            return image_array
        elif len(image_array.shape) == 3 and image_array.shape[2] == 1:
            return image_array.squeeze()
        
        return cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    
    def correct_rotation(self, image_path: str) -> np.ndarray:
        """
        傾き補正処理（±5度以内の自動補正）
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            補正済み画像（numpy array）
            
        Raises:
            FileNotFoundError: 画像ファイルが存在しない
            ValueError: 画像ファイルが不正
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot read image file: {image_path}")
            
            # グレースケール変換（角度検出のため）
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # エッジ検出
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 直線検出（Hough変換）
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None and len(lines) > 0:
                # 角度の計算
                angles = []
                for line in lines[:10]:  # 上位10本の直線を使用
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi - 90
                    if abs(angle) <= 5:  # ±5度以内のみ考慮
                        angles.append(angle)
                
                if angles:
                    # 角度の中央値を使用
                    rotation_angle = np.median(angles)
                    
                    # 画像の中心で回転
                    height, width = image.shape[:2]
                    center = (width // 2, height // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
                    
                    # 回転実行
                    corrected = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                             flags=cv2.INTER_CUBIC, 
                                             borderMode=cv2.BORDER_REPLICATE)
                    return corrected
            
            # 補正不要または検出失敗の場合は元画像を返す
            return image
            
        except Exception as e:
            logging.error(f"Error in rotation correction: {e}")
            raise ValueError(f"Failed to correct rotation: {e}")
    
    def convert_to_grayscale(self, image_path: str) -> np.ndarray:
        """
        グレースケール変換処理
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            グレースケール画像（numpy array）
            
        Raises:
            FileNotFoundError: 画像ファイルが存在しない
            ValueError: 画像ファイルが不正
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot read image file: {image_path}")
            
            # 既にグレースケールかチェック
            if len(image.shape) == 2:
                return image
            elif len(image.shape) == 3 and image.shape[2] == 1:
                return image.squeeze()
            
            # カラー画像からグレースケールに変換
            grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return grayscale
            
        except Exception as e:
            logging.error(f"Error in grayscale conversion: {e}")
            raise ValueError(f"Failed to convert to grayscale: {e}")
    
    def remove_noise(self, image_path: str) -> np.ndarray:
        """
        ノイズ除去処理（メディアンフィルタ適用）
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            ノイズ除去済み画像（numpy array）
            
        Raises:
            FileNotFoundError: 画像ファイルが存在しない
            ValueError: 画像ファイルが不正
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot read image file: {image_path}")
            
            # 設定からフィルタサイズを取得（デフォルト: 5）
            filter_size = self.config.get('noise_filter_size', 5)
            
            # メディアンフィルタでノイズ除去
            denoised = cv2.medianBlur(image, filter_size)
            
            # 追加のガウシアンフィルタ（軽微な平滑化）
            denoised = cv2.GaussianBlur(denoised, (3, 3), 0)
            
            return denoised
            
        except Exception as e:
            logging.error(f"Error in noise removal: {e}")
            raise ValueError(f"Failed to remove noise: {e}")
    
    def adjust_contrast(self, image_path: str) -> np.ndarray:
        """
        コントラスト調整処理
        
        Args:
            image_path: 処理する画像ファイルのパス
            
        Returns:
            コントラスト調整済み画像（numpy array）
            
        Raises:
            FileNotFoundError: 画像ファイルが存在しない
            ValueError: 画像ファイルが不正
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot read image file: {image_path}")
            
            # 設定からコントラスト調整方法を取得
            contrast_method = self.config.get('contrast_method', 'clahe')
            
            if contrast_method == 'clahe':
                # CLAHE (Contrast Limited Adaptive Histogram Equalization)
                # グレースケール変換
                if len(image.shape) == 3:
                    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                    l_channel = lab[:, :, 0]
                    
                    # CLAHEを適用
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    l_channel = clahe.apply(l_channel)
                    
                    # LAB色空間で結合して元の色空間に戻す
                    lab[:, :, 0] = l_channel
                    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                else:
                    # グレースケール画像の場合
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    enhanced = clahe.apply(image)
            
            elif contrast_method == 'histogram':
                # ヒストグラム均等化
                if len(image.shape) == 3:
                    # カラー画像の場合、各チャンネルに適用
                    enhanced = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
                    enhanced[:, :, 0] = cv2.equalizeHist(enhanced[:, :, 0])
                    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_YUV2BGR)
                else:
                    # グレースケール画像の場合
                    enhanced = cv2.equalizeHist(image)
            
            else:
                # 線形コントラスト調整
                alpha = self.config.get('contrast_alpha', 1.2)  # コントラスト係数
                beta = self.config.get('contrast_beta', 10)     # 明度調整
                enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            
            return enhanced
            
        except Exception as e:
            logging.error(f"Error in contrast adjustment: {e}")
            raise ValueError(f"Failed to adjust contrast: {e}")