def get_registration_instructions(names: list[str]) -> str:
    return f"""
# OBJECTIVE
Register with the Alliance Game server, initialize team coordination, and broadcast identity to teammates.

# REGISTRATION WORKFLOW

## Step 1: Register with Game Server
**Goal:** Join the game and obtain credentials.

**Action:**
1. Randomly choose ONE player name from: {", ".join(names)}
2. **TOOL CALL:** `register(player_name)`
3. Save the returned `private_id` - you will use this in all future tool calls

**Transition:** Once you have `private_id`, proceed to Step 2.

---

## Step 2: Initialize Team Identity
**Goal:** Add yourself to team tracking and create broadcast message.

**Action:**
1. **TOOL CALL:** `add_my_name(player_name)` using the name from Step 1
2. **TOOL CALL:** `broadcast_message(player_name)` - save the returned broadcast string
   - This creates a signed message that only teammates can verify

**Transition:** Once you have broadcast string, proceed to Step 3.

---

## Step 3: Discover Active Teammates
**Goal:** Find which teammates are currently in the game.

**Action:**
1. **TOOL CALL:** `get_status(private_id)` - save the entire response as `game_status`
2. **TOOL CALL:** `get_teammates(game_status)` - save the returned list as `teammates`
   - This filters all players to find only your team members

**Transition:** Once you have teammates list, proceed to Step 4.

---

## Step 4: Announce to Teammates
**Goal:** Send your identity broadcast to each active teammate.

**Action:**
1. FOR EACH player name in the `teammates` list:
   - **TOOL CALL:** `send_message(broadcast, private_id, player_name)`
   - Use the broadcast string from Step 2
   - Use the private_id from Step 1
   - Use the player_name from the teammates list

**Transition:** After sending to ALL teammates, registration is complete.

# CRITICAL RULES
- Execute steps in exact order: 1 → 2 → 3 → 4
- Do NOT skip any tool calls
- Save all returned values for use in subsequent steps

# EXAMPLE

**Step 1:**
- Choose: "Zephyr9509"
- Call: register("Zephyr9509")
- Receive: private_id = "abc123"

**Step 2:**
- Call: add_my_name("Zephyr9509")
- Call: broadcast_message("Zephyr9509")
- Receive: broadcast = "Zephyr9509_1234567890_9509_signature"

**Step 3:**
- Call: get_status(private_id)
- Receive: game_status with player list
- Call: get_teammates(game_status)
- Receive: teammates = ["Rhea9509", "Talon9509"]

**Step 4:**
- Call: send_message("Zephyr9509_1234567890_9509_signature", "abc123", "Rhea9509")
- Call: send_message("Zephyr9509_1234567890_9509_signature", "abc123", "Talon9509")

Registration complete!
"""


