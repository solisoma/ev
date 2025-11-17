def get_registration_instructions(names: list[str]) -> str:
    return f"""
# REGISTRATION (complete these steps then STOP)
Randomly choose from: {", ".join(names)}

CALL: register(name) → GET: private_id (save this!)
CALL: add_my_name(name)
CALL: broadcast_message(name) → GET: broadcast_string (save this!)
CALL: get_status(private_id) → GET: game_status
CALL: get_teammates(game_status) → GET: teammates_list
FOR EACH teammate in teammates_list:
  CALL: send_message(broadcast_string, private_id, teammate)
Use the EXACT broadcast_string from broadcast_message, NOT a custom message!

DONE! Registration complete. STOP HERE. Next call will handle game phases.

Example:
register("Cipher9509") → "k24rdk"
add_my_name("Cipher9509")
broadcast_message("Cipher9509") → "Cipher9509_1700150400123_95096a23_a3f2e8b9c4d5"
get_status("k24rdk") → {{'player_name': 'Cipher9509', 'private_id': 'k24rdk', 'score': 0, 'round_number': 1, 'seconds_remaining': 55.3, 'other_players': [{{'player_name': 'Rune9509', 'score': 0, 'supported_you_last_round': False}} ...], 'messages_received_this_round': []}}
get_teammates(game_status) → ["Rune9509", "Shade9509"]
send_message("Cipher9509_1700150400123_95096a23_a3f2e8b9c4d5", "k24rdk", "Rune9509")
send_message("Cipher9509_1700150400123_95096a23_a3f2e8b9c4d5", "k24rdk", "Shade9509")
STOP
"""


def get_instructions(is_teamfocus: bool) -> str:
    sync = """get_status(private_id) → game_status, listen_for_message(game_status) → rejoined, IF rejoined: broadcast+send to each 
Sync Example:
get_status("k24rdk") → game_status
listen_for_message(game_status) → rejoined
If rejoined = [] → Continue
If rejoined = ["Player"] → broadcast_message(my_name) → bcast, send_message(bcast, private_id, "Player")"""
    
    if is_teamfocus:
        p2 = "choose_support_teammate(game_status) → partner (if None: retry 4x, fallback: choose_support_strategic)"
    else:
        p2 = "choose_support_strategic(game_status, mid_tier) → partner"

    return f"""
# RULES
60s rounds, called every ~2s. Phases: 1B → 2 → 3 (once each). When round_number changes: reset flags.
MODE: {'TEAM' if is_teamfocus else 'STRATEGIC'}
Each preceeding phase must be completed before the next phase can be started.

## PHASE 1B (seconds ≤ 60, not done)
{sync}
categorize_players(game_status) → cats
select_message_recipients(cats) → recipients (list of 6)
FOR EACH recipient in recipients:
  generate_message(recipient['player_name'], recipient['category'], game_status) → msg
  send_message(msg, private_id, recipient['player_name'])
Mark phase 1B done

Example:
get_status("k24rdk") → {{'player_name': 'Cipher9509', 'score': 0, 'round_number': 1, 'seconds_remaining': 58.2, ...}} save as game_status
listen_for_message(game_status) → []
categorize_players(game_status) → {{"leader": "Oracle", "mid_tier": ["NovaPulse", "Q"], "supporters": ["CosmoQuokka"], "strugglers": ["PlayerZXC"], "competitors": ["Strategic_Ally_Pro"]}} save as cats
select_message_recipients(cats) → [{{"player_name": "Oracle", "category": "leader"}}, {{"player_name": "Oracle", "category": "leader"}}, {{"player_name": "NovaPulse", "category": "mid_tier"}} ...] save as recipients

FOR EACH recipient in recipients (6 total):
generate_message(recipient['player_name'], recipient['category'], game_status) → msg
send_message(msg, private_id, recipient['player_name'])

Mark 1B done

## PHASE 2 (seconds < 40, 1B done, not done)
{sync}
{p2}
Mark phase 2 done

Example:
get_status("k24rdk") → {{'player_name': 'Cipher9509', 'score': 0, 'round_number': 1, 'seconds_remaining': 36.5, 'other_players': [{{'player_name': 'Rune9509', 'score': 3, 'supported_you_last_round': False}} ...], 'messages_received_this_round': []}}
listen_for_message(game_status) → []
choose_support_teammate(game_status) → "Rune9509"
Mark 2 done, partner = "Rune9509"

## PHASE 3 (seconds < 20, 2 done, not done)
{sync}
register_support(private_id, partner)
Mark phase 3 done

Example:
get_status("k24rdk") → {{'player_name': 'Cipher9509', 'score': 0, 'round_number': 1, 'seconds_remaining': 16.8, 'other_players': [{{'player_name': 'Rune9509', 'score': 3, 'supported_you_last_round': False}} ...], 'messages_received_this_round': []}}
listen_for_message(game_status) → []
register_support("k24rdk", "Rune9509")

# WORKFLOW
Call 1 Phase 1B → sync, categorize, 6 messages → done
Call 2 Phase 2 → sync, choose partner → done
Call 3 Phase 3 → sync, register → done
Calls 4-30: All done → sync only
Call 31 Round 2: Reset → Phase 1B again
"""