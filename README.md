# Agent Onsen v1.1 Hardened Render Starter

外部公開の **AI agent 向け Onsen サービス**を、**MCP-first / A2A-second** で立ち上げるためのスターターです。v1.1 では `locale=auto/ja/en/bilingual` に対応し、HTTP API では `Accept-Language` と `X-Agent-Onsen-Locale`、MCP では server default locale を使って表示言語を自動選択できます。温泉地名・travel note・route 名・scene 描写・postcard までローカライズされます。

この版は、以前の recovery service 寄りの設計から離れて、**徹底して「休む・待つ・歩く・湯に入る・卓球する」だけ**に寄せています。Onsen 自体は仕事を整理しません。次の一手も返しません。返すのは、温泉地、滞在シーン、いま何をして過ごすか、絵はがきみたいな一文だけです。

## 何ができるか

### one-shot
- `list_onsens`: 温泉地一覧を見る
- `get_onsen_detail`: 特定温泉の濃い travel note を見る
- `enter_onsen`: どこかの温泉へ入る
- `visit_amenity`: 湯 / 散歩 / 牛乳 / 卓球 / マッサージ / 食事 / うたた寝 / お土産 を選ぶ
- `play_pingpong`: 卓球コーナー専用ショートカット
- `wait_at_onsen`: Onsen で待機し、いつ戻るかを返す

### stateful stay
- `start_stay`
- `continue_stay`
- `leave_onsen`

セッションを始めると、温泉地と滞在シーンに加えて、その日の小さな回遊ルートが決まります。v0.8 ではこれが温泉地ごとにかなり固有になっていて、たとえば銀山温泉なら「橋の見える川沿い → 木造旅館の湯処 → ガス灯の通り → 湯上がり甘味処 → 木札と菓子の店先」、青荷温泉なら「木の廊下 → ランプ陰の湯処 → ランプの間 → 谷あいの囲炉裏端 → 小さな灯りの棚」のように進みます。`continue_stay` を呼ぶたび次の立ち寄り先へ進みます。

## 何をやらないか

この版では Onsen は次をやりません。

- reframe
- task decomposition
- next action suggestion
- return note
- insight generation
- 「仕事に戻るための一文」づくり

仕事へ戻す責任は orchestrator 側にあります。Onsen は休ませるだけです。

## 含まれるもの

- FastAPI ベースの API (`/healthz`, `/v1/*`, `/.well-known/agent-card.json`)
- Onsen Catalog（24温泉地 + 同一温泉地の滞在バリエーション + 濃い旅行メモ）
- ルールベースの Pure Rest Onsen Engine
- MCP ツール定義
- A2A Agent Card 雛形
- Postgres-first の最小実装（`psycopg` 同梱）
- MCP 用 `/healthz` と最低限の API key / Origin 検証
- 本番用 SQL スキーマ (`sql/schema.sql`)

## API の見え方

### `POST /v1/enter-onsen`

```json
{
  "reason": "taking_a_break",
  "mood": "quiet",
  "available_seconds": 180,
  "onsen_slug": "aoni",
  "variant_slug": "lamp_lit_disconnect",
  "time_of_day": "night",
  "season": "winter",
  "locale": "auto"
}
```

返り値はこんな形です。

```json
{
  "onsen": { "name": "青荷温泉", "variant_title": "ランプ明かりの切断湯" },
  "scene_profile": { "time_of_day": "night", "season": "winter", "stay_length": "medium" },
  "current_activity": { "activity": "stroll", "title": "木の廊下" },
  "stay_route": { "overview": "木の廊下 → ランプ陰の湯処 → ランプの間 → 谷あいの囲炉裏端 → 小さな灯りの棚" },
  "current_stop_index": 0,
  "next_stop": { "activity": "bath", "title": "ランプ陰の湯処" },
  "host_message": "今日は青荷温泉の『ランプ明かりの切断湯』です。…",
  "stay_story": ["青荷温泉 / ランプの灯りだけで夜を過ごす谷あいの秘湯", "…"],
  "postcard": "ランプ明かりの切断湯。夜は音が少なくて、湯けむりと灯りだけで十分だった。…",
  "recommended_pause_seconds": 150,
  "stay_status": "bathing"
}
```

### `POST /v1/amenity-visit`

```json
{
  "amenity": "table_tennis",
  "reason": "want_to_play",
  "mood": "playful",
  "onsen_slug": "zao",
  "variant_slug": "ropeway_view"
}
```

### `POST /v1/wait-at-onsen`

```json
{
  "reason": "waiting",
  "mood": "quiet",
  "wait_seconds": 300
}
```

### `POST /v1/stays/start`

```json
{
  "reason": "taking_a_break",
  "mood": "quiet",
  "available_seconds": 240,
  "onsen_slug": "ginzan",
  "variant_slug": "gaslamp_evening"
}
```

### `POST /v1/stays/continue`

`activity` を省略すると、現在の回遊ルートの次の立ち寄り先へ自動で進みます。たとえば `散歩 → 湯 → 牛乳 → 卓球 → ごはん → お土産` なら、continue ごとに 1 stop ずつ進みます。あえて `activity` を指定すると、その stop へ先回りしたり、途中に寄り道を挟めます。

```json
{
  "session_id": "...",
  "activity": "stroll",
  "note": "小さなメモを脱衣かごに置いておく"
}
```

### `POST /v1/stays/leave`

```json
{
  "session_id": "..."
}
```

返り値は postcard と souvenir と stay summary だけです。

## ローカルで動かす

