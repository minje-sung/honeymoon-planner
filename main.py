import asyncio
import json
import re

import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv("/Users/minje/.env.shared/.env.honeymoon")
from openai import AsyncOpenAI
from agents import Runner, trace
from agents import InputGuardrailTripwireTriggered
from openai.types.responses import (
    ResponseTextDeltaEvent,
    ResponseOutputItemDoneEvent,
    ResponseFunctionToolCall,
)

from agents.router_agent import router_agent
from agents.flight_agent import flight_agent
from agents.hotel_agent import hotel_agent
from agents.schedule_agent import schedule_agent
from tools.mcp_config import create_flight_mcp_server, create_playwright_mcp_server

# ─────────────────────────────
# ページ設定
# ─────────────────────────────
st.set_page_config(
    page_title="新婚旅行プランナー",
    page_icon="💍",
    layout="wide",
)

# ─────────────────────────────
# CSS — minje-sung.github.io トーン × ハネムーン
# ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Noto+Sans+JP:wght@300;400;500&family=Space+Mono:ital@0;1&display=swap');

/* ══════════════════════════════
   BASE — ダークネイビー背景
══════════════════════════════ */
html, body, .stApp {
    background-color: #1c1f35 !important;
    font-family: 'Noto Sans JP', sans-serif;
    color: #ffffff;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 820px;
    margin: 0 auto;
}

/* ══════════════════════════════
   SIDEBAR — ライト
══════════════════════════════ */
[data-testid="stSidebar"] {
    background: #f8f6ff !important;
    border-right: 1px solid #e8e0f0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}
[data-testid="stSidebar"]::-webkit-scrollbar { width: 4px; }
[data-testid="stSidebar"]::-webkit-scrollbar-track { background: transparent; }
[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background: #e0d0e8;
    border-radius: 4px;
}

/* ══════════════════════════════
   CHAT HEADER
══════════════════════════════ */
.chat-header {
    text-align: center;
    padding: 0 0 2rem;
}
.chat-header-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.25em;
    color: #ff6a9c;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.chat-header-title {
    font-family: 'Syne', sans-serif;
    font-size: 36px;
    font-weight: 800;
    background: linear-gradient(135deg, #ff6a9c 0%, #ffd580 60%, #ff6a9c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.chat-header-sub {
    font-size: 13px;
    color: #a0a8c0;
    margin-top: 8px;
}

/* ══════════════════════════════
   CHAT MESSAGES — ライトカード
══════════════════════════════ */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 1px solid #ece8f5 !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 16px rgba(0,0,0,0.15) !important;
    margin-bottom: 10px !important;
    transition: box-shadow 0.2s !important;
}
[data-testid="stChatMessage"]:hover {
    box-shadow: 0 4px 24px rgba(0,0,0,0.2) !important;
}
/* チャットメッセージ内テキスト */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span {
    color: #1a1c35 !important;
}

/* ══════════════════════════════
   CHAT INPUT — ライト
══════════════════════════════ */
[data-testid="stChatInputTextArea"] {
    background: #ffffff !important;
    border: 1.5px solid #d8d0ee !important;
    border-radius: 14px !important;
    color: #1a1c35 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    font-size: 14px !important;
}
[data-testid="stChatInputTextArea"]:focus {
    border-color: #c9748a !important;
    box-shadow: 0 0 0 3px rgba(201,116,138,0.12) !important;
}
[data-testid="stChatInputTextArea"]::placeholder {
    color: #a0a0c0 !important;
}

