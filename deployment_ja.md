# Fit2Go Dashboard デプロイメントガイド

## 必要要件

- Python 3.8以上
- pip
- PostgreSQL 12以上
- Node.js 14以上 (フロントエンドビルド用)
- Redis (セッション管理用、推奨)

## インストール手順

1. リポジトリのクローン
```bash
git clone https://github.com/your-repo/fit2go_dashboard.git
cd fit2go_dashboard
```

2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows
```

3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

4. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

5. データベースの初期化
```bash
flask db upgrade
```

## Google Fit API設定

1. Google Cloud Consoleで新しいプロジェクトを作成
2. OAuth 2.0クライアントIDを作成
3. 以下のスコープを有効化:
   - fitness.activity.read
   - fitness.body.read
   - fitness.heart_rate.read
   - fitness.location.read
   - fitness.sleep.read

4. 認証情報の設定:
   - client_id
   - client_secret
   を.envファイルに設定

## Health Connect設定

1. Google Play Consoleでアプリを登録
2. 以下の権限を追加:
   - android.permission.health.READ_STEPS
   - android.permission.health.WRITE_STEPS
   - android.permission.health.READ_EXERCISE
   - android.permission.health.WRITE_EXERCISE
   - android.permission.health.READ_HEART_RATE
   - android.permission.health.WRITE_HEART_RATE

## 本番環境でのデプロイ

### Renderへのデプロイ

1. Renderアカウントの作成とセットアップ
- Renderのアカウントを作成し、ログイン
- 「New +」から「Web Service」を選択

2. サービスの設定
- GitリポジトリをRenderに接続
- 以下の設定を行う：
  * Name: fit2go-dashboard（任意）
  * Runtime: Python
  * Build Command: `pip install -r requirements.txt`
  * Start Command: `gunicorn wsgi:app`

3. 環境変数の設定
Renderのダッシュボードで以下の環境変数を設定：
```
DATABASE_URL=postgres://...（RenderのPostgreSQLサービスのURL）
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

4. データベースの設定
- RenderでPostgreSQLデータベースを作成
- 自動的に`DATABASE_URL`環境変数が設定される

### M5Stackの設定

1. M5Stackの設定ファイルを編集
- データ送信先URLをRenderのアプリケーションURLに変更
- 必要に応じてHTTPS証明書の設定を行う

### バックアップ設定（オプション）

RenderのPostgreSQLは自動的にバックアップを提供しますが、追加のバックアップが必要な場合：

1. Render上でcron jobを設定
```bash
# 毎日のバックアップを実行
pg_dump $DATABASE_URL | gzip > /backup/fit2go_$(date +%Y%m%d).sql.gz
```

## 注意事項

- Renderの無料プランではスリープモードがあるため、初回アクセス時に起動に時間がかかる場合があります
- 継続的な運用には有料プランの使用を推奨
- HTTPSは自動的に有効化されます
- アプリケーションの監視はRenderのダッシュボードで確認可能