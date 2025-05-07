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

## 本番環境での実行

### 通常の起動
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Systemdを使用した自動起動の設定
1. サービスファイルの作成
```bash
sudo nano /etc/systemd/system/fit2go.service
```

2. 以下の内容を追加:
```ini
[Unit]
Description=Fit2Go Dashboard
After=network.target

[Service]
User=fit2go
Group=fit2go
WorkingDirectory=/path/to/fit2go_dashboard
Environment="PATH=/path/to/fit2go_dashboard/venv/bin"
ExecStart=/path/to/fit2go_dashboard/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. サービスの有効化と起動
```bash
sudo systemctl enable fit2go
sudo systemctl start fit2go
```

## データベースのバックアップ

1. 自動バックアップの設定
```bash
# /etc/cron.daily/fit2go-backup
pg_dump fit2go_dashboard | gzip > /backup/fit2go_$(date +%Y%m%d).sql.gz
```

## 注意事項

- 本番環境では必ずHTTPSを有効にしてください
- セッションの永続化にはRedisの使用を推奨します
  ```bash
  pip install redis
  ```
- ログローテーションの設定を忘れずに行ってください
  ```bash
  sudo nano /etc/logrotate.d/fit2go
  ```
  ```
  /var/log/fit2go/*.log {
      daily
      rotate 14
      compress
      delaycompress
      missingok
      notifempty
      create 0640 fit2go fit2go
  }
  ```
- 定期的なデータベースバックアップを設定してください
- アプリケーションの監視とメトリクス収集を設定することを推奨します