"""
Line tracking and change detection system.
Tracks line changes, alternative lines, and chase list.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

LINES_HISTORY_FILE = 'lines_history.json'
CHASE_LIST_FILE = 'chase_list.json'
ALT_LINES_FILE = 'alt_lines.json'

def load_json_file(filename, default=None):
    """Load JSON file or return default."""
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default
    return default

def save_json_file(filename, data):
    """Save data to JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

def track_line_changes(current_lines: Dict[str, float], stat_type='PTS'):
    """
    Track line changes and detect what moved.
    
    Returns:
        dict: Line changes with old/new values and movement direction
    """
    history = load_json_file(LINES_HISTORY_FILE, {})
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get yesterday's lines
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    previous_lines = history.get(yesterday, {})
    
    changes = {}
    
    for player, current_line in current_lines.items():
        key = f"{player}_{stat_type}"
        previous_line = previous_lines.get(key)
        
        if previous_line is not None and previous_line != current_line:
            movement = current_line - previous_line
            changes[player] = {
                'previous': previous_line,
                'current': current_line,
                'movement': round(movement, 1),
                'direction': 'up' if movement > 0 else 'down',
                'stat_type': stat_type,
                'timestamp': datetime.now().isoformat()
            }
    
    # Save today's lines to history
    today_lines = {}
    for player, line in current_lines.items():
        today_lines[f"{player}_{stat_type}"] = line
    
    history[today] = today_lines
    save_json_file(LINES_HISTORY_FILE, history)
    
    return changes

def get_line_changes(stat_type='PTS'):
    """Get recent line changes."""
    history = load_json_file(LINES_HISTORY_FILE, {})
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    today_lines = history.get(today, {})
    yesterday_lines = history.get(yesterday, {})
    
    changes = {}
    for key, current_line in today_lines.items():
        if key.endswith(f"_{stat_type}"):
            player = key.replace(f"_{stat_type}", "")
            previous_line = yesterday_lines.get(key)
            
            if previous_line and previous_line != current_line:
                movement = current_line - previous_line
                changes[player] = {
                    'previous': previous_line,
                    'current': current_line,
                    'movement': round(movement, 1),
                    'direction': 'up' if movement > 0 else 'down'
                }
    
    return changes

def add_to_chase_list(player: str, line: float, stat_type: str, reason: str = ""):
    """Add a prop to the chase list."""
    chase_list = load_json_file(CHASE_LIST_FILE, [])
    
    # Check if already in list
    for item in chase_list:
        if item.get('player') == player and item.get('stat_type') == stat_type:
            # Update existing
            item['line'] = line
            item['reason'] = reason
            item['updated'] = datetime.now().isoformat()
            save_json_file(CHASE_LIST_FILE, chase_list)
            return True
    
    # Add new
    chase_list.append({
        'player': player,
        'line': line,
        'stat_type': stat_type,
        'reason': reason,
        'added': datetime.now().isoformat(),
        'updated': datetime.now().isoformat(),
        'status': 'active'
    })
    
    save_json_file(CHASE_LIST_FILE, chase_list)
    return True

def get_chase_list():
    """Get current chase list."""
    return load_json_file(CHASE_LIST_FILE, [])

def remove_from_chase_list(player: str, stat_type: str):
    """Remove from chase list."""
    chase_list = load_json_file(CHASE_LIST_FILE, [])
    chase_list = [item for item in chase_list 
                  if not (item.get('player') == player and item.get('stat_type') == stat_type)]
    save_json_file(CHASE_LIST_FILE, chase_list)
    return True

def add_alt_line(player: str, main_line: float, alt_line: float, stat_type: str, source: str = ""):
    """Add alternative line for a player."""
    alt_lines = load_json_file(ALT_LINES_FILE, {})
    
    key = f"{player}_{stat_type}"
    if key not in alt_lines:
        alt_lines[key] = []
    
    alt_lines[key].append({
        'main_line': main_line,
        'alt_line': alt_line,
        'source': source,
        'difference': round(alt_line - main_line, 1),
        'added': datetime.now().isoformat()
    })
    
    save_json_file(ALT_LINES_FILE, alt_lines)
    return True

def get_alt_lines(player: str = None, stat_type: str = 'PTS'):
    """Get alternative lines."""
    alt_lines = load_json_file(ALT_LINES_FILE, {})
    
    if player:
        key = f"{player}_{stat_type}"
        return alt_lines.get(key, [])
    
    # Return all
    result = {}
    for key, lines in alt_lines.items():
        if key.endswith(f"_{stat_type}"):
            player_name = key.replace(f"_{stat_type}", "")
            result[player_name] = lines
    
    return result

def update_line(player: str, old_line: float, new_line: float, stat_type: str = 'PTS'):
    """Update a line even after it's been sent off."""
    # Track the change
    changes = {
        player: {
            'previous': old_line,
            'current': new_line,
            'movement': round(new_line - old_line, 1),
            'direction': 'up' if new_line > old_line else 'down',
            'stat_type': stat_type,
            'timestamp': datetime.now().isoformat(),
            'manual_update': True
        }
    }
    
    # Save to history
    history = load_json_file(LINES_HISTORY_FILE, {})
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in history:
        history[today] = {}
    
    history[today][f"{player}_{stat_type}"] = new_line
    save_json_file(LINES_HISTORY_FILE, history)
    
    return changes
