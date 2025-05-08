# ローカル開発環境セットアップガイド

## 前提条件

- Python 3.8以上
- PostgreSQL 12以上（ローカルにインストール）
- pip（Pythonパッケージマネージャー）

## セットアップ手順

1. local_testブランチをクローン
```bash
git clone <repository-url>
cd fit2go_dashboard
git checkout local_test
```

2. PostgreSQLの準備
- PostgreSQLをインストール（まだの場合）
- データベースの作成
```bash
psql -U postgres
CREATE DATABASE fit2go_dashboard;
```

3. 仮想環境の作成と有効化
```bash
python -m venv venv
# Windowsの場合
venv\Scripts\activate
# Linux/macOSの場合
source venv/bin/activate
```

4. 依存関係のインストール
```bash
pip install -r requirements.txt
```

5. 環境変数の設定
```bash
cp .env.example .env
```
`.env`ファイルを以下のように編集：
```env
FLASK_ENV=development
DATABASE_URL=postgresql://localhost/fit2go_dashboard
SECRET_KEY=your-secret-key-for-development
```

6. データベースの初期化
```bash
flask db upgrade
```

7. 開発サーバーの起動
```bash
flask run --host=0.0.0.0 --port=5000
```

## テストデータの投入

M5Stackからのデータ送信をシミュレートするためのテストデータを投入できます：

```bash
python tests/insert_test_data.py
```

## 開発時の注意点

1. デバッグモード
- 開発サーバーは自動的にデバッグモードで起動します
- エラーの詳細がブラウザに表示されます
- コードの変更は自動的に反映されます

2. ログの確認
- アプリケーションのログは`logs/development.log`に出力されます
- デバッグ情報も含めて詳細なログが確認できます

3. データベースの操作
- pgAdminやDBeaver等のGUIツールを使用してデータベースを直接確認・操作できます
- 接続情報：
  - ホスト: localhost
  - データベース: fit2go_dashboard
  - ポート: 5432（デフォルト）

## トラブルシューティング

1. データベース接続エラー
- PostgreSQLサービスが起動しているか確認
- DATABASE_URLの設定が正しいか確認

2. 依存関係のエラー
- 仮想環境が有効化されているか確認
- `pip install -r requirements.txt`を再実行

3. マイグレーションエラー
```bash
flask db stamp head
flask db migrate
flask db upgrade
```

## テスト実行

単体テストとE2Eテストを実行：

```bash
pytest
```

特定のテストのみ実行：

```bash
pytest tests/test_api.py
```