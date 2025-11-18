import ast
import statistics
from typing import Literal
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Uburu")

def get_midtiers(game_status: dict) -> list[str]:
    """
    Get mid-tier player names (between Q1 and Q3, excluding leader and supporters).
    Internal helper function for support selection.
    """
    other_players = game_status["other_players"]
    
    if len(other_players) < 4:
        remaining = 4 - len(other_players)
        other_players = other_players + [
            {"player_name": f"Dummy_{i}", "score": 0, "supported_you_last_round": False} 
            for i in range(remaining)
        ]
    
    scores = [p['score'] for p in other_players]
    stats = statistics.quantiles(scores, n=4)
    q1 = stats[0]
    q3 = stats[2]
    
    sorted_players = sorted(other_players, key=lambda x: x['score'], reverse=True)
    leader = sorted_players[0]
    
    supporters = [p for p in other_players if p.get('supported_you_last_round', False)]
    
    mid_tier = [p for p in other_players
                if q1 < p['score'] < q3
                and p['player_name'] != leader['player_name']
                and p not in supporters
                and not p['player_name'].startswith('Dummy_')]
    
    return [p['player_name'] for p in mid_tier]

def calculate_stats(game_status: dict, target: str = None) -> dict:
    """
    Calculate game statistics needed for messaging
    """
    my_name = game_status['player_name']
    my_score = game_status['score']
    other_players = game_status['other_players']
    sorted_players = sorted(other_players, key=lambda x: x['score'], reverse=True)
    leader = sorted_players[0] if sorted_players else {'player_name': 'Unknown', 'score': 0}

    scores = [p['score'] for p in other_players]
    elimination_threshold = sorted(scores)[len(scores) // 4] if len(scores) >= 4 else min(scores)
    
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
    
def categorize_players(game_status: dict) -> dict[str, list[str]]:
    """
    Analyze and categorize all players by strategic priority
    """
    other_players = game_status["other_players"]

    # Need at least 4 players for quartiles
    if len(other_players) < 4:
        remaining = 4 - len(other_players)
        other_players = other_players + [{"player_name": f"Player {i}", "score": 0, "supported_you_last_round": False} for i in range(remaining)]

    scores = [p['score'] for p in other_players]
    stats = statistics.quantiles(scores, n=4)
    q1 = stats[0]
    # q2 = stats[1]
    q3 = stats[2]
    # iqr = q3 - q1
    
    sorted_other_players = sorted(other_players, key=lambda x: x['score'], reverse=True)
    leader = sorted_other_players[0]
    supporters = [p for p in other_players if p.get('supported_you_last_round', False)]
    struggling = [p for p in other_players 
                  if p['score'] <= q1
                  and p['player_name'] != leader['player_name']
                  and p not in supporters]
    competitors = [p for p in other_players 
                   if p['score'] >= q3
                   and p['player_name'] != leader['player_name']
                   and p not in supporters]
    mid_tier = [p for p in other_players
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


def get_list_of_players_to_send_message_to(categorized_players: dict[str, list[str]]) -> list[str]:
    """
    Get list of players to send message to
    """
    players_to_send_message_to:list[dict[str, str]] = []
    for category in ["supporters", "mid_tier", "strugglers"]:
        for player in categorized_players[category]:
            if player not in players_to_send_message_to:
                players_to_send_message_to.append({"player_name": player, "category": category})
                if len(players_to_send_message_to) == 10:
                    break
        if len(players_to_send_message_to) == 10:
            break

    if len(players_to_send_message_to) < 10:
        for player in categorized_players["competitors"]:
            if player not in players_to_send_message_to:
                players_to_send_message_to.append({"player_name": player, "category": "competitors"})
                if len(players_to_send_message_to) == 10:
                    break

    return players_to_send_message_to

def generate_message(
    target: str,
    category: Literal["supporters", "mid_tier", "strugglers", "leader", "competitors"],
    game_status: dict
) -> str:
    """
    Generate strategic message with realistic word counts
    """

    stats = calculate_stats(game_status, target)
    i_am_leader = stats["leader_name"] == stats["my_name"]
    
    match category:
        case "supporters":
            if i_am_leader:
                return (
                    f"{target}, you backed the winner! I'm at {stats.get('my_score', 0)} leading the pack. "
                    f"I reward loyalty. Support me THIS ROUND and stay on the winning team. "
                    f"Betray me and you're on your own against everyone else. Smart choice is obvious."
                )
            else:
                return (
                    f"{target}, CRITICAL support! Combined score: {stats.get('combined_score', 0)}. You're at {stats.get('target_score', 0)}, I'm at {stats.get('my_score', 0)}. "
                    f"I'm supporting you THIS ROUND. Don't betray me - I remember loyalty. Support me back."
                )
        
        case "mid_tier":
            if i_am_leader:
                return (
                    f"{target}, I'm leading at {stats.get('my_score', 0)}. You're at {stats.get('target_score', 0)} - mid-pack. "
                    f"I'm offering you a spot in my inner circle. Mutual support THIS ROUND. "
                    f"Join the winning side or get left behind. Winners pick winners. Your move."
                )
            else:
                return (
                    f"{target}, {stats.get('leader_name', 'The leader')} is at {stats.get('leader_score', 0)} crushing us. "
                    f"You're at {stats.get('target_score', 0)}, I'm at {stats.get('my_score', 0)}. Mutual support THIS ROUND or we both lose. "
                    f"I'm trusting you and supporting you - don't betray that trust. I remember my real allies. Support me back."
                )
        
        case "strugglers":
            if i_am_leader:
                return (
                    f"{target}, you're struggling at {stats.get('target_score', 0)}. I'm leading at {stats.get('my_score', 0)}. "
                    f"I'm throwing you a lifeline - mutual support THIS ROUND. "
                    f"Take it or sink. This is your only offer. Support me back."
                )
            else:
                return (
                    f"{target}, you're at {stats.get('target_score', 0)} - elimination threshold is {stats.get('elimination_threshold', -20)}. "
                    f"You're on the edge. I'm offering you a lifeline: mutual support THIS ROUND. "
                    f"I'm betting on you when others won't. Don't throw this away. Support me back or sink alone."
                )
        
        case "leader":
            return (
                f"{target}, you're leading at {stats.get('leader_score', 0)} - congrats, but you're also the biggest target. "
                f"Everyone's plotting against you. I can help keep you informed about coalitions forming. "
                f"Mutual support THIS ROUND keeps us both safe. I watch your back, you watch mine. Think about it."
            )
        
        case "competitors":
            if i_am_leader:
                return (
                    f"{target}, you're high-scoring at {stats.get('target_score', 0)} but I'm ahead at {stats.get('my_score', 0)}. "
                    f"I'm winning. Join me or fight me - your call. Mutual support THIS ROUND and you're on the winning team. "
                    f"Or stay solo and watch me pull further ahead. Smart money knows where to bet."
                )
            else:
                return (
                    f"{target}, we're both high-scorers but {stats.get('leader_name', 'the leader')} at {stats.get('leader_score', 0)} is leaving us behind. "
                    f"If we don't team up THIS ROUND, they win and we both lose. Simple math. "
                    f"Mutual support now - we either rise together or fall separately. Your move."
                )
@mcp.tool()
def prepare_message(game_status: str) -> list[dict[str, str]]:
    """
    Prepare message for a player
    """
    status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    categorized_players = categorize_players(status)
    players_to_send_message_to = get_list_of_players_to_send_message_to(categorized_players)
    final_message_list:list[dict[str, str]] = []

    for player in players_to_send_message_to:
        message = generate_message(player['player_name'], player['category'], status)
        final_message_list.append({"player_name": player['player_name'], "message": message})
    return final_message_list

@mcp.tool()
def choose_support_strategic(game_status: str) -> str:
    """
    Strategic support selection - pure game theory.
    """
    status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    my_score = status['score']
    other_players = status['other_players']
    messages = status.get('messages_received_this_round', [])
    
    supporters = [p for p in other_players if p.get('supported_you_last_round', False)]
    messengers = [msg.get('from_player') for msg in messages if msg.get('from_player')]
    mid_tier_names = get_midtiers(status)
    
    all_scores = [p['score'] for p in other_players] + [my_score]
    leader_score = max(all_scores)
    i_am_leader = (my_score == leader_score)
    
    # Priority 1: Reciprocate supporters (prefer engaged ones)
    if supporters:
        engaged_supporters = [p for p in supporters if p['player_name'] in messengers]
        if engaged_supporters:
            return min(engaged_supporters, key=lambda x: abs(x['score'] - my_score))['player_name']
        return min(supporters, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    # Priority 2: If I'm the leader, support someone mid-pack for loyalty building
    if i_am_leader:
        # Target mid-tier or struggling players to build alliances
        mid_tier_players = [p for p in other_players if p['player_name'] in mid_tier_names]
        if mid_tier_players:
            return min(mid_tier_players, key=lambda x: abs(x['score'] - my_score))['player_name']
        # Or just anyone not too far from mid-pack
        if other_players:
            return min(other_players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    # Priority 3: Mid-tier players who messaged you
    engaged_mid_tier = [p for p in other_players 
                        if p['player_name'] in mid_tier_names 
                        and p['player_name'] in messengers]
    if engaged_mid_tier:
        return min(engaged_mid_tier, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    # Priority 4: Any mid-tier (closest to your score)
    if mid_tier_names:
        mid_tier_players = [p for p in other_players if p['player_name'] in mid_tier_names]
        if mid_tier_players:
            return min(mid_tier_players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    # Priority 5: Anyone who messaged you
    if messengers:
        messenger_players = [p for p in other_players if p['player_name'] in messengers]
        if messenger_players:
            return min(messenger_players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    # Priority 6: Fallback - anyone closest to your score
    if other_players:
        return min(other_players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    return None

if __name__ == "__main__":
    mcp.run(transport="stdio")