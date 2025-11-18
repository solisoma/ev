import sys
import ast
import asyncio
from dotenv import load_dotenv
from instructs import GameOrchestrator
import os
from agents import Agent, SQLiteSession, set_trace_processors
from agents.mcp import MCPServerStreamableHttp, MCPServerStdio
from langsmith.wrappers import OpenAIAgentsTracingProcessor

load_dotenv(override=True)
MODEL = "gpt-4o-mini"
PARAMS = {"url": os.getenv("ALLIANCE_MCP_SERVER"), "timeout": 30}

with open("names.txt", "r") as f:
    NAMES = ast.literal_eval(f.read())

async def main():
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    session = SQLiteSession(f"Uburu_{agent_id}")
    local_param = {
        "command": "uv",
        "args": ["run", "evaluator.py"],
        "timeout": 30
    }
    async with MCPServerStreamableHttp(params=PARAMS) as mcp:
        async with MCPServerStdio(params=local_param) as local_mcp:
            agent = Agent(
                name=f"Uburu_{agent_id}",
                model=MODEL, 
                mcp_servers=[mcp, local_mcp]
            )

            orchestrator = GameOrchestrator(agent, session)
    
            await orchestrator.register(NAMES[int(agent_id) - 1])
            
            while True:
                await orchestrator.run_turn()
                await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        set_trace_processors([OpenAIAgentsTracingProcessor()])
        asyncio.run(main())
    except Exception as e:
        print(f"Error in agent: {e}")