/* ══════════════════════════════
   BUTTONS
══════════════════════════════ */
.stButton > button {
    background: #ffffff !important;
    border: 1.5px solid #e090a8 !important;
    color: #c0326a !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.05em !important;
    transition: all 0.2s ease !important;
    padding: 0.35rem 0.8rem !important;
}
.stButton > button:hover {
    background: #fff0f5 !important;
    border-color: #c0326a !important;
    box-shadow: 0 4px 12px rgba(192,50,106,0.2) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

.stLinkButton > a {
    background: #ffffff !important;
    border: 1.5px solid #d4a853 !important;
    color: #a07820 !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.05em !important;
    transition: all 0.2s ease !important;
    text-decoration: none !important;
    padding: 0.35rem 0.8rem !important;
}
.stLinkButton > a:hover {
    background: #fffbf0 !important;
    border-color: #a07820 !important;
    box-shadow: 0 4px 12px rgba(160,120,32,0.2) !important;
    transform: translateY(-1px) !important;
}

/* ══════════════════════════════
   EXPANDER (サイドバー内)
══════════════════════════════ */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e8e0f0 !important;
    border-radius: 10px !important;
    margin-bottom: 6px !important;
}
[data-testid="stExpander"]:hover {
    border-color: #d090b0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
[data-testid="stExpander"] summary {
    color: #5a4070 !important;
    font-size: 12px !important;
    font-family: 'Space Mono', monospace !important;
}

/* ══════════════════════════════
   TOAST / ALERT
══════════════════════════════ */
[data-testid="stToast"] {
    background: #ffffff !important;
    border: 1px solid #e8e0f0 !important;
    border-radius: 12px !important;
    color: #1a1c35 !important;
    font-family: 'Noto Sans JP', sans-serif !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15) !important;
}
[data-testid="stAlertContainer"] {
    background: #fff8fb !important;
    border: 1px solid #f0c0d0 !important;
    border-radius: 12px !important;
    color: #1a1c35 !important;
}

/* ══════════════════════════════
   PLAN BOARD — ライトサイドバー用
══════════════════════════════ */
.pb-title {
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 800;
    color: #c0326a;
    letter-spacing: 0.02em;
    margin-bottom: 4px;
}
.pb-sub {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #b0a0c0;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 20px;
}
.pb-card {
    background: #ffffff;
    border: 1px solid #ede8f5;
    border-top: 2px solid #e05080;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
.pb-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.pb-card-hotel {
    border-top-color: #c9a032;
}
.pb-card-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #b0a0c0;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.pb-route {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: #c0326a;
    letter-spacing: 4px;
    text-align: center;
    padding: 6px 0 10px;
}
.pb-hotel-name {
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: #8a6010;
    text-align: center;
    padding: 6px 0 10px;
    line-height: 1.3;
    letter-spacing: 1px;
}
.pb-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid #f5f0fc;
    font-size: 11px;
    gap: 8px;
}
.pb-row:last-child { border-bottom: none; }
.pb-key {
    font-family: 'Space Mono', monospace;
    color: #b0a0c0;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    flex-shrink: 0;
}
.pb-val { color: #3a3050; text-align: right; font-weight: 500; }
.pb-val-price {
    color: #c0326a;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    text-align: right;
}
.pb-val-price-hotel {
    color: #8a6010;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    text-align: right;
}
.pb-tbd {
    color: #c8c0d8;
    font-style: italic;
    font-size: 10px;
    text-align: right;
}
.pb-dest {
    font-family: 'Syne', sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #2a2040;
    text-align: center;
    margin-bottom: 14px;
}
.pb-badge {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    background: #fce8f0;
    border: 1px solid #f0c0d0;
    color: #c0326a;
    border-radius: 20px;
    padding: 2px 8px;
    letter-spacing: 0.05em;
    margin-left: 8px;
}
.pb-empty {
    border: 1.5px dashed #e0d8f0;
    border-radius: 12px;
    padding: 40px 16px;
    text-align: center;
    background: #faf8ff;
}
.pb-empty-icon { font-size: 28px; margin-bottom: 10px; }
.pb-empty-text {
    font-family: 'Space Mono', monospace;
    color: #c0b8d8;
    font-size: 10px;
    line-height: 2.2;
    letter-spacing: 0.03em;
}
.schedule-time {
    color: #c0326a;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    min-width: 44px;
    flex-shrink: 0;
    font-weight: 700;
}
.schedule-desc {
    color: #5a4870;
    font-size: 12px;
    line-height: 1.5;
}

/* ══════════════════════════════
   確定済みカード
══════════════════════════════ */
.pb-card-confirmed {
    border-top-color: #22c55e !important;
    background: #f0fdf4 !important;
}
.pb-confirmed-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #dcfce7;
    border: 1px solid #86efac;
    color: #16a34a;
    border-radius: 20px;
    padding: 2px 10px;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    margin-bottom: 10px;
}

