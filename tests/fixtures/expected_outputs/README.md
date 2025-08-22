# テスト用期待結果データ

このディレクトリには、テスト用の期待結果とモックレスポンスデータが配置されています。

## ファイル構成

### OCR APIレスポンス
- `ocr_response_sample_01.json` - 食品系チラシのOCRレスポンス
- `ocr_response_sample_02.json` - 日用品系チラシのOCRレスポンス

### 期待される抽出結果
- `extraction_result_01.json` - サンプル01の期待抽出結果
- `extraction_result_02.json` - サンプル02の期待抽出結果

### LLM APIレスポンス
- `llm_response_sample.json` - OpenAI/Anthropic APIレスポンス例

### エラーケース
- `error_responses.json` - 各種APIエラーレスポンス

## データフォーマット仕様

### 抽出結果JSON
```json
[
  {
    "product": "商品名",
    "price_incl_tax": 税込価格(整数),
    "price_excl_tax": 税抜価格(整数|null),
    "unit": "単位",
    "category": "カテゴリ",
    "confidence": 信頼度(0.0-1.0)
  }
]
```

### OCRレスポンス
Google Cloud Vision API形式のレスポンス構造：
- `text_annotations[]` - テキストアノテーション配列
- `bounding_poly` - バウンディングボックス座標
- `full_text_annotation` - 全体テキスト

## 使用方法
これらのファイルは、pytestでのモックテストやユニットテストで使用されます。
- テスト実行時に期待結果との比較に使用
- APIモックのレスポンスデータとして使用
- エラーハンドリングのテストケースとして使用

## 注意事項
- 実際のAPIレスポンス形式に合わせて定期的に更新してください
- テスト環境でのみ使用し、本番環境では使用しないでください
- 機密情報は含めず、ダミーデータのみ使用してください