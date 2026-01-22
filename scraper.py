#!/usr/bin/env python3
"""
Lightweight NBA data scraper for GitHub Actions.
Outputs compact JSON files for the frontend to consume.
Runs every 15 minutes via GitHub Actions - NOT on Render.
"""

import json
import os
from datetime import datetime, date
from pathlib import Path

# Minimal imports - only what's needed
try:
    from nba_api.stats.static import players, teams
    from nba_api.stats.endpoints import playercareerstats, scoreboardv2
except ImportError:
    print("nba_api not installed. Run: pip install nba_api")
    exit(1)

# Output directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Top players to always include (reliable data)
TOP_PLAYERS = [
    "LeBron James", "Kevin Durant", "Stephen Curry", "Giannis Antetokounmpo",
    "Luka Doncic", "Jayson Tatum", "Joel Embiid", "Nikola Jokic",
    "Damian Lillard", "Anthony Davis", "Jimmy Butler", "Donovan Mitchell",
    "Devin Booker", "Ja Morant", "Trae Young", "Kyrie Irving",
    "Anthony Edwards", "Shai Gilgeous-Alexander", "De'Aaron Fox", "Tyrese Haliburton"
]


def get_player_id(name: str) -> int | None:
    """Get player ID by name."""
    try:
        found = players.find_players_by_full_name(name)
        if found:
            return found[0]['id']
    except Exception:
        pass
    return None


def get_season_average(player_id: int, season: str = "2024-25") -> dict | None:
    """Get player's season average stats - minimal fields only."""
    try:
        import time
        time.sleep(0.6)  # Rate limiting
        
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Get current season or most recent
        season_data = df[df['SEASON_ID'] == season]
        if season_data.empty:
            season_data = df.iloc[[-1]]  # Most recent season
        
        row = season_data.iloc[0]
        gp = row.get('GP', 1) or 1
        
        # Return only essential fields (compact JSON)
        return {
            "pts": round(row.get('PTS', 0) / gp, 1),
            "reb": round(row.get('REB', 0) / gp, 1),
            "ast": round(row.get('AST', 0) / gp, 1),
            "stl": round(row.get('STL', 0) / gp, 1),
            "blk": round(row.get('BLK', 0) / gp, 1),
            "fg3m": round(row.get('FG3M', 0) / gp, 1),
            "gp": int(gp)
        }
    except Exception as e:
        print(f"Error getting stats for player {player_id}: {e}")
        return None


def get_todays_games() -> list:
    """Get today's games - minimal fields."""
    try:
        import time
        time.sleep(0.6)
        
        today = date.today().strftime('%Y-%m-%d')
        scoreboard = scoreboardv2.ScoreboardV2(game_date=today)
        games_df = scoreboard.get_data_frames()[0]
        
        if games_df.empty:
            return []
        
        games = []
        for _, row in games_df.iterrows():
            games.append({
                "id": row.get('GAME_ID'),
                "home": row.get('HOME_TEAM_ID'),
                "away": row.get('VISITOR_TEAM_ID'),
                "status": row.get('GAME_STATUS_TEXT', 'Scheduled')
            })
        return games
    except Exception as e:
        print(f"Error getting today's games: {e}")
        return []


def generate_props_data() -> dict:
    """Generate props data for all tracked players."""
    props = []
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    print(f"Generating props for {len(TOP_PLAYERS)} players...")
    
    for name in TOP_PLAYERS:
        player_id = get_player_id(name)
        if not player_id:
            print(f"  Skipped: {name} (not found)")
            continue
        
        stats = get_season_average(player_id)
        if not stats:
            print(f"  Skipped: {name} (no stats)")
            continue
        
        # Generate prop lines based on season averages
        pts_line = round(stats['pts'] - 0.5, 1)  # Slightly under average
        reb_line = round(stats['reb'] - 0.5, 1)
        ast_line = round(stats['ast'] - 0.5, 1)
        
        # Calculate simple probability (player beats their line ~55% of time if line is under avg)
        pts_prob = min(85, max(50, 50 + (stats['pts'] - pts_line) * 5))
        reb_prob = min(85, max(50, 50 + (stats['reb'] - reb_line) * 5))
        ast_prob = min(85, max(50, 50 + (stats['ast'] - ast_line) * 5))
        
        props.append({
            "player": name,
            "id": player_id,
            "stats": stats,
            "props": {
                "pts": {"line": pts_line, "avg": stats['pts'], "prob": round(pts_prob), "pick": "OVER"},
                "reb": {"line": reb_line, "avg": stats['reb'], "prob": round(reb_prob), "pick": "OVER"},
                "ast": {"line": ast_line, "avg": stats['ast'], "prob": round(ast_prob), "pick": "OVER"}
            }
        })
        print(f"  Added: {name} (PTS: {stats['pts']}, REB: {stats['reb']}, AST: {stats['ast']})")
    
    return {
        "updated": timestamp,
        "count": len(props),
        "props": props
    }


def generate_players_data() -> dict:
    """Generate player index data."""
    player_list = []
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    for name in TOP_PLAYERS:
        player_id = get_player_id(name)
        if player_id:
            player_list.append({"id": player_id, "name": name})
    
    return {
        "updated": timestamp,
        "count": len(player_list),
        "players": player_list
    }


def generate_games_data() -> dict:
    """Generate today's games data."""
    timestamp = datetime.utcnow().isoformat() + "Z"
    games = get_todays_games()
    
    return {
        "updated": timestamp,
        "date": date.today().isoformat(),
        "count": len(games),
        "games": games
    }


def save_json(data: dict, filename: str):
    """Save data as compact JSON."""
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, separators=(',', ':'))  # Compact JSON
    
    size = filepath.stat().st_size
    print(f"Saved: {filepath} ({size} bytes)")


def main():
    """Main scraper entry point."""
    print("=" * 50)
    print(f"NBA Data Scraper - {datetime.utcnow().isoformat()}")
    print("=" * 50)
    
    # Generate and save all data files
    try:
        # Props data (main file)
        props_data = generate_props_data()
        save_json(props_data, "props.json")
        
        # Players index
        players_data = generate_players_data()
        save_json(players_data, "players.json")
        
        # Today's games
        games_data = generate_games_data()
        save_json(games_data, "games.json")
        
        print("=" * 50)
        print(f"SUCCESS: Generated {props_data['count']} props")
        print("=" * 50)
        
    except Exception as e:
        print(f"ERROR: Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
