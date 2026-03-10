from agents import Agent
from prompts.system_prompts import SCHEDULE_PROMPT
from tools.search_tool import get_destination_info

schedule_agent = Agent(
    name="schedule_agent",
    instructions=SCHEDULE_PROMPT,
    model="gpt-4o-mini",
    tools=[get_destination_info],
)

