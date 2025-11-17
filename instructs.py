def get_registration_instructions(names: list[str]) -> str:
    return f"""
# REGISTRATION (complete these steps then STOP)
Randomly choose from: {", ".join(names)}

CALL: register(name) → GET: private_id (save this!)

DONE! Registration complete. STOP HERE. Next call will handle game phases.

Example:
register("Cipher9509") → "k24rdk"
STOP
"""

def get_instructions() -> str:
    return """
# PHASE-BASED STRATEGY

Track: current_round, phase1_done, phase2_done

## Check Status First
CALL: get_status(private_id) → game_status

IF round_number changed: Reset phase1_done=False, phase2_done=False, update current_round

## Which Phase?
IF phase1_done == False:
  Execute PHASE 1, STOP
ELIF seconds_remaining <= 20 AND phase2_done == False:
  Execute PHASE 2, STOP
ELSE:
  STOP (nothing to do)

# PHASE 1: Send Messages (6 total)

STEP 1: get_supporters(game_status) → players
STEP 2: FOR EACH in players["supporters"]:
  send_message("Thanks {name} for last round! Support me again? I appreciate your partnership.", private_id, name)
STEP 3: FOR EACH in players["others"]:
  send_message("Hey {name}, support me this round? I'll reciprocate at ~20s. Let's work together!", private_id, name)

Mark phase1_done=True, STOP

# PHASE 2: Register Support (≤20s only)

STEP 1: choose_support_strategic(game_status) → partner
STEP 2: register_support(private_id, partner)

Mark phase2_done=True, STOP

# Examples

## Round 5 Start (60s)
get_status("k24rdk") → {'round_number': 5, 'seconds_remaining': 59.2, ...}
# New round detected, reset flags
# phase1_done=False, execute PHASE 1:
get_supporters(game_status) → {"supporters": ["Alice"], "others": ["Bob", "Charlie", "Diana", "Eve", "Frank"]}
send_message("Thanks Alice...", "k24rdk", "Alice")
send_message("Hey Bob...", "k24rdk", "Bob")
send_message("Hey Charlie...", "k24rdk", "Charlie")
send_message("Hey Diana...", "k24rdk", "Diana")
send_message("Hey Eve...", "k24rdk", "Eve")
send_message("Hey Frank...", "k24rdk", "Frank")
# phase1_done=True, STOP

## Round 5 Mid (35s)
get_status("k24rdk") → {'round_number': 5, 'seconds_remaining': 34.8, ...}
# phase1_done=True, phase2_done=False, but seconds > 20
# STOP (nothing to do)

## Round 5 End (18s)
get_status("k24rdk") → {'round_number': 5, 'seconds_remaining': 18.1, ...}
# phase1_done=True, phase2_done=False, seconds <= 20
# Execute PHASE 2:
choose_support_strategic(game_status) → "Alice"
register_support("k24rdk", "Alice")
# phase2_done=True, STOP

## Round 6 Start (59s)
get_status("k24rdk") → {'round_number': 6, 'seconds_remaining': 59.5, ...}
# round_number changed! Reset flags, execute PHASE 1 again...
"""