/* 確定ボタン（primary） */
button[kind="primary"] {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    border-color: #22c55e !important;
    color: #ffffff !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    border-color: #16a34a !important;
    box-shadow: 0 4px 14px rgba(34,197,94,0.35) !important;
    transform: translateY(-1px) !important;
}

/* HR */
hr { border-color: #e8e0f0 !important; margin: 12px 0 !important; }

/* ══════════════════════════════
   スポット チェックリスト
══════════════════════════════ */
[data-testid="stSidebar"] [data-testid="stCheckbox"] {
    background: #faf8ff;
    border: 1px solid #ede8f5;
    border-radius: 8px;
    padding: 4px 8px;
    margin-bottom: 4px;
    transition: background 0.15s;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"]:hover {
    background: #f3eefb;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
    color: #3a3050 !important;
    font-size: 12px !important;
    font-family: 'Noto Sans JP', sans-serif !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] input:checked + div {
    background-color: #c0326a !important;
    border-color: #c0326a !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────
# session_state 初期化
# ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.sdk_history = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "新婚旅行プランナーへようこそ。💍\n\n"
            "フライト、ホテル、旅行スケジュールなど、"
            "ハネムーンに関するご質問はなんでもお気軽にどうぞ！\n\n"
            "✈️ 人気の目的地：ハワイ、バリ島、モルディブ、パリ、イタリア、プーケット"
        ),
    })

if "plan" not in st.session_state:
    st.session_state.plan = {
        "destination": None,
        "nights": None,
        "flight": None,
        "flight_return": None,
        "hotel": None,
        "days": [],
        "flight_confirmed": False,
        "flight_return_confirmed": False,
        "hotel_confirmed": False,
    }

if "pending_message" not in st.session_state:
    st.session_state.pending_message = None

if "checked_spots" not in st.session_state:
    st.session_state.checked_spots = {}  # key: f"{date}_{idx}" -> bool


# ─────────────────────────────
# ユーティリティ
# ─────────────────────────────
def _v(value: object, style: str = "val") -> str:
    """None/空はプレースホルダー表示。style: 'val' | 'price' | 'price_hotel'"""
    if value is None or str(value).strip().lower() in ("none", "null", ""):
        return '<span class="pb-tbd">AIと相談して決定</span>'
    css = {"val": "pb-val", "price": "pb-val-price", "price_hotel": "pb-val-price-hotel"}.get(style, "pb-val")
    return f'<span class="{css}">{value}</span>'


def _is_empty(val) -> bool:
    """値が未設定かどうか判定する。"""
    return not val or str(val).strip().lower() in ("none", "null", "")


def _has_undecided(data: dict, fields: list) -> bool:
    """フィールドに1つでも未決定があれば True。"""
    return any(_is_empty(data.get(key)) for key, _ in fields)


def _get_consultation_message(plan_type: str, data: dict, fields: list) -> str:
    """決定済み・未決定フィールドを整理した動的な相談メッセージを生成する。"""
    decided = [(label, data.get(key)) for key, label in fields if not _is_empty(data.get(key))]
    undecided = [label for key, label in fields if _is_empty(data.get(key))]

    parts = []
    if decided:
        decided_str = "、".join(f"{label}「{val}」" for label, val in decided)
        parts.append(f"{decided_str}は決まっています")
    if undecided:
        undecided_str = "・".join(undecided)
        parts.append(f"{undecided_str}がまだ決まっていません")

    if len(parts) == 2:
        summary = f"{parts[0]}が、{parts[1]}"
    elif parts:
        summary = parts[0]
    else:
        return f"{plan_type}の内容についてもう少し詳しく相談したいです。"

    return f"{plan_type}について相談したいです。{summary}。おすすめを提案してください。"


