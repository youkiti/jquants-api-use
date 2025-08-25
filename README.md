# J-Quants API 株価分析ツール

J-Quants APIを使用して日本株の株価とバリュエーション指標（PER・PBR）を取得するPythonスクリプトです。

## 機能

- 指定した銘柄コードの最新株価を取得
- PER（株価収益率）の算出（実績・予想）
- PBR（株価純資産倍率）の算出
- CSVファイルでの結果出力

## 使用方法

### 1. セットアップ

```bash
# 依存関係のインストール
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 認証情報の設定
cp .env.example .env
# .envファイルにJ-Quants APIの認証情報を記載
```

### 2. 実行

```bash
source venv/bin/activate && python fetch_stock_metrics_with_valuation.py
```

### 3. 結果

- 画面に表形式で表示
- `output/stock_metrics_YYYYMMDD_HHMMSS.csv` に保存

## 対象銘柄

`quants-codes.txt` に記載された17銘柄：
- 1301 (極洋)
- 1952 (新日本空調)
- 3131 (シンデン・ハイテックス)
- 3856 (Ａｂａｌａｎｃｅ)
- 5074 (テスホールディングス)
- 5965 (フジマック)
- 7247 (ミクニ)
- 8053 (住友商事)
- 8058 (三菱商事)
- 8233 (高島屋)
- 9020 (東日本旅客鉄道)
- 9045 (京阪ホールディングス)
- 9201 (日本航空)
- 9434 (ソフトバンク)
- 9647 (協和コンサルタンツ)
- 9791 (ビケンテクノ)
- 9936 (王将フードサービス)

## 必要な認証情報

J-Quants APIアカウントが必要です。[J-Quants公式サイト](https://jpx-jquants.com/)でアカウントを作成し、`.env`ファイルに以下のいずれかを設定：

**方法1: リフレッシュトークン（推奨）**
```
REFRESH_TOKEN=your_refresh_token_here
```

**方法2: メールアドレス・パスワード**
```
JQUANTS_EMAIL=your_email@example.com
JQUANTS_PASSWORD=your_password
```