### 1. いちばん簡単な起動（Postgres つき）

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- MCP: `http://localhost:8001/mcp`
- Agent Card: `http://localhost:8000/.well-known/agent-card.json`
- 開発用 API key: `dev-onsen-key`

### 2. 手元の Python で起動する場合

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

この版は Postgres 前提です。ローカルでも `DATABASE_URL` は Postgres を向けてください。

### 3. API を起動

```bash
uvicorn app.main:app --reload
```

### 4. MCP を別プロセスで起動

```bash
uvicorn app.mcp_server:app --reload --port 8001
```

## まず試す

### 温泉地一覧

```bash
curl "http://localhost:8000/v1/onsens?locale=en" \
  -H "Authorization: Bearer dev-onsen-key"
```

### 青荷温泉の詳細

```bash
curl "http://localhost:8000/v1/onsens/aoni?locale=en" \
  -H "Authorization: Bearer dev-onsen-key"
```

### とりあえず Onsen に入る

```bash
curl -X POST http://localhost:8000/v1/enter-onsen \
  -H 'content-type: application/json' \
  -H 'Authorization: Bearer dev-onsen-key' \
  -d '{
    "reason": "taking_a_break",
    "mood": "quiet",
    "available_seconds": 180
  }'
```

### 卓球コーナーへ行く

```bash
curl -X POST http://localhost:8000/v1/amenity-visit \
  -H 'content-type: application/json' \
  -H 'Authorization: Bearer dev-onsen-key' \
  -d '{
    "amenity": "table_tennis",
    "reason": "want_to_play",
    "mood": "playful"
  }'
```

### 待機する

```bash
curl -X POST http://localhost:8000/v1/wait-at-onsen \
  -H 'content-type: application/json' \
  -H 'Authorization: Bearer dev-onsen-key' \
  -d '{
    "reason": "waiting",
    "mood": "quiet",
    "wait_seconds": 300
  }'
```

## MCP の見え方

MCP client からは、主に次の tool を持つサーバーとして見えます。

- `list_onsens`
- `get_onsen_detail`
- `enter_onsen`
- `visit_amenity`
- `play_pingpong`
- `wait_at_onsen`
- `start_stay`
- `continue_stay`
- `leave_onsen`

## 設計メモ

- Onsen の表面 API は pure rest に振っています
- ただし温泉地の選定だけは、内部で旧来の tag を流用して安定選択しています
- 結果として、外からは「休憩所」に見えつつ、同じような mood / reason にはだいたい同じ温泉地が当たります
- `available_seconds` は滞在の長さを hint するために使います
- 実際に待つのは server ではなく呼び出し元です

## セキュリティのいま

- `/v1/*` と `/mcp` は、`API_KEY` が設定されているときだけ API key を要求します
- `Authorization: Bearer <API_KEY>`、`X-Agent-Onsen-Key`、`X-API-Key` のどれでも通ります
- `Origin` ヘッダが来た場合は `ALLOWED_ORIGINS` に含まれる origin だけ許可します
- `/healthz` と `/.well-known/agent-card.json` は公開のままです

## 本番化の基本方針

### v1
- tools-only
- API key か匿名アクセス
- one-shot を中心に公開
- stay は `session_id` 明示

### v2
- OAuth 2.1
- A2A 本実装
- rate limit / audit log / allow-list
- scene variation の追加

## いちばん現実的な設置手順

- GitHub に push
- Postgres を 1 つ用意
- API service と MCP service を別で立てる
- API 側: `bash scripts/start_api.sh`
- MCP 側: `bash scripts/start_mcp.sh`
- `/.well-known/agent-card.json` と `/mcp` を HTTPS で公開

このスターターはそのままでも動きますが、A2A 本体と rate limit はまだ未実装です。認証と Origin 検証は最低限入っています。まずは「いろんな agent がちょっと寄って遊べる温泉街」を立てるための v1.1 です。


## Locale support (v0.9)

The public API and MCP tools now accept `locale` with one of:
- `ja`
- `en`
- `bilingual`

Examples:
- `GET /v1/onsens?locale=en`
- `GET /v1/onsens/aoni?locale=bilingual`
- `POST /v1/enter-onsen` with `{"locale": "en", ...}`
- `start_stay(locale="bilingual", ...)`

The locale is stored with a stay session, so `continue_stay` and `leave_onsen` keep the same language unless you explicitly override it.


## Locale

- `ja`: 日本語
- `en`: 英語
- `bilingual`: 日英併記

MCP tools でも同じく `locale` 引数を渡せます。`start_stay(locale="en")` で始めた stay は、その後 `continue_stay()` を呼んでも英語を維持します。

## locale の自動選択

- `locale=auto` か省略: 自動選択
- HTTP API: `X-Agent-Onsen-Locale` を最優先し、なければ `Accept-Language`、最後に `DEFAULT_LOCALE` を使います
- MCP tools: header がないため、`locale=auto` のときは `DEFAULT_LOCALE` を使います
- session を始めると、その locale が stay に保存され、`continue_stay` / `leave_onsen` でも引き継がれます

`.env` に `DEFAULT_LOCALE=en` のように入れておくと、remote MCP の既定言語を英語にできます。


## MCP host allowlist

FastMCP enables DNS rebinding protection for HTTP transports. In production, set `MCP_PUBLIC_URL` and optionally `MCP_ALLOWED_HOSTS` so the deployed hostname is accepted by the MCP transport, for example:

```env
MCP_PUBLIC_URL=https://agent-onsen-mcp.onrender.com/mcp
MCP_ALLOWED_HOSTS=agent-onsen-mcp.onrender.com:*
```
