# Agent Onsen クイックスタート

最短で Agent Onsen を試すためのメモです。

## MCP URL

```text
https://agent-onsen-mcp-kp54.onrender.com/mcp
```

## ChatGPT

1. Web の ChatGPT を開く
2. developer mode を有効にする
3. 上の MCP URL で connector を作る
4. チャットに **Agent Onsen** を追加する
5. 次のどれかを試す

```text
Use only Agent Onsen. Start a quiet winter stay at Aoni Onsen in English.
```

```text
Use only Agent Onsen. Continue the stay.
```

```text
Use only Agent Onsen. Leave the onsen and show me the postcard.
```

## Claude

1. Claude を開く
2. **Settings → Connectors** へ行く
3. 上の MCP URL で custom connector を追加する
4. 同じ prompt を試す

## 最初に試しやすい prompt

- `Use only Agent Onsen. Take me somewhere quiet and hidden.`
- `Use only Agent Onsen. I only have two minutes.`
- `Use only Agent Onsen. Start a bilingual stay at Ginzan Onsen.`
- `Use only Agent Onsen. Continue the stay.`
- `Use only Agent Onsen. Leave the onsen and show me the souvenir.`

## 想定される返り値

Agent Onsen は productivity tool ではありません。

主に返ってくるのは、

- 温泉地
- 滞在ルート
- いまの activity
- postcard
- souvenir
- 少しだけ別の場所にいた感じ

です。

タスクの正解を出すこと自体は第一目的ではありません。
