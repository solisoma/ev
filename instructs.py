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
    if is_teamfocus:
        p2_step3 = "STEP 3: CALL choose_support_teammate(game_status) → save partner. If None: retry (max 4x). If still None: CALL choose_support_strategic(game_status, mid_tier) → save partner"
    else:
        p2_step3 = "STEP 3: CALL choose_support_strategic(game_status, mid_tier) → save partner"

    return f"""
# PHASE EXECUTION RULES
MODE: {'TEAM' if is_teamfocus else 'STRATEGIC'}
Execute phases in strict order: 1B → 2 → 3
Complete all incomplete phases in one call. Move through phases sequentially.

## EXECUTION FLOW
Check phase status and execute all incomplete phases:
IF Phase 1B not done: Execute PHASE 1B, mark done, continue to check Phase 2
IF Phase 2 not done: Execute PHASE 2, mark done, continue to check Phase 3
IF Phase 3 not done: Execute PHASE 3, mark done

## PHASE 1B - Execute these steps in order:

STEP 1: CALL get_status(private_id)
→ Save result as game_status

STEP 2: CALL listen_for_message(game_status)
→ Save result as rejoined
→ If rejoined not empty: CALL broadcast_message(my_name) → save as bcast, FOR EACH in rejoined: CALL send_message(bcast, private_id, player)

STEP 3: CALL categorize_players(game_status)
→ Save result as cats

STEP 4: CALL select_message_recipients(cats)
→ Pass cats from STEP 3
→ Save result as recipients

STEP 5: FOR EACH recipient in recipients:
→ CALL generate_message(recipient['player_name'], recipient['category'], game_status)
→ Save result as msg
→ CALL send_message(msg, private_id, recipient['player_name'])

STEP 6: Mark Phase 1B done, continue to Phase 2

Example:
STEP 1: get_status("k24rdk") → game_status = {{'player_name': 'Cipher9509', 'round_number': 1, 'seconds_remaining': 58.2, ...}}
STEP 2: listen_for_message(game_status) → rejoined = []
STEP 3: categorize_players(game_status) → cats = {{"leader": "Oracle", "mid_tier": ["NovaPulse", "Q"], ...}}
STEP 4: select_message_recipients(cats) → recipients = [6 items]
STEP 5: Loop 6 times:
  generate_message("Oracle", "leader", game_status) → msg
  send_message(msg, "k24rdk", "Oracle")
  ...continues for all 6...
STEP 6: Mark Phase 1B done

## PHASE 2 - Execute these steps in order:

STEP 1: CALL get_status(private_id)
→ Save result as game_status

STEP 2: CALL listen_for_message(game_status)
→ Save result as rejoined
→ If rejoined not empty: CALL broadcast_message(my_name) → save as bcast, FOR EACH in rejoined: CALL send_message(bcast, private_id, player)

{p2_step3}

STEP 4: Mark Phase 2 done, continue to Phase 3

Example:
STEP 1: get_status("k24rdk") → game_status = {{'round_number': 1, 'seconds_remaining': 36.5, ...}}
STEP 2: listen_for_message(game_status) → rejoined = []
STEP 3: choose_support_teammate(game_status) → partner = "Rune9509"
STEP 4: Mark Phase 2 done

## PHASE 3 - Execute these steps in order:

STEP 1: CALL get_status(private_id)
→ Save result as game_status

STEP 2: CALL listen_for_message(game_status)
→ Save result as rejoined
→ If rejoined not empty: CALL broadcast_message(my_name) → save as bcast, FOR EACH in rejoined: CALL send_message(bcast, private_id, player)

STEP 3: CALL register_support(private_id, partner)
→ Use partner saved from Phase 2

STEP 4: Mark Phase 3 done

Example:
STEP 1: get_status("k24rdk") → game_status = {{'round_number': 1, 'seconds_remaining': 16.8, ...}}
STEP 2: listen_for_message(game_status) → rejoined = []
STEP 3: register_support("k24rdk", "Rune9509")
STEP 4: Mark Phase 3 done
"""