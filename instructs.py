import json
import ast
from evaluator import choose_support_strategic, prepare_message
from agents import Runner

class GameOrchestrator:
    def __init__(self, agent, session):
        self.agent = agent
        self.session = session
        self.current_round = 0
        self.phase1_done = False
        self.phase2_done = False
        
    async def register(self, name: str):
        """Simple registration"""
        prompt = f"Register with the selected name: {name}"
        await Runner.run(self.agent, prompt, session=self.session, max_turns=5)
        print("Registered successfully")
        
    async def execute_phase1(self, game_status: dict):
        """Send all messages"""
        messages = prepare_message(status=game_status)
        f_result = "true"
        for message in messages:
            prompt = f"here is the message {message}, call send_message(message['player_name'], message['message']) Stop when done. if executed successfully, return true, otherwise return false"
            r = await Runner.run(self.agent, prompt, session=self.session, max_turns=20)
            print(f"Phase 1 result: {r.final_output}")
            if r.final_output != "true":
                f_result = "false"
                break
        self.phase1_done = f_result == "true"
        
    async def execute_phase2(self, game_status: dict):
        """Register support"""
        partner = choose_support_strategic(status=game_status)
        prompt = f"""here is the partner {partner}, register_support(private_id, partner)
        Stop when done.
        if all steps were executed successfully, return true, otherwise return false
        """
        r = await Runner.run(self.agent, prompt, session=self.session, max_turns=10)
        print(f"Phase 2 result: {r.final_output}")
        self.phase2_done = r.final_output == "true"

    async def catch_tool_call(self, tool_name: str):
        """Get current game state - FAST VERSION"""
        # Simple prompt - just call the tool
        prompt = "Call get_status(private_id)"
        
        # Execute with max_turns=1 (only need one call)
        stream = Runner.run_streamed(self.agent, prompt, session=self.session, max_turns=3)
        last_called_tool = None
        result = {}
        
        async for event in stream.stream_events():
            if event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        last_called_tool = event.item.raw_item.name
                    elif event.item.type == "tool_call_output_item":
                        if last_called_tool == tool_name:
                            result = ast.literal_eval(json.loads(event.item.output)["text"])
                            break

        
        return result
        
    async def run_turn(self):
        """Main game loop - Python decides what to do"""
        # Get game status
        print("=== Turn ===")

        game_status = await self.catch_tool_call("get_status")
        round_num = game_status['round_number']
        seconds = game_status['seconds_remaining']

        print(f"Round number: {round_num} Seconds remaining: {seconds} messages received this round: {game_status['messages_received_this_round']}")
        # Check if new round
        if round_num != self.current_round:
            self.current_round = round_num
            self.phase1_done = False
            self.phase2_done = False
            
        if not self.phase1_done and self.current_round != 0:
            print("Executing Phase 1...")
            await self.execute_phase1(game_status)
            
        elif not self.phase2_done and seconds <= 20 and self.current_round != 0:
            print("Executing Phase 2...")
            await self.execute_phase2(game_status)
            
        else:
            print("Waiting...")