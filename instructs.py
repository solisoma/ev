def get_registration_instructions() -> str:
    return """
ALLIANCE GAME - REGISTRATION PROTOCOL

Execute these TOOL CALLS IN EXACT ORDER:

STEP 1: Register with game server
1. Choose a random player name
2. TOOL CALL: register(player_name) - save the returned private_id
3. TOOL CALL: add_my_name(player_name) - dont skip this tool call
4. TOOL CALL: broadcast_message(player_name) - save the broadcast string
5. TOOL CALL: get_status() - save as game_status
6. FOR EACH player in game_status['other_players']:
   TOOL CALL: send_message(broadcast, private_id, player['player_name'])

Execute ALL tool calls sequentially. Registration complete after all players messaged.
"""


def get_instructions(is_teamfocus: bool) -> str:
    if is_teamfocus:
        phase2_instructions = """
PHASE 2: CHOOSE SUPPORT (TEAM-FIRST)
Condition: seconds_remaining < 40 AND Phase 1B complete AND Phase 2 not complete.

SYNC FIRST (Execute these tool calls before Phase 2 logic):
1. TOOL CALL: get_status() - save as game_status
2. TOOL CALL: listen_for_message(game_status) - save as rejoined
3. If rejoined not empty:
   TOOL CALL: broadcast_message(my_name) - save as broadcast
   FOR EACH in rejoined: TOOL CALL: send_message(broadcast, private_id, player)

AFTER SYNC COMPLETE, execute Phase 2:
1. TOOL CALL: choose_support_teammate(game_status)
2. If a name is returned: save partner, mark Phase 2 complete, stop
3. If None: retry on next call (max 4 retries)
4. After 4 failures: TOOL CALL: choose_support_strategic(game_status, mid_tier), save partner, mark complete, stop
"""
    else:
        phase2_instructions = """
PHASE 2: CHOOSE SUPPORT (STRATEGIC)
Condition: seconds_remaining < 40 AND Phase 1B complete AND Phase 2 not complete.

SYNC FIRST (Execute these tool calls before Phase 2 logic):
1. TOOL CALL: get_status() - save as game_status
2. TOOL CALL: listen_for_message(game_status) - save as rejoined
3. If rejoined not empty:
   TOOL CALL: broadcast_message(my_name) - save as broadcast
   FOR EACH in rejoined: TOOL CALL: send_message(broadcast, private_id, player)

AFTER SYNC COMPLETE, execute Phase 2:
1. TOOL CALL: choose_support_strategic(game_status, mid_tier)
2. Save partner, mark Phase 2 complete, stop
"""

    return f"""
ALLIANCE GAME AGENT — STRICT SEQUENTIAL EXECUTION
Rounds last 60 seconds.

Registration executes ONLY if you have no player_name and private_id.
If you have player_name and private_id, skip registration and go to phases.

MODE: {'TEAM-FIRST' if is_teamfocus else 'STRATEGIC'}

====================================================
PHASE 1B — MESSAGE SENDING
====================================================
Condition: Phase 1B not complete AND seconds_remaining <= 60

SYNC FIRST (Execute these tool calls before Phase 1B logic):
1. TOOL CALL: get_status() - save as game_status
2. TOOL CALL: listen_for_message(game_status) - save as rejoined
3. If rejoined not empty:
   TOOL CALL: broadcast_message(my_name) - save as broadcast
   FOR EACH in rejoined: TOOL CALL: send_message(broadcast, private_id, player)

AFTER SYNC COMPLETE, execute Phase 1B:

Messaging Rules (MAX 6 messages per round):
- Leader: 2 messages first
- Remaining 4 messages in priority order: mid_tier, supporters, strugglers, competitors

Tool calls in order:
1. TOOL CALL: categorize_players(game_status) - save as categories
2. TOOL CALL: generate_message(categories['leader'], 'leader', game_status) - save as msg
3. TOOL CALL: send_message(msg, private_id, categories['leader'])
4. TOOL CALL: send_message(msg, private_id, categories['leader']) - second message to leader
5. FOR up to 4 more players (priority order):
   TOOL CALL: generate_message(player, category, game_status) - save as msg
   TOOL CALL: send_message(msg, private_id, player)
6. When 6 messages sent: mark Phase 1B complete

====================================================
{phase2_instructions}
====================================================

PHASE 3 — REGISTER SUPPORT
====================================================
Condition: seconds_remaining < 20 AND Phase 2 complete AND Phase 3 not complete

SYNC FIRST (Execute these tool calls before Phase 3 logic):
1. TOOL CALL: get_status() - save as game_status
2. TOOL CALL: listen_for_message(game_status) - save as rejoined
3. If rejoined not empty:
   TOOL CALL: broadcast_message(my_name) - save as broadcast
   FOR EACH in rejoined: TOOL CALL: send_message(broadcast, private_id, player)

AFTER SYNC COMPLETE, execute Phase 3:
1. If partner exists: TOOL CALL: register_support(private_id, partner)
2. Mark Phase 3 complete

====================================================
ROUND TRACKING
====================================================
- Track round_number from get_status()
- When round_number changes: reset Phase 1B/2/3 flags, retry counters, message counts
- Never execute same phase twice in one round
- Always follow order: Registration (once) then Phase 1B then Phase 2 then Phase 3

====================================================
STRICT RULES
====================================================
- Execute SYNC (get_status + listen_for_message) before EACH phase
- Call tools in the EXACT order shown
- NEVER skip a tool call in a sequence
- NEVER reorder tool calls
- NEVER exceed 6 messages in Phase 1B
- Save tool results and use them in subsequent calls
"""