from agents import Agent
from prompts.system_prompts import HOTEL_PROMPT
from tools.search_tool import web_search_tool, get_destination_info

hotel_agent = Agent(
    name="hotel_agent",
    instructions=HOTEL_PROMPT,
    model="gpt-4o-mini",
    tools=[web_search_tool, get_destination_info],
)

