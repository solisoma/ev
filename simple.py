import sys
import ast
import asyncio
import traceback
from dotenv import load_dotenv
from instructs import get_instructions, get_registration_instructions
import os
from agents import Agent, Runner, SQLiteSession, set_trace_processors
from agents.mcp import MCPServerStreamableHttp, MCPServerStdio
from langsmith.wrappers import OpenAIAgentsTracingProcessor

load_dotenv(override=True)
MODEL = "gpt-4o-mini"
PARAMS = {"url": os.getenv("ALLIANCE_MCP_SERVER"), "timeout": 30}
# LOCAL_PARAMS = {"command": "uv", "args": ["run", "evaluator.py"], "timeout": 30}
TURN_PROMPT = "Check round. Execute next incomplete phase: Phase 1 (messages) OR Phase 2 (support at ≤20s). STOP after phase."

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
                instructions=get_instructions(), 
                model=MODEL, 
                mcp_servers=[mcp, local_mcp]
            )
            print(f"Running agent {agent_id} .....")
            await Runner.run(agent, get_registration_instructions(NAMES[int(agent_id) - 1]), session=session, max_turns=50)
            print("Registered")
            while True:
                print("=== TURN ===")
                try:
                    await Runner.run(agent, TURN_PROMPT, session=session, max_turns=50)
                except Exception as e:
                    print(f"Error in agent {agent_id}: {e}")
                    break
                finally:
                    await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        set_trace_processors([OpenAIAgentsTracingProcessor()])
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()