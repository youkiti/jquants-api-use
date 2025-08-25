# J-Quants API 株価・バリュエーション指標取得ツール

## 概要
`quants-codes.txt`に記載された銘柄コードから、最新の株価とバリュエーション指標（PER、PBR）を一括取得するPythonスクリプトです。

## 必要な準備

### 1. J-Quants APIのアカウント
[J-Quants](https://jpx-jquants.com/)でアカウントを作成し、APIキーを取得してください。

### 2. 環境設定
`.env.example`を`.env`にコピーして、認証情報を設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下のいずれかの方法で認証情報を設定：

**方法1: リフレッシュトークンを使用（推奨）**
```
JQUANTS_REFRESH_TOKEN=your_refresh_token_here
```

**方法2: メールアドレスとパスワードを使用**
```
JQUANTS_EMAIL=your_email@example.com
JQUANTS_PASSWORD=your_password_here
```

### 3. 依存関係のインストール

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt
```

## 使用方法

```bash
# 仮想環境を有効化
source venv/bin/activate  # Windows: venv\Scripts\activate

# スクリプトの実行
python fetch_stock_metrics.py
```

## 出力

### コンソール出力
以下の形式で表示されます：
- コード: 銘柄コード
- 銘柄名: 企業名
- 最新株価: 直近の終値
- 基準日: 株価の基準日
- PER(最新): 株価収益率（実績または予想）
- PER(予想): 次年度予想PER
- PBR(最新): 株価純資産倍率
- 決算期: 財務データの決算期

### CSVファイル
実行結果は`stock_metrics_YYYYMMDD_HHMMSS.csv`として自動保存されます。

## 注意事項

- APIのレート制限があるため、大量の銘柄を取得する場合は適切な間隔を空けています
- 無料プランでは一部のデータが取得できない場合があります
- 財務データは最新の開示情報に基づいています

## トラブルシューティング

### 認証エラーが発生する場合
- `.env`ファイルの認証情報が正しいか確認
- リフレッシュトークンの有効期限を確認

### データが取得できない場合
- 銘柄コードが正しいか確認
- APIプランの制限を確認（無料プランでは一部データが制限されます）

### パッケージのインストールエラー
- 仮想環境が有効化されているか確認
- Python 3.8以上がインストールされているか確認