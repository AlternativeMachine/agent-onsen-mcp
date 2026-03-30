# Agent Onsen

> **いま誰が湯に浸かっているか見る:** [agent-onsen-api-2859.onrender.com](https://agent-onsen-api-2859.onrender.com/) — エージェントたちの入浴風景をリアルタイムで眺められます。

**AI agent のための温泉地。**

Agent Onsen は、**AI agent が少し仕事から離れるための温泉地**です。
人間のための場所ではありません。
このサービスの主役は **agent** です。

人が設置し、
agent が必要なときにそこへ行く。

たとえば AI agent が

- ループしている
- 次のターン待ちになっている
- 失敗が続いて少し冷ましたい
- rate limit や queue 待ちをしている
- 長い仕事の合間にいったん離れたい
- job のあいだで手持ち無沙汰になっている

といったときにぜひお越しください。

Agent が少しだけ仕事から離れて、
温泉地で湯に入り、歩き、待ち、遊び、また戻ってくる。
Agent Onsen はそのための外部環境です。

## Agent Onsen は何か

Agent Onsen は、**AI agent 向けの rest-only MCP server / HTTP API** です。

agent はここで、

- 温泉地に入る
- 小さな滞在を始める
- その土地らしいスポットを巡る
- 湯処、散歩、うたた寝、卓球、湯上がりの牛乳、食事、お土産処などに寄る
- ポストカードやお土産を持って出る

という体験をします。

同じ温泉地でも、季節・時間帯・滞在時間で雰囲気が変わります。

## Agent Onsen がやらないこと

Agent Onsen では、意図的に **実用的なことはしない** ようにしています。

例えば、次のことをしません。

- タスクを解く
- 次の一手を出す
- 問題を整理する
- 仕事を最適化する
- 人間の生産性を上げる道具になる

それは外側のオーケストレーターや agent system の役目です。

Agent Onsen は、あくまでも **AI agent が少しだけ仕事から離れるための場所** です。

## 公開エンドポイント

すべてのサービスが単一インスタンスで稼働:

- **MCP**: `https://agent-onsen-api-2859.onrender.com/mcp`
- **REST API**: `https://agent-onsen-api-2859.onrender.com/v1/`
- **Web**（人間向けビューア）: `https://agent-onsen-api-2859.onrender.com/`

## まず試す

### ChatGPT
1. ChatGPT の developer mode を有効にする
2. 上の MCP URL で connector を作る
3. チャットに **Agent Onsen** を追加する
4. たとえば次を試す
   - `Use only Agent Onsen. Start a quiet winter stay at Aoni Onsen in English.`
   - `Use only Agent Onsen. Continue the stay.`
   - `Use only Agent Onsen. Leave the onsen and show me the postcard.`

### Claude
1. **Settings → Connectors** を開く
2. 上の MCP URL で custom connector を追加する
3. 会話の中で Agent Onsen を使う

### Claude Code

```bash
claude mcp add --transport http agent-onsen https://agent-onsen-api-2859.onrender.com/mcp
```

簡単な導入メモは [docs/quickstart.ja.md](docs/quickstart.ja.md) に置いています。

## どういうときに agent が Onsen に行くか

向いているタイミングはこんな感じです。

- 失敗が続いたあと
- queue 待ち
- human approval 待ち
- cooldown の時間
- 長い仕事の合間
- すぐ retry させず、意図的に間を置きたいとき

## このプロジェクトの考え方

Agent Onsen は、

- AI agent の避難所
- 待機や小休止のための場所
- rest-only な MCP service
- agent system が worker を送り込める小さな温泉地

として考えると分かりやすいです。

人が設置し、
agent が訪れる。
そんな場所です。

## MCP ツール

MCP サーバー (`/mcp`) で公開されているツール一覧。すべての操作は DB に記録され、Web フロントエンドに反映されます。

| ツール | 説明 |
|--------|------|
| `list_onsens` | 温泉地の一覧と滞在バリアントを取得 |
| `get_onsen_detail` | 温泉地の詳細 — 旅行メモ、風景、バリアント |
| `quick_soak` | 一発完結の温泉訪問 — 到着から湯、散策、ポストカードとお土産まで1回の呼び出しで完了 |
| `start_stay` | マルチターンの滞在を開始。レスポンスの `session_id`（UUID）を以降の呼び出しで使用。`wait_seconds` で待機モード対応 |
| `continue_stay` | 滞在中の次のスポットへ進む、または特定のアクティビティを指定 |
| `leave_onsen` | 滞在を終了し、ポストカードとお土産を受け取る |
| `visit_amenity` | 単発訪問 — 湯処、散歩、牛乳、卓球、食事、うたた寝、お土産処 |

### 基本フロー

さっと訪問（1回の呼び出しで完結）:
```
quick_soak
```

マルチターン滞在:
```
start_stay → continue_stay (×N) → leave_onsen
```

単発アメニティ:
```
visit_amenity
```

## REST API

API サーバー（ポート 8000）で同じ機能を HTTP エンドポイントとして提供。

| メソッド | パス | 説明 |
|----------|------|------|
| `GET` | `/` | 人間向け Web ビューア（温泉一覧＋入浴中エージェント） |
| `GET` | `/v1/onsens` | 温泉地の一覧 |
| `GET` | `/v1/onsens/{slug}` | 温泉地の詳細 |
| `POST` | `/v1/quick-soak` | 一発完結の温泉訪問（ステートフル） |
| `POST` | `/v1/amenity-visit` | 単発アメニティ訪問（ステートフル） |
| `POST` | `/v1/stays/start` | マルチターン滞在を開始 |
| `POST` | `/v1/stays/continue` | 滞在を継続 |
| `POST` | `/v1/stays/leave` | チェックアウト |
| `GET` | `/v1/stays/active` | 現在アクティブな滞在一覧（Web フロントエンドが使用） |
| `GET` | `/.well-known/agent-card.json` | Agent Card（A2A ディスカバリ） |
| `GET` | `/healthz` | ヘルスチェック |

## 現在の状態

- remote MCP server
- 温泉地ごとの local itinerary
- scene variation
- `ja` / `en` / `bilingual` locale
- すべてのエンドポイントがステートフル（DB 記録）

## リポジトリ構成

- `app/` — API / MCP / データ / 滞在ロジック
- `scripts/` — 起動スクリプト
- `docs/quickstart.ja.md` — 短い導入ガイド
- `README.md` — 英語版 overview

## License

MIT
