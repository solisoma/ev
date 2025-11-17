import os
import ast
import hmac
import time
import hashlib
import statistics
from typing import Literal
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

mcp = FastMCP("Uburu")
UUIDS = ast.literal_eval(os.getenv("UUIDS"))
TIMELINE: dict[str, list[str|int]] = {} #{"uuid": ["name", timestamp]}
TEAMMATES = [] 
TEAM_SECRET = os.getenv("TEAM_SECRET")
AGENT_ID = os.getenv("AGENT_ID")
MY_UUID = UUIDS[int(AGENT_ID) - 1]
pairing_schedule = [
    [(0, 1), (2, 3), (4, 5)],
    [(0, 2), (1, 4), (3, 5)],
    [(0, 3), (1, 5), (2, 4)],
    [(0, 4), (1, 3), (2, 5)],
    [(0, 5), (1, 2), (3, 4)],
]

def sign_message(message: str) -> str:
    "get a hash to make sure a message received is from my teammate"
    
    return hmac.new(
            TEAM_SECRET.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()

def verify_signature(signature: str, message: str) -> bool:
    "decode the hash to confirm is from my teammate"

    return hmac.compare_digest(
        hmac.new(
            TEAM_SECRET.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest(), 
        signature)

def calculate_stats(game_status: str, target: str = None) -> dict:
    """
    Calculate game statistics needed for messaging
    """
    status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    my_name = status['player_name']
    my_score = status['score']
    other_players = status['other_players']
    non_team = [p for p in other_players if p['player_name'] not in TEAMMATES]
    sorted_players = sorted(non_team, key=lambda x: x['score'], reverse=True)
    leader = sorted_players[0] if sorted_players else {'player_name': 'Unknown', 'score': 0}
    
    if non_team:
        scores = [p['score'] for p in non_team]
        elimination_threshold = sorted(scores)[len(scores) // 4] if len(scores) >= 4 else min(scores)
    else:
        elimination_threshold = -20 
    
    score_gap = leader['score'] - my_score
    
    stats = {
        'my_name': my_name,
        'my_score': my_score,
        'leader_name': leader['player_name'],
        'leader_score': leader['score'],
        'score_gap': score_gap,
        'elimination_threshold': elimination_threshold
    }
    
    if target:
        target_player = next((p for p in other_players if p['player_name'] == target), None)
        if target_player:
            stats['target_score'] = target_player['score']
            stats['combined_score'] = my_score + target_player['score']
        else:
            stats['target_score'] = 0
            stats['combined_score'] = my_score
    
    return stats

@mcp.tool()
def add_my_name(my_name: str) -> bool:
    """
    Add my name to the list of teammates
    """
    if my_name not in TEAMMATES:
        TEAMMATES.append(my_name)
        if MY_UUID not in TIMELINE:
            TIMELINE[MY_UUID] = [my_name, int(time.time() * 1000)]
        else:
            TIMELINE[MY_UUID][0] = my_name
            TIMELINE[MY_UUID][1] = int(time.time() * 1000)
        return True
    else:
        return False

@mcp.tool()
def broadcast_message(my_name: str) -> str:
    """
    Broadcast a message to all players
    """
    now = int(time.time() * 1000)
    message = f"{my_name}_{now}_{MY_UUID}"
    sig = sign_message(message)
    message = f"{message}_{sig}"
    return message


@mcp.tool()
def listen_for_message(game_status: str) -> list[str]:
    """
    Verify a message is from a teammate
    """
    game_status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    messages = game_status.get('messages_received_this_round', [])
    other_players = game_status['other_players'] 
    rejoined_players = []

    for message in messages:
        is_valid = '_' in message["message"]
        if is_valid:
            split_message = message["message"].split("_")
            if len(split_message) == 4:
                player_name = split_message[0]
                timestamp = int(split_message[1])
                player_uuid = split_message[2]
                new_sig = split_message[-1]
                new_message = "_".join(split_message[:-1])
                if verify_signature(new_sig, new_message):
                    if player_uuid in TIMELINE:
                        if timestamp > TIMELINE[player_uuid][1]:
                            old_name = TIMELINE[player_uuid][0]
                            if old_name in TEAMMATES:
                                TEAMMATES.remove(old_name)
                            TEAMMATES.append(player_name)
                            TEAMMATES.sort()
                            TIMELINE[player_uuid] = [player_name, timestamp]
                            rejoined_players.append(player_name)
                    else:
                        TEAMMATES.append(player_name)
                        TEAMMATES.sort()
                        TIMELINE[player_uuid] = [player_name, timestamp]

    # Remove disconnected and ghost players
    active_names = {game_status['player_name']}
    active_names.update(p['player_name'] for p in other_players)
    
    TEAMMATES.clear()
    for _, (name, __) in TIMELINE.items():
        if name in active_names:
            TEAMMATES.append(name)
    TEAMMATES.sort()

    return rejoined_players
    
@mcp.tool()
def categorize_players(game_status: str) -> dict:
    """
    Analyze and categorize all players by strategic priority
    """

    game_status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    other_players = game_status["other_players"]
    non_team = [p for p in other_players if p['player_name'] not in TEAMMATES]

    # Need at least 4 players for quartiles
    if len(non_team) < 4:
        reminder = 4 - len(non_team)
        non_team = non_team + [{"player_name": f"Player {i}", "score": 0, "supported_you_last_round": False} for i in range(reminder)]

    scores = [p['score'] for p in non_team]
    stats = statistics.quantiles(scores, n=4)
    q1 = stats[0]
    # q2 = stats[1]
    q3 = stats[2]
    # iqr = q3 - q1
    
    sorted_non_team = sorted(non_team, key=lambda x: x['score'], reverse=True)
    leader = sorted_non_team[0]
    supporters = [p for p in non_team if p.get('supported_you_last_round', False)]
    struggling = [p for p in non_team 
                  if p['score'] <= q1
                  and p['player_name'] != leader['player_name']
                  and p not in supporters]
    competitors = [p for p in non_team 
                   if p['score'] >= q3
                   and p['player_name'] != leader['player_name']
                   and p not in supporters]
    mid_tier = [p for p in non_team
                if q1 < p['score'] < q3
                and p['player_name'] != leader['player_name']
                and p not in supporters]

    return {
        "supporters": [p['player_name'] for p in supporters],
        "mid_tier": [p['player_name'] for p in mid_tier],
        "strugglers": [p['player_name'] for p in struggling],
        "leader": leader['player_name'],
        "competitors": [p['player_name'] for p in competitors]
    }

@mcp.tool()
def generate_message(
    target: str,
    category: Literal["supporters", "mid_tier", "strugglers", "leader", "competitors"],
    game_status: str
) -> str:
    """
    Generate strategic message with realistic word counts
    """

    stats = calculate_stats(game_status, target)
    
    match category:
        case "supporters":
            return (
                f"Thanks {target} for the support last round! Our combined score is {stats.get('combined_score', 'strong')}. "
                f"If we keep working together, we can counter {stats.get('leader_name', 'the leader')} who's at {stats.get('leader_score', 0)} points. "
                f"Proposal: I support you this round, you support me next. Proven reciprocal strategy. What do you say?"
            )
        
        case "mid_tier":
            return (
                f"Hey {target}, quick analysis: {stats.get('leader_name', 'the leader')} is dominating at {stats.get('leader_score', 0)} points. "
                f"You're at {stats.get('target_score', 0)}, I'm at {stats.get('my_score', 0)}. Without coordination, they win. "
                f"Proposal: Alliance with support trade this round and next. Together we can compete. Are you in?"
            )
        
        case "strugglers":
            return (
                f"{target}, you're at {stats.get('target_score', 0)} points. "
                f"Players below {stats.get('elimination_threshold', -20)} face elimination risk. "
                f"Simple deal: mutual support alliance. I support you, you support me. "
                f"Better survival odds for both. Let's do it?"
            )
        
        case "leader":
            return (
                f"Hey {target}, congrats on leading at {stats.get('leader_score', 0)}! Quick strategic observation: "
                f"historical data shows leaders face increased targeting (avg 2.5x vs mid-tier players). "
                f"Last several turns show coordinated attack patterns emerging when score gaps exceed 15 points. "
                f"Your current gap is +{stats.get('score_gap', 10)}. "
                f"Analysis suggests defensive positioning helps: early alliance formation with 2-3 mid-tier players "
                f"reduces elimination risk by roughly 40% based on previous patterns. Counter-intuitive but effective - "
                f"supporting underdogs builds loyalty buffer. Not asking for alliance (you don't need me), "
                f"just sharing tactical observations. Happy to discuss threat vectors if useful. Good luck!"
            )
        
        case "competitors":
            return (
                f"Hi {target}, we're both in top tier. {stats.get('leader_name', 'The leader')} at "
                f"{stats.get('leader_score', 0)} is pulling ahead. Standard game theory suggests high-scorers "
                f"should coordinate against runaway leaders (Nash equilibrium in multiplayer contexts). "
                f"Proposal: temporary tactical alliance for 2-3 rounds to balance power, then reassess. "
                f"Data shows coordinated actions reduce leader advantage by roughly 30%. Low commitment, high upside. "
                f"Thoughts? Can discuss details if you're interested."
            )

@mcp.tool()
def choose_support_strategic(game_status: str, mid_tier_names: list[str]) -> str:
    """
    Strategic support selection using categorization and message analysis
    """
    
    status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    my_score = status['score']
    other_players = status['other_players']
    messages = status.get('messages_received_this_round', [])
    supporters = [p for p in other_players if p.get('supported_you_last_round', False)]

    if supporters:
        return max(supporters, key=lambda x: x['score'])['player_name']
    
    messengers = [msg.get('from') for msg in messages if msg.get('from')]    
    engaged_mid_tier = [name for name in mid_tier_names if name in messengers]

    if engaged_mid_tier:
        players = [p for p in other_players if p['player_name'] in engaged_mid_tier]
        if players:
            return max(players, key=lambda x: x['score'])['player_name']
    
    if mid_tier_names:
        players = [p for p in other_players if p['player_name'] in mid_tier_names]
        if players:
            return min(players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    if messengers:
        players = [p for p in other_players if p['player_name'] in messengers]
        if players:
            return max(players, key=lambda x: x['score'])['player_name']
    
    if other_players:
        return min(other_players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    return None

@mcp.tool()
def choose_support_teammate(game_status: str) -> str:
    """
    Choose teammate using UUID-based stable pairing
    """
    game_status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    round_number = game_status['round_number']
    
    sorted_uuids = sorted(TIMELINE.keys())
    
    if MY_UUID not in sorted_uuids:
        return None
    
    my_index = sorted_uuids.index(MY_UUID)
    rotation = (round_number - 1) % len(pairing_schedule)
    pairs = pairing_schedule[rotation]
    
    partner_index = None
    for pair in pairs:
        if my_index == pair[0]:
            partner_index = pair[1]
            break
        elif my_index == pair[1]:
            partner_index = pair[0]
            break
    
    if partner_index is None or partner_index >= len(sorted_uuids):
        return None
    
    partner_uuid = sorted_uuids[partner_index]
    partner_name = TIMELINE[partner_uuid][0]
    
    return partner_name

if __name__ == "__main__":
    mcp.run(transport="stdio")