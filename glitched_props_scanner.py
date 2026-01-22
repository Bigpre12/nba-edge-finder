"""
Automated Glitched Props Scanner
Scans betting platforms around the clock to find pricing errors and glitched props.
"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Try to import requests, but don't fail if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. Some features may be limited.")

from glitched_props import add_glitched_prop, get_glitched_props

# Configuration
SCAN_INTERVAL_MINUTES = 5  # Background scan every 5 minutes (for duplicate checking)
PLATFORMS = ['PrizePicks', 'Underdog', 'DraftKings', 'FanDuel', 'BetMGM', 'Caesars', 'PointsBet']

# Cache for recent scans to avoid duplicates
RECENT_SCANS_FILE = 'recent_glitched_scans.json'

def load_recent_scans():
    """Load recent scan results to avoid duplicates."""
    if os.path.exists(RECENT_SCANS_FILE):
        try:
            with open(RECENT_SCANS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_recent_scans(scans: Dict):
    """Save recent scan results."""
    try:
        with open(RECENT_SCANS_FILE, 'w') as f:
            json.dump(scans, f, indent=2)
    except Exception as e:
        print(f"Error saving recent scans: {e}")

def fetch_platform_lines(platform: str, player_name: str, stat_type: str = 'PTS'):
    """
    Fetch current lines from a betting platform.
    This is a placeholder - actual implementation would use platform APIs or scraping.
    
    Args:
        platform: Platform name (PrizePicks, Underdog, etc.)
        player_name: Player name
        stat_type: Stat type (PTS, REB, AST, etc.)
    
    Returns:
        dict: Line information or None if not found
    """
    # TODO: Implement actual platform API calls or scraping
    # For now, this is a mock that simulates finding lines
    
    # In production, you would:
    # 1. Use platform APIs if available
    # 2. Scrape platform websites (check ToS first)
    # 3. Use third-party line aggregation services
    
    # Mock implementation - replace with actual API calls
    return None

def compare_lines_across_platforms(player_name: str, stat_type: str = 'PTS'):
    """
    Compare lines for a player across multiple platforms to find discrepancies.
    
    Args:
        player_name: Player name
        stat_type: Stat type
    
    Returns:
        dict: Glitched prop info if found, None otherwise
    """
    platform_lines = {}
    
    # Fetch lines from all platforms
    for platform in PLATFORMS:
        try:
            line_data = fetch_platform_lines(platform, player_name, stat_type)
            if line_data and 'line' in line_data:
                platform_lines[platform] = line_data['line']
        except Exception as e:
            print(f"Error fetching from {platform}: {e}")
            continue
    
    if len(platform_lines) < 2:
        return None  # Need at least 2 platforms to compare
    
    # Find the outlier (glitched line)
    lines = list(platform_lines.values())
    avg_line = sum(lines) / len(lines)
    
    # Find lines that are significantly different from average
    threshold = 2.0  # 2 points difference = potential glitch
    glitched_platforms = []
    
    for platform, line in platform_lines.items():
        diff = abs(line - avg_line)
        if diff >= threshold:
            glitched_platforms.append({
                'platform': platform,
                'line': line,
                'difference': line - avg_line,
                'market_avg': round(avg_line, 1)
            })
    
    if glitched_platforms:
        # Return the most glitched one
        most_glitched = max(glitched_platforms, key=lambda x: abs(x['difference']))
        
        # Calculate rating (1-10) based on difference size
        diff = abs(most_glitched['difference'])
        if diff >= 5.0:
            rating = 10
        elif diff >= 4.0:
            rating = 9
        elif diff >= 3.0:
            rating = 8
        elif diff >= 2.5:
            rating = 7
        elif diff >= 2.0:
            rating = 6
        else:
            rating = 5
        
        reasoning = f"Line is {most_glitched['difference']:+.1f} points off market average ({most_glitched['market_avg']}). " \
                   f"Market range: {min(lines):.1f} - {max(lines):.1f}"
        
        return {
            'player': player_name,
            'stat_type': stat_type,
            'platform': most_glitched['platform'],
            'line': most_glitched['line'],
            'reasoning': reasoning,
            'rating': rating,
            'market_avg': most_glitched['market_avg'],
            'difference': most_glitched['difference']
        }
    
    return None

def get_relevant_players_for_today():
    """
    Get players that matter for today's slate:
    1. Players with games today
    2. Role players on hot streaks (2+ games)
    3. Players with positive trending performance
    
    Returns:
        list: List of relevant players with reasoning
    """
    from nba_engine import (
        get_all_active_players, fetch_recent_games, calculate_streak,
        get_player_performance_factors, get_season_average
    )
    from datetime import datetime
    
    relevant_players = []
    active_players = get_all_active_players()
    
    if not active_players:
        return []
    
    print(f"Filtering {len(active_players)} active players for relevant targets...")
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    for player in active_players:
        player_name = player['full_name']
        reasons = []
        
        try:
            # Check for hot streaks (2+ consecutive OVER or UNDER hits)
            # Use a reasonable line estimate (season average) for streak calculation
            season_avg = get_season_average(player['id'], 'PTS', '2023-24', player_name)
            if season_avg:
                streak_info = calculate_streak(player_name, season_avg, 'PTS', '2023-24', min_streak=2)
                if streak_info.get('active'):
                    reasons.append(f"Hot streak: {streak_info['streak_count']} games {streak_info['streak_type']}")
            
            # Check for positive performance trends
            factors = get_player_performance_factors(player_name, 'PTS', '2023-24')
            if factors:
                trend = factors.get('performance_trend', 'stable')
                if trend == 'up':
                    recent_avg = factors.get('recent_stat_avg', 0)
                    older_avg = factors.get('older_stat_avg', 0)
                    improvement = recent_avg - older_avg
                    if improvement > 2:  # Significant improvement
                        reasons.append(f"Positive trend: +{improvement:.1f} PTS improvement")
                
                # Check for role players with consistent minutes (not stars, but reliable)
                recent_minutes = factors.get('recent_min_avg', 0)
                if 20 <= recent_minutes <= 35:  # Role player minutes range
                    if not factors.get('rotation_change', False) and not factors.get('injury_risk', False):
                        reasons.append(f"Role player: {recent_minutes:.0f} MPG, stable rotation")
            
            # If player has any relevant reason, add them
            if reasons:
                relevant_players.append({
                    'player': player,
                    'player_name': player_name,
                    'reasons': reasons,
                    'priority': len(reasons)  # More reasons = higher priority
                })
        
        except Exception as e:
            # Skip players that error out (likely no data)
            continue
    
    # Sort by priority (most reasons first)
    relevant_players.sort(key=lambda x: x['priority'], reverse=True)
    
    print(f"Found {len(relevant_players)} relevant players for today's scan")
    if relevant_players:
        print("Top targets:")
        for i, p in enumerate(relevant_players[:10], 1):
            print(f"  {i}. {p['player_name']}: {', '.join(p['reasons'])}")
    
    return relevant_players

def scan_active_players_for_glitches(quick_scan=False, max_players=None):
    """
    Scan relevant players for glitched props across platforms.
    Focuses on:
    - Players with games today
    - Role players on hot streaks
    - Players with positive trending performance
    
    Args:
        quick_scan: If True, only scan top 10-20 players for instant results
        max_players: Maximum number of players to scan (None = all relevant)
    
    This is the main scanning function that runs periodically.
    """
    scan_type = "QUICK" if quick_scan else "FULL"
    print(f"[{datetime.now()}] Starting {scan_type} glitched props scan...")
    
    try:
        # Get relevant players (not all active players)
        relevant_players = get_relevant_players_for_today()
        
        if not relevant_players:
            print("No relevant players found for scanning")
            return []
        
        # Limit players for quick scan (top 10-20 highest priority)
        if quick_scan:
            max_players = max_players or 15  # Default to 15 for instant results
            players_to_scan = relevant_players[:max_players]
            print(f"QUICK SCAN: Scanning top {len(players_to_scan)} priority players for instant results...")
        else:
            players_to_scan = relevant_players[:max_players] if max_players else relevant_players
            print(f"FULL SCAN: Scanning {len(players_to_scan)} relevant players across {len(PLATFORMS)} platforms...")
        
        recent_scans = load_recent_scans()
        found_glitches = []
        scanned_count = 0
        
        for player_data in players_to_scan:
            player = player_data['player']
            player_name = player_data['player_name']
            reasons = player_data['reasons']
            scanned_count += 1
            
            # Check if we recently scanned this player
            scan_key = f"{player_name}_PTS"
            last_scan = recent_scans.get(scan_key, {}).get('last_scan')
            if last_scan:
                last_scan_time = datetime.fromisoformat(last_scan)
                if datetime.now() - last_scan_time < timedelta(minutes=SCAN_INTERVAL_MINUTES):
                    continue  # Skip if scanned recently
            
            try:
                # Scan for PTS first (most common)
                glitch = compare_lines_across_platforms(player_name, 'PTS')
                
                if glitch:
                    # Enhance reasoning with why this player was selected
                    enhanced_reasoning = f"{glitch['reasoning']} | Target selected because: {', '.join(reasons)}"
                    
                    prop_text = f"{player_name} {'O' if glitch['line'] < glitch['market_avg'] else 'U'} {glitch['line']} {glitch['stat_type']}"
                    
                    # Check if this prop already exists
                    existing_props = get_glitched_props()
                    is_duplicate = any(
                        p['prop'] == prop_text and p['platform'] == glitch['platform']
                        for p in existing_props
                    )
                    
                    if not is_duplicate:
                        if add_glitched_prop(prop_text, enhanced_reasoning, glitch['rating'], glitch['platform']):
                            found_glitches.append(glitch)
                            print(f"Found glitched prop: {prop_text} on {glitch['platform']} (Rating: {glitch['rating']}/10)")
                            print(f"  Reasons: {', '.join(reasons)}")
                    
                    # Update recent scans
                    recent_scans[scan_key] = {
                        'last_scan': datetime.now().isoformat(),
                        'found_glitch': True,
                        'reasons': reasons
                    }
                else:
                    # Update recent scans even if no glitch found
                    recent_scans[scan_key] = {
                        'last_scan': datetime.now().isoformat(),
                        'found_glitch': False,
                        'reasons': reasons
                    }
                
                # Rate limiting - be respectful
                time.sleep(2)  # 2 seconds between players
                
            except Exception as e:
                print(f"Error scanning {player_name}: {e}")
                continue
            
            # Progress update every 5 players (since we're scanning fewer now)
            if scanned_count % 5 == 0:
                print(f"   Progress: {scanned_count}/{len(players_to_scan)} players scanned, {len(found_glitches)} glitches found...")
        
        # Save recent scans
        save_recent_scans(recent_scans)
        
        print(f"Scan complete: {scanned_count} players scanned, {len(found_glitches)} new glitched props found")
        
        return found_glitches
        
    except Exception as e:
        print(f"Error in glitched props scan: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_scan_status():
    """Get the status of the automated scanning system."""
    recent_scans = load_recent_scans()
    total_scanned = len(recent_scans)
    
    # Count how many had glitches found
    glitches_found = sum(1 for scan in recent_scans.values() if scan.get('found_glitch', False))
    
    # Get last scan time
    last_scan_times = [datetime.fromisoformat(scan['last_scan']) for scan in recent_scans.values() if 'last_scan' in scan]
    last_scan = max(last_scan_times) if last_scan_times else None
    
    return {
        'total_scanned': total_scanned,
        'glitches_found': glitches_found,
        'last_scan': last_scan.isoformat() if last_scan else None,
        'scan_interval_minutes': SCAN_INTERVAL_MINUTES,
        'platforms_monitored': PLATFORMS
    }
