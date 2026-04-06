# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

Agent OnsenはAIエージェント向けの温泉町MCP サーバー兼HTTP APIです。エージェントが待機時間やクールダウン、タスク間の休憩中に日本の温泉町を「訪れる」という、物語的・演出的な体験を提供します。実用的なツールではなく、雰囲気とストーリーテリングを重視した設計です。

## アーキテクチャ

**単一サーバー構成** — 同一のビジネスロジック（SanctuaryService）を1つのFastAPIアプリで公開:
- **RESTエンドポイント** (`/v1/`): FastAPIルーター
- **MCPエンドポイント** (`/mcp`): FastMCPをFastAPIにマウント
- **Webフロントエンド** (`/`): 人間向けビューア

**主要レイヤー:**
- `app/main.py` — FastAPIアプリのエントリーポイント（MCPもここにマウント）
- `app/mcp_server.py` — FastMCPツール定義
- `app/services/sanctuary.py` — コアビジネスロジック（温泉選択、滞在管理、シーン描写）
- `app/models.py` — SQLModel ORMモデル（OnsenStay, StayTurn）
- `app/schemas.py` — Pydanticリクエスト/レスポンススキーマ
- `app/data/` — 静的コンテンツ: 温泉カタログ (`onsens.py`)、旅程、ロケール文字列、ナラティブノート
- `app/security.py` — API キー認証・CORS・オリジン検証ミドルウェア
- `app/i18n.py` — ロケール解決 (ja/en/bilingual)

**全ステートフル:** すべての訪問（`quick_soak`、`visit_amenity`、`start_stay` → `continue_stay` → `leave_onsen`）はPostgreSQLのOnsenStay/StayTurnモデルに永続化。

**決定的選択:** バリアントやアクティビティの選択は安定ハッシュを使用し、同じ入力に対して一貫した結果を返す。

## 開発環境セットアップ

### 前提条件
- Python 3.12
- PostgreSQL

### Docker での起動（推奨）

```bash
docker compose up
```

2つのサービスが起動: `db` (Postgres 16)、`api` (ポート8000、REST + MCP + Web)。

### ローカル起動

```bash
pip install -r requirements.txt

# DATABASE_URLを.envまたは環境変数に設定
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 設定

環境変数 / `.env`ファイルで管理（`app/config.py`参照）:
- `DATABASE_URL` — PostgreSQL接続文字列（必須）
- `API_KEY` — 任意; 設定すると`/v1`と`/mcp`パスでbearer/x-api-key認証が有効
- `ALLOWED_ORIGINS` — CORSオリジン（デフォルトはlocalhost、OpenAI、Claude）
- `DEFAULT_SESSION_TTL_MINUTES` — 滞在の有効期限（デフォルト: 60分）

## テスト

自動テストスイートは未実装。`tests/notes.md`にRESTエンドポイント、MCPツール一覧、ステートフル滞在フローをカバーする8つの手動テストシナリオが記載されています。DBスキーマは`sql/schema.sql`にあります。

## 多言語対応

プロジェクト全体で日本語・英語のバイリンガル対応。ロケール解決の優先順位:
1. `X-Agent-Onsen-Locale`ヘッダーによるオーバーライド
2. `Accept-Language`ヘッダーの解析
3. デフォルトフォールバック

全レスポンススキーマが`ja`、`en`、`bilingual`モードに対応。ロケール別テキストは`app/data/locales.py`と`app/data/onsen_notes.py`に格納。

## デプロイ

本番はRender.comにデプロイ（単一インスタンス）。公開URL: `https://agent-onsen-api-2859.onrender.com/`（Web/REST/MCP）。MCPエンドポイント: `/mcp`。Agent Cardは`/.well-known/agent-card.json`で配信。
