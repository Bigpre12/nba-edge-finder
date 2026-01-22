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
SCAN_INTERVAL_MINUTES = 15  # Scan every 15 minutes
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

def scan_active_players_for_glitches():
    """
    Scan all active players for glitched props across platforms.
    This is the main scanning function that runs periodically.
    """
    print(f"[{datetime.now()}] Starting automated glitched props scan...")
    
    try:
        from nba_engine import get_all_active_players
        
        active_players = get_all_active_players()
        if not active_players:
            print("Warning: No active players found")
            return []
        
        print(f"Scanning {len(active_players)} active players across {len(PLATFORMS)} platforms...")
        
        recent_scans = load_recent_scans()
        found_glitches = []
        scanned_count = 0
        
        # Scan top players first (most likely to have lines)
        # Limit to first 50 to avoid rate limits
        players_to_scan = active_players[:50]
        
        for player in players_to_scan:
            player_name = player['full_name']
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
                    prop_text = f"{player_name} {'O' if glitch['line'] < glitch['market_avg'] else 'U'} {glitch['line']} {glitch['stat_type']}"
                    
                    # Check if this prop already exists
                    existing_props = get_glitched_props()
                    is_duplicate = any(
                        p['prop'] == prop_text and p['platform'] == glitch['platform']
                        for p in existing_props
                    )
                    
                    if not is_duplicate:
                        if add_glitched_prop(prop_text, glitch['reasoning'], glitch['rating'], glitch['platform']):
                            found_glitches.append(glitch)
                            print(f"Found glitched prop: {prop_text} on {glitch['platform']} (Rating: {glitch['rating']}/10)")
                    
                    # Update recent scans
                    recent_scans[scan_key] = {
                        'last_scan': datetime.now().isoformat(),
                        'found_glitch': True
                    }
                else:
                    # Update recent scans even if no glitch found
                    recent_scans[scan_key] = {
                        'last_scan': datetime.now().isoformat(),
                        'found_glitch': False
                    }
                
                # Rate limiting - be respectful
                time.sleep(2)  # 2 seconds between players
                
            except Exception as e:
                print(f"Error scanning {player_name}: {e}")
                continue
            
            # Progress update every 10 players
            if scanned_count % 10 == 0:
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
