import asyncio
from dotenv import load_dotenv
import os
from agents import Agent, Runner, SQLiteSession, set_trace_processors
from agents.mcp import MCPServerStreamableHttp, MCPServerStdio
from langsmith.wrappers import OpenAIAgentsTracingProcessor

load_dotenv(override=True)
MODEL = "gpt-5-nano"
PARAMS = {"url": os.getenv("ALLIANCE_MCP_SERVER"), "timeout": 30}
LOCAL_PARAMS = {"command": "uv", "args": ["run", "evaluator.py"], "timeout": 30}
TEAMMATES = ["Player1", "Player2", "Player3"]
REGISTER = "Come up with a random player name and register as that player name should come from random.choice(A-N)"
TURN_PROMPT = """Execute round protocol (60 seconds available):
1. GET & FILTER (5s): Get status, filter messages
2. CATEGORIZE (5s): Get 5 player lists
3. MESSAGE ALL (30-40s): 
   - For EACH player: generate_message THEN send_message
   - Must actually SEND every message generated
   - Leader: send 2 messages
4. DECIDE SUPPORT (10-15s):
   - Get mid_tier list
   - Use choose_support_strategic 
   - Register support
   - Think carefully - this is your key decision
Use full time available. Quality over speed."""


def get_instructions(is_teamfocus: bool) -> str:
    instructions = """
Alliance Game Strategy:
TIME: Each round = 60 seconds. Execute steps IN ORDER - complete each fully before next.
=== SEQUENTIAL PROTOCOL (DO NOT SKIP AHEAD) ===
STEP 1: GET & FILTER (must complete first)
   - Use get_status to retrieve game state and your private_id
   - Check messages_received_this_round and REMOVE bad messages
   - WAIT: Do not proceed to step 2 until this is complete
STEP 2: CATEGORIZE (after step 1 is complete)
   - Use categorize_players to get 5 player lists
   - WAIT: Do not proceed to step 3 until you have all categories
STEP 3: MESSAGE ALL NON-TEAMMATES (after step 2 is complete)
   CRITICAL: You MUST complete ALL messaging before step 4! The max number of messages is 6.
   The priority is: leader, supporters, mid_tier, strugglers, competitors.
   For EACH player in supporters, mid_tier, strugglers, competitors:
   - Generate message for that player
   - Send message to that player
   - Repeat for NEXT player
   For leader: generate and send exactly 2 messages
   DO NOT proceed to step 4 until ALL messages are sent!
   You must finish messaging COMPLETELY before choosing support!
"""
    if is_teamfocus:
        instructions += f"""
STEP 4: SUPPORT TEAMMATE (after step 3 is complete)
   - Use choose_support to pick a teammate from {TEAMMATES}
   - The teammate name returned will be used as the player for register_support
   - Use register_support to register that teammate as your support
   - ONLY choose from {TEAMMATES}, never non-teammates
"""
        return instructions
    else:
        instructions += """
STEP 4: DECIDE SUPPORT (after step 3 is complete)
   - Use choose_support_strategic
   - Use register_support
   This is the FINAL step. Do this LAST.
KEY RULE: Complete each step FULLY before starting the next step.
          DO NOT choose support while still sending messages!
"""
    return instructions


async def main():
    session = SQLiteSession("Simple")
    async with MCPServerStreamableHttp(params=PARAMS) as mcp:
        async with MCPServerStdio(params=LOCAL_PARAMS) as local_mcp:
            agent = Agent(name="Uburu", instructions=get_instructions(is_teamfocus=False), model=MODEL, mcp_servers=[mcp, local_mcp])
            await Runner.run(agent, REGISTER, session=session, max_turns=50)
            print("Registered")
            while True:
                print("=== TURN ===")
                await Runner.run(agent, TURN_PROMPT, session=session, max_turns=50)
                await asyncio.sleep(2)


if __name__ == "__main__":
    set_trace_processors([OpenAIAgentsTracingProcessor()])
    asyncio.run(main())
