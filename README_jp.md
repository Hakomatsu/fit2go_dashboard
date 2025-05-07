# Fit2Go Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English version here](README.md)

**注意: このリポジトリのすべてのコードは GitHub Copilot Agent を使用して生成されています。**

Fit2Go DashboardはFlexispot Sit2Go フィットネスチェア用のWebダッシュボードアプリケーションです。M5Stackデバイスから送信されるフィットネスデータをリアルタイムで可視化し、運動記録を管理します。

## 主な機能

### リアルタイムモニタリング
- 現在の速度（km/h）、RPM、METs値をタコメーター形式で表示
- 運動距離、消費カロリー、経過時間のリアルタイム表示
- セッションデータのグラフ表示

### デイリーサマリー
- 15分単位での運動データ集計
- 時間帯別の平均速度、RPM、距離、カロリーを表示
- 日次の累計データ表示

### カレンダー機能
- 月別の運動記録閲覧
- 日付別の詳細データ表示
- セッション別の詳細グラフ表示

### 累積データ管理
- 総運動時間、総距離、総消費カロリーの表示
- 履歴データのエクスポート機能

## 技術スタック

- Backend: Python/Flask
- Database: PostgreSQL
- Frontend: HTML/CSS/JavaScript
- Charts: Plotly.js
- Calendar: FullCalendar
- Hosting: Render

## 開発環境のセットアップ

1. リポジトリのクローン
```bash
git clone <repository-url>
cd fit2go-dashboard
```

2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

4. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して必要な環境変数を設定
```

5. データベースのセットアップ
```bash
flask db upgrade
```

6. 開発サーバーの起動
```bash
flask run
```

## デプロイ

このアプリケーションは[Render](https://render.com)にデプロイするように設定されています。
デプロイの詳細な手順については[デプロイガイド](deployment_ja.md)を参照してください。

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/your-feature`)
3. 変更をコミット (`git commit -am 'feat: add new feature'`)
4. ブランチにプッシュ (`git push origin feature/your-feature`)
5. プルリクエストを作成

## コミットメッセージの規約

このプロジェクトは[Conventional Commits](https://www.conventionalcommits.org/)の規約に従っています。
プルリクエストのタイトルも同様の規約に従う必要があります。

使用可能なタイプ:
- feat: 新機能
- fix: バグ修正
- docs: ドキュメントのみの変更
- style: コードの動作に影響しないスタイルの変更
- refactor: リファクタリング
- perf: パフォーマンス改善
- test: テストの追加・修正
- build: ビルドシステムや外部依存関係の変更
- ci: CI設定の変更
- chore: その他の変更
- revert: コミットの取り消し

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。