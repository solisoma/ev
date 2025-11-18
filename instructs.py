import json
from agents import Runner

class GameOrchestrator:
    def __init__(self, agent, session):
        self.agent = agent
        self.session = session
        self.current_round = -1
        self.phase1_done = False
        self.phase2_done = False
        
    async def register(self, names: list[str]):
        """Simple registration"""
        prompt = f"Randomly select a name from {", ".join(names)} and call register with the selected name"
        await Runner.run(self.agent, prompt, session=self.session, max_turns=5)
        print("Registered successfully")
        
    async def execute_phase1(self, game_status: dict):
        """Send all messages"""
        prompt = f"""
    Execute these steps in order:
    here is the game status: {game_status}, dont remove any fields when passing it to the functions
    STEP 1: prepare_message(game_status) → save as messages_to_send
    STEP 2: for each player in messages_to_send, call send_message(player['player_name'], player['message'])
    Stop when done.

    if all steps were executed successfully, return true, otherwise return false
    """
        r = await Runner.run(self.agent, prompt, session=self.session, max_turns=20)
        print(f"Phase 1 result: {r.final_output}")
        self.phase1_done = r.final_output == "true"
        
    async def execute_phase2(self, game_status: dict):
        """Register support"""
        prompt = f"""
    Execute these steps in order:
    here is the game status: {game_status}, dont remove any fields when passing it to the functions
    STEP 1: choose_support_strategic(game_status) → save as partner
    STEP 2: register_support(game_status['private_id'], partner)
    Stop when done.

    if all steps were executed successfully, return true, otherwise return false
    """
        r = await Runner.run(self.agent, prompt, session=self.session, max_turns=10)
        print(f"Phase 2 result: {r.final_output}")
        self.phase2_done = r.final_output == "true"
        
    async def run_turn(self):
        """Main game loop - Python decides what to do"""
        # Get game status
        print("=== Turn ===")
        prompt = """Call get_status(private_id).
    Return ONLY the exact JSON dictionary returned by get_status. Nothing else.
    Format:
    {"player_name": "...", "private_id": "...", "score": ..., "round_number": ..., "seconds_remaining": ..., "other_players": [...], "messages_received_this_round": [...]}
    Do NOT add:
    - No explanations
    - No "Here is the result:"
    - No "The status is:"
    - Just the raw JSON dictionary"""

        result = await Runner.run(self.agent, prompt, session=self.session, max_turns=3)
        result_str = result.final_output
        if '```' in result_str:
            start = result_str.find('{')
            end = result_str.rfind('}') + 1
            result_str = result_str[start:end]
        game_status = json.loads(result_str)
        round_num = game_status['round_number']
        seconds = game_status['seconds_remaining']

        print(f"Round number: {round_num} Seconds remaining: {seconds} messages received this round: {game_status['messages_received_this_round']}")
        # Check if new round
        if round_num != self.current_round:
            self.current_round = round_num
            self.phase1_done = False
            self.phase2_done = False
            
        if not self.phase1_done:
            print("Executing Phase 1...")
            await self.execute_phase1(game_status)
            
        elif not self.phase2_done and seconds <= 20:
            print("Executing Phase 2...")
            await self.execute_phase2(game_status)
            
        else:
            print("Waiting...")