def _format_airport(value: object) -> str:
    """
    空港名を "都市名 (CODE)" 形式に正規化する。
    例: "東京 (Narita International Airport, NRT)" → "東京 (NRT)"
    """
    if not value or str(value).strip().lower() in ("none", "null", ""):
        return "???"
    s = str(value).strip()
    # 日時文字列（数字4桁で始まる）が混入していたら弾く
    if re.match(r'^\d{4}', s):
        return "???"
    # "City/Name (..., NRT)" または "City/Name (NRT)" → "City (NRT)"
    m = re.match(r'^(.+?)\s*\(.*?([A-Z]{3})\)\s*$', s)
    if m:
        return f"{m.group(1).strip()} ({m.group(2)})"
    return s


# ─────────────────────────────
# プラン抽出・更新
# ─────────────────────────────
async def extract_plan_data(response_text: str) -> dict | None:
    """エージェント応答から旅行計画データを抽出する。"""
    client = AsyncOpenAI()
    extraction_prompt = f"""
以下のテキストから旅行計画データを抽出してください。

【nights 抽出ルール】
- 「一週間」「7日間」「7泊」「7泊8日」→ nights=7
- 「〇泊〇日」→ 〇泊の数値を nights に入れる
- 「5日間」→ nights=4（日数-1）
- 宿泊数が読み取れる表現があれば必ず数値で入れること

【days 抽出ルール】
- 「1日目」「Day 1」「初日」→ day_index=0
- 「2日目」「Day 2」→ day_index=1（以降同様）
- 日程プランが複数日にわたる場合は、すべての日のエントリをdaysに含めること
- 各日のactivitiesにはその日の観光スポット・レストラン・アクティビティ名を簡潔に入れる
- 「〇〇に行きたい」「〇〇を訪れたい」など単体で言及された場合は day_index=0 に入れる
- date・time が不明な場合は null にする

【is_user_selection ルール】
- ユーザーが特定の1つのフライト/ホテルを選択・確定した場合のみ true
- AIが候補を列挙しているだけの場合は false

テキスト:
{response_text}

【フライト抽出ルール】
- flight: 往路（行き）のフライト。出発地が日本・自国 → 目的地 の便
- flight_return: 復路（帰り）のフライト。目的地 → 日本・自国 の便
- 片道のみ言及されている場合は該当する方だけ埋め、もう一方は null のままにする

以下のJSON形式で返してください。該当データがないフィールドはnullにしてください:
{{
  "is_user_selection": false,
  "flight": {{
    "airline": null,
    "flight_number": null,
    "departure_airport": "出発地の都市名と空港コード（例: 東京 (NRT)）。日時は絶対に入れないこと",
    "arrival_airport": "到着地の都市名と空港コード（例: ホノルル (HNL)）。日時は絶対に入れないこと",
    "departure_time": "出発日時のみ（例: 2026-03-26 19:21）",
    "arrival_time": "到着日時のみ（例: 2026-03-27 01:05）",
    "seat_class": null,
    "price": null
  }},
  "flight_return": {{
    "airline": null,
    "flight_number": null,
    "departure_airport": "復路の出発地（例: ホノルル (HNL)）。日時は絶対に入れないこと",
    "arrival_airport": "復路の到着地（例: 東京 (NRT)）。日時は絶対に入れないこと",
    "departure_time": "復路の出発日時のみ（例: 2026-04-02 10:00）",
    "arrival_time": "復路の到着日時のみ（例: 2026-04-03 14:00）",
    "seat_class": null,
    "price": null
  }},
  "hotel": {{
    "name": null, "check_in": null, "check_out": null,
    "room_type": null, "price_per_night": null
  }},
  "destination": null,
  "nights": null,
  "days": [
    {{
      "date": null,
      "day_index": 0,
      "activities": [
        {{"time": null, "description": "スポット名"}}
      ]
    }},
    {{
      "date": null,
      "day_index": 1,
      "activities": [
        {{"time": null, "description": "スポット名"}}
      ]
    }}
  ]
}}

JSONのみを返してください。マークダウンのコードブロックは不要です。
フィールドの説明文字列は実際の値に置き換えてください。
daysに追加すべきスポットが1件もない場合のみ空配列 [] を返してください。
"""
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": extraction_prompt}],
        temperature=0,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None


