from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

from my_agents.flight_agent import flight_agent
from my_agents.hotel_agent import hotel_agent
from my_agents.schedule_agent import schedule_agent
from prompts.system_prompts import GUARDRAIL_PROMPT, ROUTER_PROMPT

# 新婚旅行関連チェック用エージェント
guardrail_agent = Agent(
    name="guardrail_agent",
    instructions=GUARDRAIL_PROMPT,
    model="gpt-4o-mini",
)


@input_guardrail
async def honeymoon_guardrail(
    context: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """新婚旅行に無関係な質問をブロックするガードレール"""
    user_input = input if isinstance(input, str) else str(input)

    result = await Runner.run(
        guardrail_agent,
        user_input,
        context=context.context,
    )

    result_text = result.final_output.strip()
    is_irrelevant = "関連なし" in result_text

    return GuardrailFunctionOutput(
        output_info=result_text,
        tripwire_triggered=is_irrelevant,
    )


# ルーターエージェント
router_agent = Agent(
    name="honeymoon_planner",
    instructions=ROUTER_PROMPT,
    model="gpt-4o-mini",
    input_guardrails=[honeymoon_guardrail],
    handoffs=[flight_agent, hotel_agent, schedule_agent],
)
