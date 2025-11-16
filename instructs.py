def get_instructions(is_teamfocus: bool) -> str:
    if is_teamfocus:
        # Team mode: Try teammates first, fallback to strategic after 4 fails
        phase2_instructions = """
PHASE 2: CHOOSE SUPPORT (TEAM-FIRST)
When: seconds_remaining < 40 AND Phase 1B done AND Phase 2 not done
───────────────────────────────────────────────────────────────
TEAM-FIRST MODE: Prefer teammates, fallback to strategic if needed.

1. Call choose_support_teammate(game_status)
2. IF returns a name: Save as partner, mark Phase 2 complete
3. IF returns None: Retry on next call (max 4 attempts)
4. After 4 failed teammate attempts:
   - Fallback: choose_support_strategic(game_status, mid_tier)
   - Save as partner, mark Phase 2 complete

Always register someone. Teammates preferred, strategic fallback available."""
    
    else:
        # Strategic mode: Use strategic selection directly
        phase2_instructions = """
PHASE 2: CHOOSE SUPPORT (STRATEGIC)
When: seconds_remaining < 40 AND Phase 1B done AND Phase 2 not done
───────────────────────────────────────────────────────────────
STRATEGIC MODE: Use game theory to select best support target.

1. Call choose_support_strategic(game_status, mid_tier)
   - This analyzes all players and picks optimal target
   - May return teammate or non-teammate based on strategy
2. Save as partner, mark Phase 2 complete

Pure strategic selection based on reciprocity and game state."""

    return f"""
ALLIANCE GAME - 60 second rounds, multiple calls per round

MODE: {'TEAM-FIRST' if is_teamfocus else 'STRATEGIC'}

═══════════════════════════════════════════════════════════════
REGISTRATION (First call ever):
═══════════════════════════════════════════════════════════════
1. Come up with a random player name and register as that player name should come from random.choice(A-Z)
2. Call add_my_name(your_player_name)
3. Call broadcast_message(your_player_name) → save broadcast string
4. Get all players from game_status['other_players']
5. FOR EACH player in other_players:
   - Call send_message(broadcast_string, private_id, player_name)

═══════════════════════════════════════════════════════════════
EVERY CALL:
═══════════════════════════════════════════════════════════════

STEP 1: SYNC TEAM STATE (Execute EVERY call)
───────────────────────────────────────────────────────────────
A) get_status() → save as game_status
B) listen_for_message(game_status) → returns rejoined_players list
C) IF rejoined_players not empty:
   - broadcast = broadcast_message(my_name)
   - FOR EACH in rejoined_players: send_message(broadcast, private_id, player)

───────────────────────────────────────────────────────────────

STEP 2: EXECUTE PHASES (Once per round each)
───────────────────────────────────────────────────────────────

PHASE 1B: SEND MESSAGES
When: seconds_remaining <= 60 AND Phase 1B not done this round
───────────────────────────────────────────────────────────────
1. categories = categorize_players(game_status)
2. Leader (2 messages):
   - msg = generate_message(leader, 'leader', game_status)
   - send_message(msg, private_id, leader) twice
3. ALL supporters (1 each):
   - FOR EACH: generate_message + send_message
4. ALL mid_tier (1 each):
   - FOR EACH: generate_message + send_message
5. ALL strugglers (1 each):
   - FOR EACH: generate_message + send_message
6. ALL competitors (1 each):
   - FOR EACH: generate_message + send_message
7. Mark Phase 1B complete

───────────────────────────────────────────────────────────────

{phase2_instructions}

───────────────────────────────────────────────────────────────

PHASE 3: REGISTER SUPPORT
When: seconds_remaining < 20 AND Phase 2 done AND Phase 3 not done
───────────────────────────────────────────────────────────────
1. IF partner exists: register_support(private_id, partner)
2. Mark Phase 3 complete

Track round_number. New round = reset all phase flags.
"""