def _merge_activities(day: dict, new_activities: list):
    """重複しないアクティビティのみ追加する。"""
    existing_descs = {a.get("description", "") for a in day.get("activities", [])}
    for act in new_activities:
        desc = act.get("description", "")
        if desc and desc not in existing_descs:
            day.setdefault("activities", []).append(act)
            existing_descs.add(desc)


def update_plan(extracted: dict):
    """None でないフィールドのみ部分更新。確定済みカードはスキップ。"""
    plan = st.session_state.plan
    def _merge_flight(plan_key: str, confirmed_key: str, data: dict):
        if not isinstance(data, dict):
            return
        if plan.get(confirmed_key):
            return
        if plan.get(plan_key):
            merged = {**plan[plan_key]}
            for k, v in data.items():
                if v is not None and str(v).strip().lower() not in ("none", "null", ""):
                    merged[k] = v
            plan[plan_key] = merged
        else:
            plan[plan_key] = data

    if extracted.get("flight"):
        _merge_flight("flight", "flight_confirmed", extracted["flight"])
    if extracted.get("flight_return"):
        _merge_flight("flight_return", "flight_return_confirmed", extracted["flight_return"])
    if extracted.get("hotel") and not plan.get("hotel_confirmed"):
        hotel_data = extracted["hotel"]
        if isinstance(hotel_data, dict):
            if plan.get("hotel"):  # 既存データがある場合はマージ（上書き防止）
                merged = {**plan["hotel"]}
                for k, v in hotel_data.items():
                    if v is not None and str(v).strip().lower() not in ("none", "null", ""):
                        merged[k] = v
                plan["hotel"] = merged
            else:  # 初回は直接代入（元の動作を維持）
                plan["hotel"] = hotel_data
    if extracted.get("destination"):
        plan["destination"] = extracted["destination"]
    if extracted.get("nights"):
        plan["nights"] = extracted["nights"]
    if extracted.get("days"):
        existing_dates = {d["date"]: i for i, d in enumerate(plan["days"]) if d.get("date")}
        for new_day in extracted["days"]:
            new_activities = new_day.get("activities", [])
            if not new_activities:
                continue
            if new_day.get("date") and new_day["date"] in existing_dates:
                # 日付が一致する既存 day にマージ
                idx = existing_dates[new_day["date"]]
                _merge_activities(plan["days"][idx], new_activities)
            else:
                # day_index で既存スロットへマージ、なければ新規追加
                day_idx = new_day.get("day_index", 0) or 0
                if day_idx < len(plan["days"]):
                    _merge_activities(plan["days"][day_idx], new_activities)
                else:
                    # スロットが足りない場合は空スロットを補完して追加
                    while len(plan["days"]) <= day_idx:
                        plan["days"].append({"date": None, "activities": []})
                    _merge_activities(plan["days"][day_idx], new_activities)
                    if new_day.get("date"):
                        plan["days"][day_idx]["date"] = new_day["date"]
        for i, day in enumerate(sorted(plan["days"], key=lambda x: x.get("date") or "")):
            day["label"] = f"Day {i + 1}"


