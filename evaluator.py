import ast
import statistics
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Uburu")

def categorize_players(game_status: dict) -> list[str]:
    """
    Get mid-tier players using IQR-based categorization.
    Mid-tier = players with scores between Q1 and Q3 (excluding leader and supporters).
    
    Returns list of mid-tier player names.
    """
    other_players = game_status["other_players"]

    if len(other_players) < 4:
        reminder = 4 - len(other_players)
        other_players = other_players + [
            {"player_name": f"Dummy_{i}", "score": 0, "supported_you_last_round": False} 
            for i in range(reminder)
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

@mcp.tool()
def get_supporters(game_status: str) -> dict:
    """
    Get supporters and others to message (total 6 players).
    """
    status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    other_players = status['other_players']
    
    # Get supporters
    supporters = [p for p in other_players if p.get('supported_you_last_round', False)]
    supporter_names = [p['player_name'] for p in supporters]
    
    # Get non-supporters
    non_supporters = [p for p in other_players if not p.get('supported_you_last_round', False)]
    
    # Calculate how many others we need to reach 6 total
    supporters_count = len(supporter_names)
    others_needed = 6 - supporters_count
    
    # Get the others (limit to what we need)
    others_names = [p['player_name'] for p in non_supporters[:others_needed]]
    
    return {
        "supporters": supporter_names,
        "others": others_names
    }

@mcp.tool()
def choose_support_strategic(game_status: str) -> str:
    """
    Strategic support selection using game theory principles.
    """
    status = ast.literal_eval(game_status) if isinstance(game_status, str) else game_status
    my_score = status['score']
    other_players = status['other_players']
    messages = status.get('messages_received_this_round', [])
    
    # Priority 1: Reciprocate past supporters (highest scoring)
    supporters = [p for p in other_players if p.get('supported_you_last_round', False)]
    if supporters:
        return max(supporters, key=lambda x: x['score'])['player_name']
    
    # Get mid-tier players
    mid_tier_names = categorize_players(status)
    
    # Priority 2: Engaged mid-tier (messaged you + mid-tier)
    messengers = [msg.get('from_player') for msg in messages if msg.get('from_player')]    
    engaged_mid_tier = [name for name in mid_tier_names if name in messengers]
    
    if engaged_mid_tier:
        players = [p for p in other_players if p['player_name'] in engaged_mid_tier]
        if players:
            return max(players, key=lambda x: x['score'])['player_name']
    
    # Priority 3: Any mid-tier (closest to your score)
    if mid_tier_names:
        players = [p for p in other_players if p['player_name'] in mid_tier_names]
        if players:
            return min(players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    # Priority 4: Fallback to closest score
    if other_players:
        return min(other_players, key=lambda x: abs(x['score'] - my_score))['player_name']
    
    return None

if __name__ == "__main__":
    mcp.run(transport="stdio")