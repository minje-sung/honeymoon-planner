# 新婚旅行プランナー / Honeymoon Planner

> OpenAI Agents SDK を使ったマルチエージェント旅行プランニングアシスタント  
> A multi-agent travel planning assistant built with OpenAI Agents SDK

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://honeymoon-planner.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org)
[![OpenAI Agents SDK](https://img.shields.io/badge/OpenAI_Agents_SDK-latest-green)](https://github.com/openai/openai-agents-python)

---

## 日本語 | [English](#english)

---

## 概要

新婚旅行の計画をチャットで完結できる AI アシスタントです。ユーザーの質問を分析し、航空便・ホテル・旅行日程の 3 領域を担当する専門エージェントに自動で振り分けます。会話の内容はリアルタイムでサイドバーの **Plan Board** に構造化されて表示されます。

## アーキテクチャ

```
ユーザー入力
     │
     ▼
[Input Guardrail] ── 新婚旅行と無関係な質問をここでブロック
     │
     ▼
Router Agent (honeymoon_planner)
     │
     ├─ handoff ──▶ Flight Agent   [WebSearchTool + get_destination_info + flights-mcp]
     ├─ handoff ──▶ Hotel Agent    [WebSearchTool + get_destination_info]
     └─ handoff ──▶ Schedule Agent [get_destination_info + Playwright MCP]
                                              ↓
                                   Google マップをリアルタイム検索して観光地情報を取得
```

---

## 開発時に重要だったポイント

### 1. Handoff — 専門エージェントへの委任

一つの巨大なエージェントではなく、役割を分離した専門エージェントに委任する構造を採用しました。

```python
router_agent = Agent(
    name="honeymoon_planner",
    handoffs=[flight_agent, hotel_agent, schedule_agent],
)
```

SDK は `handoffs` リストから `transfer_to_flight_agent` などのツールを自動生成します。各エージェントのプロンプトが小さくなり精度が上がるだけでなく、後から新しい専門エージェント（例：旅行保険エージェント）を追加するのも容易です。

---

### 2. Input Guardrail — メインエージェントに到達する前にブロック

新婚旅行と無関係な質問を、メインエージェントが処理する前にブロックします。

```python
@input_guardrail
async def honeymoon_guardrail(context, agent, input):
    result = await Runner.run(guardrail_agent, input)  # 軽量な判定エージェント
    is_irrelevant = "関連なし" in result.final_output
    return GuardrailFunctionOutput(tripwire_triggered=is_irrelevant)
```

判定自体も別の軽量エージェント（`guardrail_agent`）が担当します。メインエージェントを動かす前にブロックできるため、無駄な API コストが発生しません。`InputGuardrailTripwireTriggered` 例外をキャッチして、UI で丁寧なメッセージを表示します。

---

### 3. MCP — 2 種類の異なる連携方式

このプロジェクトでは性格の異なる 2 つの MCP を使用しています。

| | flights-mcp | Playwright MCP |
|---|---|---|
| 役割 | 実際の航空便検索 | ブラウザ操作で Google マップをリアルタイム検索 |
| 実行方式 | `uv run`（ローカルソース） | `npx @playwright/mcp@latest`（自動ダウンロード） |
| 注入先 | Flight Agent | Schedule Agent |

エージェント実行時に MCP サーバーを `async with` で起動し、`clone(mcp_servers=[...])` でエージェントに注入します。Playwright MCP は起動失敗時に自動でフォールバックするよう実装しています。

```python
async with create_flight_mcp_server() as flight_mcp:
    flight_agent_with_mcp = flight_agent.clone(mcp_servers=[flight_mcp])
```

---

### 4. Streaming + ツール通知 — リアルタイムフィードバック

`Runner.run_streamed()` でテキストをトークン単位で表示し、ツール呼び出し時は `st.toast()` で通知します。

```python
async for event in stream.stream_events():
    if isinstance(event.data, ResponseTextDeltaEvent):
        placeholder.markdown(response_text + "▌")   # カーソル演出
    elif isinstance(event.data, ResponseOutputItemDoneEvent):
        st.toast(f"🔧 Tool: {tool_name}")            # どのツールが呼ばれたか表示
```

---

### 5. Trace — 実行フローの可視化

```python
with trace("新婚旅行プランナー"):
    stream = Runner.run_streamed(router_agent, messages)
```

`with trace("名前")` で囲むだけで、OpenAI Traces ダッシュボードに実行フローが記録されます。どのエージェントに handoff されたか、どのツールが呼ばれたか、何秒かかったかが一目でわかります。

---

### 6. Plan Board — 自然言語応答から構造化データを抽出

エージェントの自然言語応答を、別途 LLM を呼び出して JSON に変換し、サイドバーのプランボードに反映します。

```python
async def extract_plan_data(response_text: str) -> dict:
    # gpt-4o-mini に応答テキストを渡し、航空便・ホテル・日程情報を JSON で抽出
```

確定済みの航空便・ホテルは `flight_confirmed` フラグで保護し、以降の会話で上書きされないようにしています。

---

### 7. ローカル / Cloud 環境の自動分岐

ローカル開発では `.env` から API キーを読み込み、Streamlit Cloud では `st.secrets` から読み込む二重対応です。MCP サーバーも `mcp_servers/` フォルダの存在有無で環境を判定し、Cloud では自動的にダミーサーバーに切り替わります（`deploy` ブランチ）。

---

## 技術スタック

| カテゴリ | 技術 |
|---|---|
| AI フレームワーク | OpenAI Agents SDK |
| LLM | GPT-4o-mini |
| UI | Streamlit |
| MCP | flights-mcp, Playwright MCP |
| モニタリング | OpenAI Traces |
| デプロイ | Streamlit Cloud |

---

## ローカル実行

```bash
git clone https://github.com/minje-sung/honeymoon-planner
cd honeymoon-planner
uv sync
cp .env.example .env
# .env に OPENAI_API_KEY を記入
uv run streamlit run main.py
```

---

---

<a name="english"></a>

## English | [日本語](#日本語--english)

---

## Overview

An AI assistant that helps you plan your honeymoon entirely through chat. It analyzes user input and automatically routes questions to specialized agents handling flights, hotels, and travel itineraries. Conversation content is structured in real time and displayed in the sidebar **Plan Board**.

## Architecture

```
User Input
     │
     ▼
[Input Guardrail] ── Blocks unrelated questions before they reach the main agent
     │
     ▼
Router Agent (honeymoon_planner)
     │
     ├─ handoff ──▶ Flight Agent   [WebSearchTool + get_destination_info + flights-mcp]
     ├─ handoff ──▶ Hotel Agent    [WebSearchTool + get_destination_info]
     └─ handoff ──▶ Schedule Agent [get_destination_info + Playwright MCP]
                                              ↓
                                   Real-time Google Maps search for attraction data
```

---

## Key Development Points

### 1. Handoff — Delegating to Specialized Agents

Instead of a single monolithic agent, the system delegates to specialized agents with clearly separated responsibilities.

```python
router_agent = Agent(
    name="honeymoon_planner",
    handoffs=[flight_agent, hotel_agent, schedule_agent],
)
```

The SDK automatically generates tools like `transfer_to_flight_agent` from the `handoffs` list. Each agent's prompt stays small and focused, improving accuracy. Adding new agents later (e.g., a travel insurance agent) is straightforward.

---

### 2. Input Guardrail — Block Before Reaching the Main Agent

Off-topic questions are blocked before the main agent even starts processing.

```python
@input_guardrail
async def honeymoon_guardrail(context, agent, input):
    result = await Runner.run(guardrail_agent, input)  # Lightweight classifier agent
    is_irrelevant = "関連なし" in result.final_output
    return GuardrailFunctionOutput(tripwire_triggered=is_irrelevant)
```

The classification itself is handled by a separate lightweight agent (`guardrail_agent`). Blocking before the main agent runs prevents unnecessary API costs. The `InputGuardrailTripwireTriggered` exception is caught to display a friendly message in the UI.

---

### 3. MCP — Two Different Integration Patterns

This project uses two MCPs with fundamentally different characteristics.

| | flights-mcp | Playwright MCP |
|---|---|---|
| Role | Real flight search | Real-time Google Maps via browser control |
| Execution | `uv run` (local source) | `npx @playwright/mcp@latest` (auto-download) |
| Injected into | Flight Agent | Schedule Agent |

MCP servers are started with `async with` at runtime and injected into agents via `clone(mcp_servers=[...])`. Playwright MCP automatically falls back gracefully if startup fails.

```python
async with create_flight_mcp_server() as flight_mcp:
    flight_agent_with_mcp = flight_agent.clone(mcp_servers=[flight_mcp])
```

---

### 4. Streaming + Tool Notifications — Real-time Feedback

`Runner.run_streamed()` displays text token by token, and `st.toast()` notifies the user when a tool is called.

```python
async for event in stream.stream_events():
    if isinstance(event.data, ResponseTextDeltaEvent):
        placeholder.markdown(response_text + "▌")   # Typing cursor effect
    elif isinstance(event.data, ResponseOutputItemDoneEvent):
        st.toast(f"🔧 Tool: {tool_name}")            # Show which tool was invoked
```

---

### 5. Trace — Visualizing Execution Flow

```python
with trace("新婚旅行プランナー"):
    stream = Runner.run_streamed(router_agent, messages)
```

Wrapping execution with `with trace("name")` records the full execution flow in the OpenAI Traces dashboard — which agent received the handoff, which tools were called, and how long each step took.

---

### 6. Plan Board — Extracting Structured Data from Natural Language

Agent responses in natural language are converted to JSON via a separate LLM call and reflected in the sidebar Plan Board.

```python
async def extract_plan_data(response_text: str) -> dict:
    # Passes response text to gpt-4o-mini to extract flight/hotel/schedule data as JSON
```

Confirmed flights and hotels are protected by a `flight_confirmed` flag to prevent them from being overwritten by subsequent conversations.

---

### 7. Local / Cloud Environment Auto-switching

API keys are loaded from `.env` in local development and from `st.secrets` on Streamlit Cloud. MCP servers are also auto-detected: if the `mcp_servers/` folder doesn't exist (Cloud environment), they automatically switch to dummy servers (`deploy` branch).

---

## Tech Stack

| Category | Technology |
|---|---|
| AI Framework | OpenAI Agents SDK |
| LLM | GPT-4o-mini |
| UI | Streamlit |
| MCP | flights-mcp, Playwright MCP |
| Monitoring | OpenAI Traces |
| Deploy | Streamlit Cloud |

---

## Local Setup

```bash
git clone https://github.com/minje-sung/honeymoon-planner
cd honeymoon-planner
uv sync
cp .env.example .env
# Add your OPENAI_API_KEY to .env
uv run streamlit run main.py
```

---

[Portfolio](https://minje-sung.github.io) · [Demo](https://honeymoon-planner.streamlit.app)