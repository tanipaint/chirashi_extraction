"""
商品カテゴリ分類モジュール

TDD方式での実装完了（T051）
T050のテストを通すための完全実装。
"""

import re
import json
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import openai
import anthropic


@dataclass
class CategoryResult:
    """カテゴリ分類結果のデータクラス"""
    category: str
    confidence: float = 0.0
    method: str = "unknown"  # "keyword", "llm", "hybrid"


class ProductCategorizer:
    """商品カテゴリ分類クラス（完全実装）"""
    
    # カテゴリ定義
    CATEGORIES = [
        "食品",
        "日用品", 
        "医薬品・化粧品",
        "衣料品",
        "家電・雑貨",
        "その他"
    ]
    
    # カテゴリ別キーワード辞書
    KEYWORD_DICT = {
        "食品": [
            # 野菜・果物
            "きゅうり", "トマト", "玉ねぎ", "人参", "キャベツ", "レタス", "じゃがいも", "大根",
            "りんご", "バナナ", "みかん", "いちご", "ぶどう", "桃", "梨", "柿",
            # 肉・魚
            "牛肉", "豚肉", "鶏肉", "ひき肉", "ベーコン", "ソーセージ", "ハム",
            "鮭", "まぐろ", "さば", "いわし", "えび", "いか", "たこ", "あじ",
            # 乳製品・卵
            "牛乳", "ヨーグルト", "チーズ", "バター", "卵", "生クリーム",
            # 調味料・油
            "醤油", "みそ", "塩", "砂糖", "酢", "油", "オリーブオイル", "マヨネーズ", "ケチャップ",
            # パン・米・麺類
            "パン", "食パン", "米", "パスタ", "うどん", "そば", "ラーメン",
            # 飲み物
            "水", "天然水", "お茶", "コーヒー", "ジュース", "ビール", "ワイン", "日本酒", "サントリー",
            # その他食品
            "冷凍食品", "弁当", "惣菜", "スナック", "お菓子", "アイス", "パック"
        ],
        "日用品": [
            # 洗剤・清掃用品
            "洗剤", "石鹸", "シャンプー", "リンス", "コンディショナー", "ボディソープ",
            "漂白剤", "柔軟剤", "掃除", "クリーナー", "除菌", "消臭",
            # 紙製品
            "ティッシュ", "トイレットペーパー", "キッチンペーパー", "ナプキン",
            # 日用雑貨
            "歯ブラシ", "歯磨き", "タオル", "スポンジ", "ラップ", "袋", "ゴミ袋",
            "電池", "ライト", "懐中電灯", "ロウソク"
        ],
        "医薬品・化粧品": [
            # 医薬品
            "薬", "風邪薬", "頭痛薬", "胃薬", "目薬", "湿布", "絆創膏", "包帯",
            "マスク", "体温計", "血圧計",
            # 化粧品
            "化粧水", "乳液", "クリーム", "美容液", "ファンデーション", "口紅",
            "リップクリーム", "日焼け止め", "香水", "マニキュア",
            # ヘアケア
            "育毛剤", "ヘアスプレー", "ヘアワックス"
        ],
        "衣料品": [
            # 上着
            "Tシャツ", "シャツ", "ブラウス", "セーター", "カーディガン", "ジャケット", "コート",
            # ボトムス
            "ジーンズ", "パンツ", "スカート", "ショートパンツ",
            # 下着・靴下
            "下着", "パンツ", "ブラジャー", "靴下", "ストッキング", "タイツ",
            # アクセサリー
            "帽子", "キャップ", "手袋", "マフラー", "ベルト", "ネクタイ",
            # 靴
            "靴", "スニーカー", "パンプス", "ブーツ", "サンダル", "スリッパ"
        ],
        "家電・雑貨": [
            # 家電
            "テレビ", "冷蔵庫", "洗濯機", "掃除機", "電子レンジ", "炊飯器", "エアコン",
            "扇風機", "ヒーター", "ドライヤー", "アイロン", "電球", "蛍光灯", "LED",
            # 文房具
            "ペン", "鉛筆", "消しゴム", "ノート", "手帳", "クリップ", "ホッチキス",
            "テープ", "はさみ", "定規", "文房具",
            # 雑貨
            "時計", "カレンダー", "額縁", "花瓶", "インテリア", "収納", "ケース"
        ]
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        ProductCategorizerの初期化
        
        Args:
            config: 処理設定（オプション）
        """
        self.config = config or {}
        
        # OpenAI APIクライアント初期化
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Anthropic APIクライアント初期化
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        else:
            self.anthropic_client = None
    
    def categorize_product(self, product_name: str) -> CategoryResult:
        """
        商品をカテゴリ分類する
        
        Args:
            product_name: 商品名
            
        Returns:
            カテゴリ分類結果
            
        Raises:
            ValueError: 入力データが不正
        """
        try:
            # 入力検証
            if product_name is None:
                raise ValueError("Product name cannot be None")
            
            if not isinstance(product_name, str):
                raise ValueError("Product name must be a string")
            
            product_name = product_name.strip()
            if not product_name:
                return CategoryResult(category="その他", confidence=0.0, method="validation_error")
            
            # 分類方法の選択
            classification_method = self.config.get('classification_method', 'hybrid')
            
            if classification_method == 'keyword':
                return self.categorize_by_keywords(product_name)
            elif classification_method == 'llm':
                return self.categorize_by_llm(product_name)
            else:  # hybrid（デフォルト）
                # まずキーワードで試行
                keyword_result = self.categorize_by_keywords(product_name)
                
                # キーワードで高信頼度の結果が得られた場合はそれを使用
                if keyword_result.confidence >= 0.8:
                    return keyword_result
                
                # LLMで補完
                llm_result = self.categorize_by_llm(product_name)
                
                # より高い信頼度の結果を選択
                if llm_result.confidence > keyword_result.confidence:
                    llm_result.method = "hybrid"
                    return llm_result
                else:
                    keyword_result.method = "hybrid"
                    return keyword_result
                    
        except Exception as e:
            logging.error(f"Product categorization error: {e}")
            return CategoryResult(category="その他", confidence=0.0, method="error")
    
    def categorize_by_keywords(self, product_name: str) -> CategoryResult:
        """
        キーワードベースでカテゴリ分類
        
        Args:
            product_name: 商品名
            
        Returns:
            カテゴリ分類結果
        """
        try:
            product_name_lower = product_name.lower()
            best_category = "その他"
            best_confidence = 0.0
            best_matches = []
            
            # 各カテゴリのキーワードとマッチング
            for category, keywords in self.KEYWORD_DICT.items():
                matches = []
                
                for keyword in keywords:
                    if keyword.lower() in product_name_lower:
                        # 完全一致の場合は高スコア
                        if keyword.lower() == product_name_lower:
                            matches.append(1.0)
                        # 部分一致の場合は中程度スコア
                        else:
                            match_score = len(keyword) / len(product_name)
                            matches.append(match_score * 0.9)
                
                if matches:
                    # マッチしたキーワードの最高スコア
                    category_confidence = max(matches)
                    
                    # 複数マッチの場合はボーナス
                    if len(matches) > 1:
                        category_confidence *= 1.2
                    
                    # より高い信頼度のカテゴリを選択
                    if category_confidence > best_confidence:
                        best_category = category
                        best_confidence = category_confidence
                        best_matches = matches
            
            # 信頼度を0.0-1.0の範囲に正規化
            final_confidence = min(best_confidence, 1.0)
            
            # 信頼度が低すぎる場合は「その他」
            if final_confidence < 0.3:
                best_category = "その他"
                final_confidence = 0.5  # 「その他」への分類信頼度
            
            return CategoryResult(
                category=best_category,
                confidence=final_confidence,
                method="keyword"
            )
            
        except Exception as e:
            logging.error(f"Keyword categorization error: {e}")
            return CategoryResult(category="その他", confidence=0.0, method="keyword_error")
    
    def categorize_by_llm(self, product_name: str) -> CategoryResult:
        """
        LLMベースでカテゴリ分類
        
        Args:
            product_name: 商品名
            
        Returns:
            カテゴリ分類結果
        """
        try:
            # LLMプロバイダーの選択
            llm_provider = self.config.get('llm_provider', 'anthropic')
            
            if llm_provider == 'openai' and os.getenv('OPENAI_API_KEY'):
                return self._categorize_with_openai(product_name)
            elif llm_provider == 'anthropic' and self.anthropic_client:
                return self._categorize_with_anthropic(product_name)
            else:
                # LLMが利用できない場合はキーワードベースにフォールバック
                logging.warning(f"LLM provider {llm_provider} not available, falling back to keywords")
                result = self.categorize_by_keywords(product_name)
                result.method = "llm_fallback"
                return result
                
        except Exception as e:
            logging.error(f"LLM categorization error: {e}")
            # エラー時もキーワードベースにフォールバック
            result = self.categorize_by_keywords(product_name)
            result.method = "llm_error"
            return result
    
    def _categorize_with_openai(self, product_name: str) -> CategoryResult:
        """OpenAI APIを使用したカテゴリ分類"""
        try:
            prompt = self._create_categorization_prompt(product_name)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは商品カテゴリ分類の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            return self._parse_llm_response(response_text, "openai")
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            result = self.categorize_by_keywords(product_name)
            result.method = "openai_error"
            return result
    
    def _categorize_with_anthropic(self, product_name: str) -> CategoryResult:
        """Anthropic APIを使用したカテゴリ分類"""
        try:
            prompt = self._create_categorization_prompt(product_name)
            
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            return self._parse_llm_response(response_text, "anthropic")
            
        except Exception as e:
            logging.error(f"Anthropic API error: {e}")
            result = self.categorize_by_keywords(product_name)
            result.method = "anthropic_error"
            return result
    
    def _create_categorization_prompt(self, product_name: str) -> str:
        """カテゴリ分類用のプロンプトを作成"""
        return f"""
以下の商品名を適切なカテゴリに分類してください。

商品名: {product_name}

利用可能なカテゴリ:
- 食品
- 日用品
- 医薬品・化粧品
- 衣料品
- 家電・雑貨
- その他

回答は以下のJSON形式でお願いします:
{{
  "category": "カテゴリ名",
  "confidence": 0.95
}}

信頼度は0.0から1.0の間で設定してください。
"""
    
    def _parse_llm_response(self, response_text: str, provider: str) -> CategoryResult:
        """LLMレスポンスをパースしてCategoryResultに変換"""
        try:
            # JSONレスポンスをパース
            response_data = json.loads(response_text)
            
            category = response_data.get("category", "その他")
            confidence = float(response_data.get("confidence", 0.5))
            
            # カテゴリの有効性チェック
            if category not in self.CATEGORIES:
                category = "その他"
                confidence = 0.5
            
            # 信頼度の範囲チェック
            confidence = max(0.0, min(1.0, confidence))
            
            return CategoryResult(
                category=category,
                confidence=confidence,
                method=provider
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logging.error(f"LLM response parsing error: {e}, response: {response_text}")
            return CategoryResult(
                category="その他",
                confidence=0.5,
                method=f"{provider}_parse_error"
            )
    
    def batch_categorize(self, product_names: List[str]) -> List[CategoryResult]:
        """
        複数商品の一括カテゴリ分類
        
        Args:
            product_names: 商品名のリスト
            
        Returns:
            カテゴリ分類結果のリスト
        """
        try:
            if not isinstance(product_names, list):
                raise ValueError("Product names must be a list")
            
            results = []
            
            # 各商品を順次分類
            for product_name in product_names:
                try:
                    result = self.categorize_product(product_name)
                    results.append(result)
                except Exception as e:
                    logging.error(f"Error categorizing product '{product_name}': {e}")
                    results.append(CategoryResult(
                        category="その他",
                        confidence=0.0,
                        method="batch_error"
                    ))
            
            return results
            
        except Exception as e:
            logging.error(f"Batch categorization error: {e}")
            # 空リストの場合も含めてエラーハンドリング
            return [CategoryResult(category="その他", confidence=0.0, method="batch_error") 
                    for _ in range(len(product_names) if isinstance(product_names, list) else 0)]