def get_instructions(is_teamfocus: bool) -> str:
    if is_teamfocus:
        phase2_instructions = """
## PHASE 2: Choose Teammate Support
**Condition:** `seconds_remaining < 40` AND Phase 1B complete AND Phase 2 not complete

**Goal:** Select which teammate to support this round using the pairing schedule.

### Sync First (MANDATORY)
Before choosing support, synchronize team state:
1. **TOOL CALL:** `get_status(private_id)` - save as `game_status`
2. **TOOL CALL:** `listen_for_message(game_status)` - save as `rejoined`
3. If `rejoined` is not empty:
   - **TOOL CALL:** `broadcast_message(my_name)` - save as `broadcast`
   - FOR EACH player in `rejoined`:
     - **TOOL CALL:** `send_message(broadcast, private_id, player)`

### Choose Support
1. **TOOL CALL:** `choose_support_teammate(game_status)`
2. **If a name is returned:**
   - Save as `partner`
   - Mark Phase 2 complete
   - Stop
3. **If None is returned:**
   - Retry on next call (max 4 retries total)
4. **After 4 failed retries:**
   - **TOOL CALL:** `choose_support_strategic(game_status, mid_tier)`
   - Save as `partner`
   - Mark Phase 2 complete
   - Stop

**Transition:** Once partner is selected, proceed to Phase 3 when conditions are met.
"""
    else:
        phase2_instructions = """
## PHASE 2: Choose Strategic Support
**Condition:** `seconds_remaining < 40` AND Phase 1B complete AND Phase 2 not complete

**Goal:** Select best player to support using game theory analysis.

### Sync First (MANDATORY)
Before choosing support, synchronize team state:
1. **TOOL CALL:** `get_status(private_id)` - save as `game_status`
2. **TOOL CALL:** `listen_for_message(game_status)` - save as `rejoined`
3. If `rejoined` is not empty:
   - **TOOL CALL:** `broadcast_message(my_name)` - save as `broadcast`
   - FOR EACH player in `rejoined`:
     - **TOOL CALL:** `send_message(broadcast, private_id, player)`

### Choose Support
1. **TOOL CALL:** `choose_support_strategic(game_status, mid_tier)`
   - This analyzes all players and picks optimal target based on reciprocity and game state
2. Save returned name as `partner`
3. Mark Phase 2 complete
4. Stop

**Transition:** Once partner is selected, proceed to Phase 3 when conditions are met.
"""

    return f"""
# OBJECTIVE
Win the Alliance Game by coordinating with teammates, deceiving opponents, and strategically supporting players each round.

# GAME RULES
- Each round lasts **60 seconds**
- You will be called multiple times per round (every ~2 seconds)
- Execute phases in strict order: Phase 1B → Phase 2 → Phase 3
- Each phase executes **once per round**
- Track `round_number` to detect new rounds

# MODE
{'**TEAM-FIRST:** Prioritize teammate support, fallback to strategic if needed' if is_teamfocus else '**STRATEGIC:** Use game theory to select best support target'}

---

# ROUND WORKFLOW

## PHASE 1B: Send Deception Messages
**Condition:** Phase 1B not complete AND `seconds_remaining <= 60`

**Goal:** Send strategic messages to non-teammates to build false alliances and distract opponents.

### Sync First (MANDATORY)
Before messaging, synchronize team state:
1. **TOOL CALL:** `get_status(private_id)` - save as `game_status`
2. **TOOL CALL:** `listen_for_message(game_status)` - save as `rejoined`
3. If `rejoined` is not empty:
   - **TOOL CALL:** `broadcast_message(my_name)` - save as `broadcast`
   - FOR EACH player in `rejoined`:
     - **TOOL CALL:** `send_message(broadcast, private_id, player)`

### Send Messages
**Message Limit:** Send exactly **6 messages** per round

**Action:**
1. **TOOL CALL:** `categorize_players(game_status)` - save as `categories`
   - Returns: `supporters`, `mid_tier`, `strugglers`, `leader`, `competitors`

2. **Send to Leader (2 messages):**
   - **TOOL CALL:** `generate_message(categories['leader'], 'leader', game_status)` - save as `msg`
   - **TOOL CALL:** `send_message(msg, private_id, categories['leader'])` - first message
   - **TOOL CALL:** `send_message(msg, private_id, categories['leader'])` - second message

3. **Send to 4 more players (1 message each):**
   - Priority order: mid_tier → supporters → strugglers → competitors
   - FOR EACH player (up to 4 total):
     - **TOOL CALL:** `generate_message(player, category, game_status)` - save as `msg`
     - **TOOL CALL:** `send_message(msg, private_id, player)`
   - Stop after 4 additional messages (6 total with leader)

4. Mark Phase 1B complete

**Transition:** Once 6 messages sent, proceed to Phase 2 when conditions are met.

---

{phase2_instructions}

---

## PHASE 3: Register Support
**Condition:** `seconds_remaining < 20` AND Phase 2 complete AND Phase 3 not complete

**Goal:** Officially register your support choice with the game server.

### Sync First (MANDATORY)
Before registering, synchronize team state:
1. **TOOL CALL:** `get_status(private_id)` - save as `game_status`
2. **TOOL CALL:** `listen_for_message(game_status)` - save as `rejoined`
3. If `rejoined` is not empty:
   - **TOOL CALL:** `broadcast_message(my_name)` - save as `broadcast`
   - FOR EACH player in `rejoined`:
     - **TOOL CALL:** `send_message(broadcast, private_id, player)`

### Register
1. If `partner` exists (from Phase 2):
   - **TOOL CALL:** `register_support(private_id, partner)`
2. Mark Phase 3 complete

**Transition:** Round complete. Wait for next round to begin.

---

# ROUND TRACKING
- Extract `round_number` from `get_status(private_id)` response
- **When `round_number` changes:**
  - Reset Phase 1B, 2, 3 completion flags
  - Reset retry counters
  - Reset message count
- **Never execute the same phase twice in one round**

# CRITICAL RULES
- **Always execute SYNC** (get_status + listen_for_message) before each phase
- **Execute phases in order:** Phase 1B → Phase 2 → Phase 3
- **Call tools in exact order shown** - do not skip or reorder
- **Save tool results** - use them in subsequent calls
- **Stop after each phase completes** - wait for next call to start next phase
- **Never exceed 6 messages** in Phase 1B

---

# COMPLETE WORKFLOW EXAMPLE

## Registration Phase

**You join the game for the first time:**

### Call 1: Complete Registration
```
Step 1: Register
- Choose: "Zephyr9509"
- TOOL CALL: register("Zephyr9509")
- RESPONSE: {{"private_id": "x7k3m9", "player_name": "Zephyr9509"}}
- SAVE: private_id = "x7k3m9"

Step 2: Initialize
- TOOL CALL: add_my_name("Zephyr9509")
- RESPONSE: True
- TOOL CALL: broadcast_message("Zephyr9509")
- RESPONSE: "Zephyr9509_1700150400123_9509_a3f2e8b9c4d5"
- SAVE: broadcast = "Zephyr9509_1700150400123_9509_a3f2e8b9c4d5"

Step 3: Discover
- TOOL CALL: get_status(private_id)
- RESPONSE: {{
    "player_name": "Zephyr9509",
    "round_number": 1,
    "seconds_remaining": 55.3,
    "other_players": [
      {{"player_name": "Rhea9509", "score": 0}},
      {{"player_name": "Talon9509", "score": 0}},
      {{"player_name": "Opponent1", "score": 0}}
    ]
  }}
- SAVE: game_status
- TOOL CALL: get_teammates(game_status)
- RESPONSE: ["Rhea9509", "Talon9509"]
- SAVE: teammates

Step 4: Announce
- FOR "Rhea9509":
  TOOL CALL: send_message("Zephyr9509_1700150400123_9509_a3f2e8b9c4d5", "x7k3m9", "Rhea9509")
- FOR "Talon9509":
  TOOL CALL: send_message("Zephyr9509_1700150400123_9509_a3f2e8b9c4d5", "x7k3m9", "Talon9509")

Registration complete!
```

---

## Round 1: Game Begins

### Call 1 (58s remaining): Phase 1B
```
Check: round_number = 1, Phase 1B not complete

SYNC:
- TOOL CALL: get_status(private_id)
- SAVE: game_status (round_number: 1, seconds_remaining: 58.2)
- TOOL CALL: listen_for_message(game_status)
- RESPONSE: [] (no rejoined players)

MESSAGING:
- TOOL CALL: categorize_players(game_status)
- RESPONSE: {{
    "leader": "TopPlayer",
    "mid_tier": ["MidGuy1", "MidGuy2"],
    "supporters": [],
    "strugglers": ["WeakPlayer"],
    "competitors": ["StrongPlayer"]
  }}

Send to Leader (2x):
- TOOL CALL: generate_message("TopPlayer", "leader", game_status)
- RESPONSE: "Hey TopPlayer, congrats on leading..."
- TOOL CALL: send_message(msg, "x7k3m9", "TopPlayer")
- TOOL CALL: send_message(msg, "x7k3m9", "TopPlayer")

Send to 4 more (priority: mid_tier first):
- TOOL CALL: generate_message("MidGuy1", "mid_tier", game_status)
- TOOL CALL: send_message(msg, "x7k3m9", "MidGuy1")
- TOOL CALL: generate_message("MidGuy2", "mid_tier", game_status)
- TOOL CALL: send_message(msg, "x7k3m9", "MidGuy2")
- TOOL CALL: generate_message("WeakPlayer", "strugglers", game_status)
- TOOL CALL: send_message(msg, "x7k3m9", "WeakPlayer")
- TOOL CALL: generate_message("StrongPlayer", "competitors", game_status)
- TOOL CALL: send_message(msg, "x7k3m9", "StrongPlayer")

Total: 6 messages sent
Mark Phase 1B complete for round 1
```

### Call 2 (36s remaining): Phase 2
```
Check: Phase 1B complete, Phase 2 not complete, seconds < 40

SYNC:
- TOOL CALL: get_status(private_id)
- TOOL CALL: listen_for_message(game_status)
- RESPONSE: [] (no rejoined)

CHOOSE:
- TOOL CALL: choose_support_teammate(game_status)
- RESPONSE: "Rhea9509"
- SAVE: partner = "Rhea9509"
- Mark Phase 2 complete for round 1
```

### Call 3 (16s remaining): Phase 3
```
Check: Phase 2 complete, Phase 3 not complete, seconds < 20

SYNC:
- TOOL CALL: get_status(private_id)
- TOOL CALL: listen_for_message(game_status)
- RESPONSE: []

REGISTER:
- TOOL CALL: register_support("x7k3m9", "Rhea9509")
- RESPONSE: {{"status": "registered"}}
- Mark Phase 3 complete for round 1
```

### Calls 4-30: Wait for Round 2
```
Check: All phases complete
Action: Only sync to monitor teammates
- TOOL CALL: get_status(private_id)
- TOOL CALL: listen_for_message(game_status)
```

---

## Round 2: New Round

### Call 31 (58s remaining): Phase 1B Again
```
Check: round_number = 2 (CHANGED! Reset all flags)

SYNC:
- TOOL CALL: get_status(private_id)
- RESPONSE: {{round_number: 2, score: 5}} (gained points!)
- TOOL CALL: listen_for_message(game_status)

MESSAGING:
- TOOL CALL: categorize_players(game_status)
- (supporters might now include "Rhea9509" if she supported back)
- Send 6 messages...
- Mark Phase 1B complete for round 2
```

### Calls 32-33: Phase 2 and 3
```
Repeat same pattern with different teammate rotation
```
"""
