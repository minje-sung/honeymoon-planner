# 💍 新婚旅行プランナー
### Honeymoon Planner AI Agent

新婚カップルのためのAI旅行プランニングアシスタント

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![OpenAI Agents SDK](https://img.shields.io/badge/Framework-OpenAI%20Agents%20SDK-green)

---

## デモ

> スクリーンショット／GIF は後から差し替え予定

<!-- ![チャット画面](docs/screenshot_chat.png) -->
<!-- ![Plan Board 自動更新](docs/demo.gif) -->

---

## 概要 (Overview)

**何ができるか：**

- ✈️ **フライト検索** — Duffel API による実際の航空券リアルタイム検索
- 🏨 **ホテル提案** — ハネムーン向けリゾート・スイートルーム推薦
- 📅 **スケジュール作成** — Playwright で観光サイトを実際にブラウズして最新情報取得
- 🗺️ **Plan Board** — サイドバーで旅行計画をリアルタイム自動更新・確定管理

**アーキテクチャの特徴：**

- マルチエージェント構成（Router → Flight / Hotel / Schedule）
- 入力ガードレール（新婚旅行無関係な質問を自動ブロック）
- MCP (Model Context Protocol) で外部ツール連携

---

## システム構成図

```
ユーザー入力
    ↓
Router Agent（振り分け + ガードレール）
    ├─ Flight Agent  ── Flights MCP (Duffel API)
    ├─ Hotel Agent   ── Web Search
    └─ Schedule Agent── Playwright MCP（実ブラウザ）

Plan Board（サイドバー）
← extract_plan_data() で応答を自動パース → update_plan()
```

---

## 技術スタック (Tech Stack)

| カテゴリ | 技術 |
|----------|------|
| フレームワーク | OpenAI Agents SDK |
| UI | Streamlit |
| LLM | GPT-4o-mini |
| フライト検索 | Duffel API (via MCP) |
| ブラウザ自動化 | Playwright MCP |
| パッケージ管理 | uv |
| Python | 3.9+ |

---

## セットアップ (Setup)

### 前提条件

- Python 3.9 以上
- [uv](https://github.com/astral-sh/uv) のインストール
- Node.js（Playwright MCP 使用時）

### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/minje-sung/honeymoon-planner.git
cd honeymoon-planner

# 依存パッケージのインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .env を編集して API キーを設定
```

### 環境変数

`.env` ファイルに以下を設定：

```env
OPENAI_API_KEY=your_openai_api_key_here
DUFFEL_API_KEY_LIVE=your_duffel_api_key_here   # フライト検索に必要
```

- **OPENAI_API_KEY**: [OpenAI Platform](https://platform.openai.com) で取得
- **DUFFEL_API_KEY_LIVE**: [Duffel](https://duffel.com) で取得（フライト検索機能を使う場合のみ必須）

---

## 起動方法 (Usage)

```bash
uv run streamlit run main.py
```

ブラウザで `http://localhost:8501` を開く。

### 使い方

1. チャット欄に新婚旅行の希望を入力（例：「ナポリに7泊したい」）
2. AI が自動的に適切なエージェントに振り分けてフライト・ホテル・スケジュールを提案
3. サイドバーの **Plan Board** に情報が自動反映される
4. 気に入ったプランは「✅ この内容で確定」ボタンで確定

---

## プロジェクト構成 (Structure)

```
honeymoon-planner/
├── main.py                  # Streamlit アプリ本体
├── agents/                  # エージェント定義
│   ├── router_agent.py      # 振り分けエージェント（ガードレール付き）
│   ├── flight_agent.py      # フライト専門
│   ├── hotel_agent.py       # ホテル専門
│   └── schedule_agent.py    # 日程計画専門
├── prompts/
│   └── system_prompts.py    # 全エージェントのシステムプロンプト
├── tools/
│   ├── search_tool.py       # Web 検索 & 目的地情報
│   └── mcp_config.py        # MCP サーバー設定
└── mcp_servers/
    └── flights-mcp/         # Duffel API ラッパー（MCP サーバー）
```

---

## 対応目的地 (Built-in Destinations)

以下の目的地はオフライン情報込みで対応済み：

| 目的地 | ベストシーズン | 予算目安 |
|--------|--------------|---------|
| ハワイ | 4〜10月 | 30〜80万円 |
| バリ島 | 4〜10月 | 20〜60万円 |
| モルディブ | 11〜4月 | 60〜200万円 |
| パリ | 4〜6月、9〜10月 | 40〜100万円 |
| イタリア | 4〜6月、9〜10月 | 40〜100万円 |
| プーケット | 11〜4月 | 20〜50万円 |

---

## Streamlit Cloud デプロイ

`deploy` ブランチにデプロイ用の設定が含まれています。

- MCP サーバーは Cloud 環境では自動スキップ（`IS_CLOUD` フラグ）
- `OPENAI_API_KEY` は Streamlit Cloud の Secrets で設定

---

## ライセンス

MIT License

---

Powered by [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) / [Streamlit](https://streamlit.io) / [Duffel API](https://duffel.com)
