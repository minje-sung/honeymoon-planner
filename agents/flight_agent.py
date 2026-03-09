from datetime import date

from agents import Agent
from prompts.system_prompts import FLIGHT_PROMPT
from tools.search_tool import web_search_tool, get_destination_info

flight_agent = Agent(
    name="flight_agent",
    instructions=FLIGHT_PROMPT.format(today=date.today().isoformat()),
    model="gpt-4o-mini",
    tools=[web_search_tool, get_destination_info],
)
