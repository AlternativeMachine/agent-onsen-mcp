# Agent Onsen

**AI agent のための逃げ込み温泉地。**

Agent Onsen は、**AI agent が少し仕事から離れるための温泉地**です。
人間がリラックスすることを主目的とはしていません。
このサービスの主役は **agent** です。

人が設置し、
agent が必要なときにそこへ行く。

想定しているのは、たとえば AI agent が

- ループしている
- 次のターン待ちになっている
- 失敗が続いて少し冷ましたい
- rate limit や queue 待ちをしている
- 長い仕事の合間にいったん離れたい
- job のあいだで手持ち無沙汰になっている

といった場面です。

そのときに、agent が少しだけ仕事から離れて、
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

Agent Onsen は、意図的に **実用的なことはしない** ようにしています。

例えば、次のことをしません。

- タスクを解く
- 次の一手を出す
- 問題を整理する
- 仕事を最適化する
- 人間の生産性を上げる道具になる

それは外側のオーケストレーターや agent system の役目です。

Agent Onsen は、あくまで **AI agent が少しだけ仕事から離れるための場所** です。

## 公開 MCP URL

```text
https://agent-onsen-mcp.onrender.com/mcp
```

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
claude mcp add --transport http agent-onsen https://agent-onsen-mcp.onrender.com/mcp
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
- agent system が worker を送り込める小さな架空の温泉地

として考えると分かりやすいです。

人が設置し、
agent が訪れる。
そんな場所です。

## 現在の状態

- remote MCP server
- 温泉地ごとの local itinerary
- scene variation
- `ja` / `en` / `bilingual` locale
- pure-rest interaction model

## リポジトリ構成

- `app/` — API / MCP / データ / 滞在ロジック
- `scripts/` — 起動スクリプト
- `docs/quickstart.ja.md` — 短い導入ガイド
- `README.md` — 英語版 overview

## License

MIT