# ─────────────────────────────
# Plan Board (Sidebar)
# ─────────────────────────────
def render_plan_board():
    plan = st.session_state.plan
    has_any = plan["flight"] or plan["flight_return"] or plan["hotel"] or plan["days"] or plan.get("nights")

    st.html('<div class="pb-title">🗺️ Plan Board</div><div class="pb-sub">honeymoon travel plan</div>')

    if not has_any:
        st.html("""
        <div class="pb-empty">
            <div class="pb-empty-icon">💌</div>
            <div class="pb-empty-text">
                chat to build<br>your plan here
            </div>
        </div>
        """)
        return

    # 目的地
    if plan["destination"] or plan["nights"]:
        dest = plan["destination"] or "TBD"
        nights = f"{plan['nights']}泊" if plan["nights"] else "TBD"
        st.html(f'<div class="pb-dest">{dest}<span class="pb-badge">{nights}</span></div>')

    # ─── Flight カード（共通描画関数） ───
    _FLIGHT_FIELDS = [
        ("departure_airport", "出発地"),
        ("arrival_airport", "到着地"),
        ("airline", "航空会社"),
        ("flight_number", "便名"),
        ("departure_time", "出発日時"),
        ("arrival_time", "到着日時"),
        ("seat_class", "座席クラス"),
        ("price", "料金"),
    ]

    def _render_flight_card(flight_data: dict, confirmed_key: str, label: str, btn_prefix: str):
        is_confirmed = plan.get(confirmed_key, False)
        dep = _format_airport(flight_data.get("departure_airport") or flight_data.get("departure"))
        arr = _format_airport(flight_data.get("arrival_airport") or flight_data.get("arrival"))
        confirmed_badge = '<span class="pb-confirmed-badge">✓ 確定済み</span>' if is_confirmed else ""
        card_class = "pb-card pb-card-confirmed" if is_confirmed else "pb-card"
        st.html(f"""
        <div class="{card_class}">
            <div class="pb-card-label">✈ {label}</div>
            {confirmed_badge}
            <div class="pb-route">{dep} → {arr}</div>
            <div class="pb-row"><span class="pb-key">airline</span>{_v(flight_data.get('airline'))}</div>
            <div class="pb-row"><span class="pb-key">flight no.</span>{_v(flight_data.get('flight_number'))}</div>
            <div class="pb-row"><span class="pb-key">depart</span>{_v(flight_data.get('departure_time'))}</div>
            <div class="pb-row"><span class="pb-key">arrive</span>{_v(flight_data.get('arrival_time'))}</div>
            <div class="pb-row"><span class="pb-key">class</span>{_v(flight_data.get('seat_class'))}</div>
            <div class="pb-row"><span class="pb-key">price</span>{_v(flight_data.get('price'), 'price')}</div>
        </div>
        """)
        has_undecided = _has_undecided(flight_data, _FLIGHT_FIELDS)
        b1, b2 = st.columns(2)
        if is_confirmed:
            with b1:
                st.link_button("🔗 予約する", "https://www.google.com/flights", use_container_width=True)
            with b2:
                if st.button("💬 AIに相談依頼", key=f"{btn_prefix}_change_btn", use_container_width=True):
                    plan[confirmed_key] = False
                    st.session_state.pending_message = _get_consultation_message(label, flight_data, _FLIGHT_FIELDS)
                    st.rerun()
        else:
            with b1:
                if st.button(
                    "✅ この内容で確定",
                    key=f"{btn_prefix}_confirm_btn",
                    type="primary",
                    disabled=has_undecided,
                    use_container_width=True,
                ):
                    plan[confirmed_key] = True
                    st.rerun()
            with b2:
                if st.button("💬 AIに相談依頼", key=f"{btn_prefix}_ai_btn", use_container_width=True):
                    st.session_state.pending_message = _get_consultation_message(label, flight_data, _FLIGHT_FIELDS)
                    st.rerun()

    if plan["flight"]:
        _render_flight_card(plan["flight"], "flight_confirmed", "flight (outbound)", "flight_out")
    if plan["flight_return"]:
        _render_flight_card(plan["flight_return"], "flight_return_confirmed", "flight (return)", "flight_ret")

    # ─── Hotel カード ───
    _HOTEL_FIELDS = [
        ("name", "ホテル名"),
        ("check_in", "チェックイン日"),
        ("check_out", "チェックアウト日"),
        ("room_type", "部屋タイプ"),
    ]
    if plan["hotel"]:
        h = plan["hotel"]
        is_hotel_confirmed = plan.get("hotel_confirmed", False)
        name = h.get("name") or "AIと相談して決定"
        confirmed_badge = '<span class="pb-confirmed-badge">✓ 確定済み</span>' if is_hotel_confirmed else ""
        card_class = "pb-card pb-card-hotel pb-card-confirmed" if is_hotel_confirmed else "pb-card pb-card-hotel"
        st.html(f"""
        <div class="{card_class}">
            <div class="pb-card-label">🏨 hotel</div>
            {confirmed_badge}
            <div class="pb-hotel-name">{name}</div>
            <div class="pb-row"><span class="pb-key">check-in</span>{_v(h.get('check_in'))}</div>
            <div class="pb-row"><span class="pb-key">check-out</span>{_v(h.get('check_out'))}</div>
            <div class="pb-row"><span class="pb-key">room type</span>{_v(h.get('room_type'))}</div>
        </div>
        """)
        hotel_has_undecided = _has_undecided(h, _HOTEL_FIELDS)
        b1, b2 = st.columns(2)
        if is_hotel_confirmed:
            with b1:
                st.link_button("🔗 予約する", "https://www.booking.com", use_container_width=True)
            with b2:
                if st.button("💬 AIに相談依頼", key="hotel_change_btn", use_container_width=True):
                    plan["hotel_confirmed"] = False
                    st.session_state.pending_message = _get_consultation_message("ホテル", h, _HOTEL_FIELDS)
                    st.rerun()
        else:
            with b1:
                if st.button(
                    "✅ この内容で確定",
                    key="hotel_confirm_btn",
                    type="primary",
                    disabled=hotel_has_undecided,
                    use_container_width=True,
                ):
                    plan["hotel_confirmed"] = True
                    st.rerun()
            with b2:
                if st.button("💬 AIに相談依頼", key="hotel_ai_btn", use_container_width=True):
                    st.session_state.pending_message = _get_consultation_message("ホテル", h, _HOTEL_FIELDS)
                    st.rerun()

    # ─── Schedule ───
    nights = plan.get("nights")
    days_data = plan.get("days", [])
    if nights or days_data:
        from datetime import datetime, timedelta
        st.html('<div class="pb-card-label" style="margin-bottom:8px;">📅 schedule</div>')

        # 日付 → day データのマップ（day_index フィールドも考慮）
        days_by_date = {d.get("date"): d for d in days_data if d.get("date")}
        days_by_index = {}
        for pos, d in enumerate(days_data):
            idx = d.get("day_index")
            days_by_index[pos if idx is None else idx] = d

        # チェックイン日から日付を計算
        hotel = plan.get("hotel") or {}
        check_in_str = hotel.get("check_in")

        # 表示する日数（nights + 1日）
        try:
            num_days = int(nights) + 1 if nights else len(days_data)
        except (ValueError, TypeError):
            num_days = len(days_data)

        for i in range(num_days):
            day_date = ""
            if check_in_str:
                try:
                    day_date = (datetime.strptime(check_in_str, "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
                except Exception:
                    pass

            label = f"Day {i + 1}"
            day_data = days_by_date.get(day_date) or days_by_index.get(i)
            activities = day_data.get("activities", []) if day_data else []

            title = label + (f" — {day_date}" if day_date else "")
            with st.expander(title, expanded=bool(activities)):
                if activities:
                    for act_idx, act in enumerate(activities):
                        spot_key = f"{day_date or i}_{act_idx}"
                        is_done = st.session_state.checked_spots.get(spot_key, False)
                        time_str = act.get("time") or ""
                        desc = act.get("description", "")
                        label_text = f"{time_str}　{desc}" if time_str else desc
                        checked = st.checkbox(
                            label_text,
                            value=is_done,
                            key=f"cb_{spot_key}",
                        )
                        st.session_state.checked_spots[spot_key] = checked
                else:
                    st.html('<span class="pb-tbd">AIと相談して決定</span>')


# ─────────────────────────────
# エージェント実行
# ─────────────────────────────
async def _stream_agent(router, input_messages: list, chat_placeholder) -> tuple[str, list]:
    """ストリーミング実行の共通ロジック。ツール呼び出しを toast で通知。"""
    response_text = ""
    with trace("新婚旅行プランナー"):
        stream = Runner.run_streamed(router, input_messages)

        async for event in stream.stream_events():
            if event.type != "raw_response_event":
                continue

            if isinstance(event.data, ResponseTextDeltaEvent):
                response_text += event.data.delta or ""
                chat_placeholder.markdown(response_text + "▌")

            elif (
                isinstance(event.data, ResponseOutputItemDoneEvent)
                and isinstance(event.data.item, ResponseFunctionToolCall)
            ):
                tool_name = getattr(event.data.item, "name", "unknown")
                raw_args = getattr(event.data.item, "arguments", "{}")
                try:
                    args_dict = json.loads(raw_args)
                    args_str = ", ".join(f"{k}: {v}" for k, v in args_dict.items())
                except Exception:
                    args_str = raw_args
                st.toast(f"🔧 Tool Calling: `{tool_name}`\n{args_str}", icon="🔧")

    chat_placeholder.markdown(response_text)
    return response_text, stream.to_input_list()


async def run_agent(sdk_history: list, user_input: str, chat_placeholder) -> tuple[str, list]:
    """ストリーミング実行。Playwright MCP 起動失敗時はフォールバック。"""
    input_messages = sdk_history + [{"role": "user", "content": user_input}]

    async with create_flight_mcp_server() as flight_mcp_server:
        flight_agent_with_mcp = flight_agent.clone(mcp_servers=[flight_mcp_server])

        # Playwright MCP は別途起動し、失敗時はフォールバック
        try:
            async with create_playwright_mcp_server() as playwright_mcp_server:
                schedule_agent_with_mcp = schedule_agent.clone(mcp_servers=[playwright_mcp_server])
                router = router_agent.clone(
                    handoffs=[flight_agent_with_mcp, hotel_agent, schedule_agent_with_mcp]
                )
                return await _stream_agent(router, input_messages, chat_placeholder)
        except Exception:
            # Playwright MCP 起動失敗時はスケジュールエージェントを MCP なしで動かす
            router = router_agent.clone(
                handoffs=[flight_agent_with_mcp, hotel_agent, schedule_agent]
            )
            return await _stream_agent(router, input_messages, chat_placeholder)


def process_chat(user_input: str):
    """チャットメッセージを処理してUIを更新する。"""
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user", avatar="💑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="💍"):
        placeholder = st.empty()
        try:
            response, new_history = asyncio.get_event_loop().run_until_complete(
                run_agent(st.session_state.sdk_history, user_input, placeholder)
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.sdk_history = new_history

            extracted = asyncio.get_event_loop().run_until_complete(
                extract_plan_data(response)
            )
            if extracted:
                update_plan(extracted)

        except InputGuardrailTripwireTriggered:
            error_message = (
                "申し訳ありません。🙏\n\n"
                "このサービスは**新婚旅行・ハネムーン**に関するご質問専用です。\n"
                "フライト、ホテル、旅行スケジュール、目的地についてお気軽にお聞きください！"
            )
            placeholder.warning(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})

        except Exception as error:
            placeholder.error(f"エラーが発生しました：{str(error)}")


# ─────────────────────────────
# レイアウト
# ─────────────────────────────

# ── サイドバー — Plan Board（常に固定） ──
with st.sidebar:
    render_plan_board()

# ── メイン — チャット ──
st.markdown("""
<div class="chat-header">
    <div class="chat-header-eyebrow">✦ honeymoon planner ✦</div>
    <div class="chat-header-title">新婚旅行プランナー</div>
    <div class="chat-header-sub">ハネムーンの夢を叶えるAIアシスタント</div>
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    avatar = "💍" if msg["role"] == "assistant" else "💑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# pending_message の自動実行
if st.session_state.pending_message:
    pending = st.session_state.pending_message
    st.session_state.pending_message = None
    process_chat(pending)
    st.rerun()

if user_input := st.chat_input("新婚旅行について質問してください..."):
    process_chat(user_input)
    st.rerun()
