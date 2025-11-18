import asyncio
from dotenv import load_dotenv
from instructs import GameOrchestrator
import os
from agents import Agent, SQLiteSession, set_trace_processors
from agents.mcp import MCPServerStreamableHttp
from langsmith.wrappers import OpenAIAgentsTracingProcessor

load_dotenv(override=True)
MODEL = "gpt-4o-mini"
PARAMS = {"url": os.getenv("ALLIANCE_MCP_SERVER"), "timeout": 30}
PLAY_NAME = "Vorx"

async def main():
    session = SQLiteSession(f"{PLAY_NAME}")
    async with MCPServerStreamableHttp(params=PARAMS) as mcp:
        agent = Agent(
            name="Uburu",
            model=MODEL, 
            mcp_servers=[mcp]
        )

        orchestrator = GameOrchestrator(agent, session)

        await orchestrator.register(PLAY_NAME)
        
        while True:
            await orchestrator.run_turn()
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        set_trace_processors([OpenAIAgentsTracingProcessor()])
        asyncio.run(main())
    except Exception as e:
        print(f"Error in agent: {e}")