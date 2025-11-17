import asyncio
from dotenv import load_dotenv
from instructs import get_instructions, get_registration_instructions
import os
from agents import Agent, Runner, SQLiteSession, set_trace_processors
from agents.mcp import MCPServerStreamableHttp, MCPServerStdio
from langsmith.wrappers import OpenAIAgentsTracingProcessor

load_dotenv(override=True)
MODEL = "gpt-4o-mini"
PARAMS = {"url": os.getenv("ALLIANCE_MCP_SERVER"), "timeout": 30}
LOCAL_PARAMS = {"command": "uv", "args": ["run", "evaluator.py"], "timeout": 30}
TURN_PROMPT = "Execute protocol. Check round_number and seconds_remaining."


async def main():
    session = SQLiteSession("Simple")
    async with MCPServerStreamableHttp(params=PARAMS) as mcp:
        async with MCPServerStdio(params=LOCAL_PARAMS) as local_mcp:
            agent = Agent(
                name="Uburu", 
                instructions=get_instructions(is_teamfocus=False), 
                model=MODEL, 
                mcp_servers=[mcp, local_mcp]
            )
            await Runner.run(agent, get_registration_instructions(), session=session, max_turns=50)
            print("Registered")
            while True:
                print("=== TURN ===")
                await Runner.run(agent, TURN_PROMPT, session=session, max_turns=50)
                await asyncio.sleep(2)


if __name__ == "__main__":
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    asyncio.run(main())