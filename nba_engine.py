import pandas as pd
from nba_api.stats.endpoints import playergamelog, playercareerstats, teamgamelog, teamdashboardbygeneralsplits
# Note: scoreboard removed - not available in all nba_api versions
from nba_api.stats.static import players, teams
import time
from datetime import datetime, timedelta
import math
import re
from cache_manager import get_cache_key, get_cached_data, set_cached_data
from requests.exceptions import Timeout, ConnectionError, RequestException
import requests

def get_player_id(name):
    """
    Find NBA player ID by full name.
    
    Args:
        name (str): Player's full name (e.g., "LeBron James")
    
    Returns:
        int: Player ID if found, None otherwise
    """
    player_dict = players.find_players_by_full_name(name)
    return player_dict[0]['id'] if player_dict else None

def fetch_recent_games(player_name, stat_type='PTS', season='2023-24', games=10):
    """
    Fetch recent game-by-game statistics for a player.
    Uses caching to reduce API calls.
    
    Args:
        player_name (str): Player's full name
        stat_type (str): Stat type to fetch (default: 'PTS')
        season (str): NBA season (default: '2023-24')
        games (int): Number of recent games to fetch (default: 10)
    
    Returns:
        list: List of dictionaries with game data, or None if error
    """
    # Check cache first
    cache_key = get_cache_key(player_name, stat_type, season, games)
    cached_result = get_cached_data(cache_key)
    if cached_result is not None:
        return cached_result
    
    pid = get_player_id(player_name)
    if not pid:
        return None
    
    # Retry logic for API calls with timeout handling
    max_retries = 5  # Increased from 3
    retry_delay = 3  # Increased from 2
    
    for attempt in range(max_retries):
        try:
            log = playergamelog.PlayerGameLog(player_id=pid, season=season, timeout=60)  # Increased from 30
            df = log.get_data_frames()[0].head(games)
            break  # Success, exit retry loop
        except (Timeout, ConnectionError, RequestException) as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 3, 6, 12, 24
                print(f"   ⚠️ Timeout/connection error for {player_name} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"   ❌ Failed to fetch games for {player_name} after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a timeout-related error even if not caught by Timeout exception
            if 'timeout' in error_str or 'timed out' in error_str or 'read timeout' in error_str:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"   ⚠️ Timeout error for {player_name} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Timeout fetching games for {player_name} after {max_retries} attempts")
                    return None
            else:
                # Non-timeout errors - don't retry
                print(f"   ❌ Error fetching games for {player_name}: {e}")
                return None
    else:
        # If we exhausted retries
        return None
    
    try:
        
        if df.empty:
            return None
        
        # Handle combination stats (e.g., PTS+REB)
        is_combination = '+' in stat_type
        if is_combination:
            components = stat_type.split('+')
        else:
            components = [stat_type]
        
        # Check if all required columns exist
        missing_cols = [col for col in components if col not in df.columns]
        if missing_cols:
            return None
        
        # Return list of games with stat values and additional context
        game_list = []
        for _, row in df.iterrows():
            minutes = row.get('MIN', 0)
            # Convert minutes from "MM:SS" format to float
            if isinstance(minutes, str) and ':' in minutes:
                parts = minutes.split(':')
                minutes_float = float(parts[0]) + float(parts[1]) / 60.0
            else:
                minutes_float = float(minutes) if pd.notna(minutes) else 0
            
            # Calculate stat value (sum for combinations)
            if is_combination:
                stat_value = sum(row.get(col, 0) if pd.notna(row.get(col, 0)) else 0 for col in components)
            else:
                stat_value = row.get(stat_type, 0) if pd.notna(row.get(stat_type, 0)) else 0
            
            game_list.append({
                'game_date': row.get('GAME_DATE', ''),
                'stat_value': stat_value,
                'matchup': row.get('MATCHUP', ''),
                'minutes': minutes_float,
                'did_not_play': minutes_float < 1.0,  # DNP if less than 1 minute
                'wl': row.get('WL', ''),  # Win/Loss
                'fgm': row.get('FGM', 0),  # Field goals made
                'fga': row.get('FGA', 0),  # Field goals attempted
                # Store individual stats for combination calculations
                'pts': row.get('PTS', 0) if pd.notna(row.get('PTS', 0)) else 0,
                'reb': row.get('REB', 0) if pd.notna(row.get('REB', 0)) else 0,
                'ast': row.get('AST', 0) if pd.notna(row.get('AST', 0)) else 0,
                'stl': row.get('STL', 0) if pd.notna(row.get('STL', 0)) else 0,
                'blk': row.get('BLK', 0) if pd.notna(row.get('BLK', 0)) else 0,
                'fg3m': row.get('FG3M', 0) if pd.notna(row.get('FG3M', 0)) else 0,  # 3-pointers made
            })
        
        # Cache the result
        set_cached_data(cache_key, game_list)
        return game_list
    except Exception as e:
        print(f"Error fetching games for {player_name}: {e}")
        return None

def fetch_recent_stats(player_name, stat_type='PTS', season='2023-24', games=5):
    """
    Fetch recent game statistics for a player.
    
    Args:
        player_name (str): Player's full name
        stat_type (str): Stat type to fetch (default: 'PTS')
        season (str): NBA season (default: '2023-24')
        games (int): Number of recent games to average (default: 5)
    
    Returns:
        float: Average of the specified stat over last N games, None if error
    """
    games_list = fetch_recent_games(player_name, stat_type, season, games)
    if not games_list:
        return None
    
    values = [g['stat_value'] for g in games_list]
    return sum(values) / len(values) if values else None

def calculate_streak(player_name, line, stat_type='PTS', season='2023-24', min_streak=2):
    """
    Calculate if a player is on a streak (hitting OVER or UNDER consistently).
    
    Args:
        player_name (str): Player's full name
        line (float): Betting line/projection
        stat_type (str): Stat type to check (default: 'PTS')
        season (str): NBA season (default: '2023-24')
        min_streak (int): Minimum consecutive games to count as streak (default: 2)
    
    Returns:
        dict: Streak information with 'streak_count', 'streak_type' (OVER/UNDER), 'active'
    """
    games_list = fetch_recent_games(player_name, stat_type, season, games=10)
    if not games_list or len(games_list) < min_streak:
        return {'streak_count': 0, 'streak_type': None, 'active': False}
    
    # PlayerGameLog returns games with most recent first, so check from index 0
    current_streak = 0
    streak_type = None
    
    for game in games_list:
        stat_value = game['stat_value']
        
        if stat_value > line:
            hit = 'OVER'
        elif stat_value < line:
            hit = 'UNDER'
        else:
            # Exactly on the line - breaks streak
            break
        
        if streak_type is None:
            streak_type = hit
            current_streak = 1
        elif streak_type == hit:
            current_streak += 1
        else:
            # Streak broken by different result
            break
    
    return {
        'streak_count': current_streak,
        'streak_type': streak_type,
        'active': current_streak >= min_streak
    }

def get_all_active_players():
    """
    Get all currently active NBA players.
    
    Returns:
        list: List of dictionaries with player information (id, full_name)
    """
    try:
        active_players = players.get_active_players()
        return [{'id': p['id'], 'full_name': p['full_name']} for p in active_players]
    except Exception as e:
        print(f"Error fetching active players: {e}")
        return []

def get_season_average(player_id, stat_type='PTS', season='2023-24', player_name=None):
    """
    Get a player's season average for a specific stat.
    Uses retry logic with timeout handling.
    
    Args:
        player_id (int): NBA player ID
        stat_type (str): Stat type to fetch (default: 'PTS')
        season (str): NBA season (default: '2023-24')
        player_name (str): Optional player name for better error messages
    
    Returns:
        float: Season average, None if error or no data
    """
    # Retry logic for API calls with timeout handling
    max_retries = 5  # Increased from 3
    retry_delay = 3  # Increased from 2
    
    for attempt in range(max_retries):
        try:
            # NBA API doesn't support timeout parameter directly
            career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
            df = career_stats.get_data_frames()[0]
            break  # Success, exit retry loop
        except (Timeout, ConnectionError, RequestException) as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 3, 6, 12, 24
                player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
                print(f"   ⚠️ Timeout/connection error for {player_info} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
                print(f"   ❌ Failed to fetch season average for {player_info} after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
            error_type = type(e).__name__
            error_str = str(e).lower()
            
            # Check if it's a timeout-related error
            if 'timeout' in error_str or 'timed out' in error_str or 'read timeout' in error_str or 'connection' in error_str:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"   ⚠️ Timeout error for {player_info} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Timeout fetching season average for {player_info} after {max_retries} attempts")
                    return None
            elif error_type in ['KeyError', 'AttributeError', 'ValueError', 'IndexError']:
                # These are data errors, not network errors - don't retry
                print(f"   ⚠️ {error_type} fetching season average for {player_info}: {e}")
                return None
            else:
                # Unknown error - retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"   ⚠️ Error for {player_info} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Error fetching season average for {player_info} after {max_retries} attempts: {error_type}: {e}")
                    return None
    else:
        # If we exhausted retries
        return None
    
    try:
        
        if df.empty:
            player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
            print(f"   ⚠️ No career stats found for {player_info}")
            return None
        
        # Filter for the specific season
        season_df = df[df['SEASON_ID'] == season]
        
        if season_df.empty:
            player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
            print(f"   ⚠️ No data for {player_info} in season {season}")
            return None
        
        if stat_type not in season_df.columns:
            player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
            print(f"   ⚠️ Stat '{stat_type}' not available for {player_info}")
            return None
        
        # Get the average for the season
        avg = season_df[stat_type].mean()
        if pd.notna(avg):
            return round(avg, 1)
        else:
            player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
            print(f"   ⚠️ Average is NaN for {player_info} ({stat_type})")
            return None
    except KeyError as e:
        player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
        print(f"   ⚠️ KeyError fetching season average for {player_info}: {e}")
        return None
    except AttributeError as e:
        player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
        print(f"   ⚠️ AttributeError fetching season average for {player_info}: {e}")
        return None
    except Exception as e:
        player_info = f"{player_name} (ID: {player_id})" if player_name else f"ID: {player_id}"
        error_type = type(e).__name__
        print(f"   ❌ Error fetching season average for {player_info} ({stat_type}, {season}): {error_type}: {e}")
        import traceback
        # Only print full traceback for unexpected errors
        if error_type not in ['KeyError', 'AttributeError', 'ValueError']:
            traceback.print_exc()
        return None

def generate_projections_from_active_players(stat_type='PTS', season='2023-24', min_games=10, use_season_avg=True):
    """
    Generate projections for all active players based on their season averages.
    
    Args:
        stat_type (str): Stat type to generate projections for (default: 'PTS')
        season (str): NBA season (default: '2023-24')
        min_games (int): Minimum games played to include player (default: 10)
    
    Returns:
        dict: Dictionary mapping player names to their season averages as projections
    """
    active_players = get_all_active_players()
    projections = {}
    
    print(f"📊 Fetching projections for {len(active_players)} active players (stat: {stat_type})...")
    
    successful = 0
    failed = 0
    
    for i, player in enumerate(active_players):
        player_name = player['full_name']
        player_id = player['id']
        
        try:
            # Get season average as projection
            # For combination stats, get_season_average handles it
            avg = get_season_average(player_id, stat_type=stat_type, season=season, player_name=player_name)
            
            if avg is not None:
                # Use season average as the projection line
                projections[player_name] = round(avg, 1)
                successful += 1
            else:
                failed += 1
                # Only log if it's a real error (not just no data for this season)
                # The get_season_average function already logs specific issues
        except Exception as e:
            error_type = type(e).__name__
            print(f"   ❌ Exception getting {player_name} (ID: {player_id}): {error_type}: {e}")
            failed += 1
            continue
        
        # Rate limiting - be more conservative with bulk operations to avoid timeouts
        if (i + 1) % 10 == 0:
            print(f"   📈 Progress: {i + 1}/{len(active_players)} players processed ({successful} successful, {failed} failed)...")
            time.sleep(5)  # Longer delay every 10 players to avoid rate limits and timeouts
        elif (i + 1) % 5 == 0:
            time.sleep(2.5)  # Medium delay every 5 players
        else:
            time.sleep(1.5)  # Increased delay between players to reduce timeout risk
    
    print(f"✅ Generated projections for {len(projections)} players ({successful} successful, {failed} failed)")
    if len(projections) < 10:
        print(f"⚠️ WARNING: Only {len(projections)} players loaded. This is unusually low.")
        print(f"   Check NBA API availability and network connection.")
    
    return projections

def get_player_performance_factors(player_name, stat_type='PTS', season='2023-24'):
    """
    Analyze performance factors that affect a player's performance.
    
    Args:
        player_name (str): Player's full name
        stat_type (str): Stat type to analyze (default: 'PTS')
        season (str): NBA season (default: '2023-24')
    
    Returns:
        dict: Dictionary with performance factors analysis
    """
    games_list = fetch_recent_games(player_name, stat_type, season, games=10)
    if not games_list:
        return None
    
    # Calculate minutes trends
    minutes_list = [g['minutes'] for g in games_list]
    recent_minutes = minutes_list[:5] if len(minutes_list) >= 5 else minutes_list
    older_minutes = minutes_list[5:10] if len(minutes_list) >= 10 else []
    
    recent_min_avg = sum(recent_minutes) / len(recent_minutes) if recent_minutes else 0
    older_min_avg = sum(older_minutes) / len(older_minutes) if older_minutes else recent_min_avg
    
    # Detect injuries (DNP games)
    dnp_games = [g for g in games_list if g['did_not_play']]
    recent_dnp = len([g for g in games_list[:3] if g['did_not_play']])
    
    # Detect rotation changes (significant minutes variance)
    minutes_variance = pd.Series(minutes_list).std() if len(minutes_list) > 1 else 0
    rotation_change = abs(recent_min_avg - older_min_avg) > 5 if older_minutes else False
    
    # Performance trend
    stat_values = [g['stat_value'] for g in games_list]
    recent_stats = stat_values[:5] if len(stat_values) >= 5 else stat_values
    older_stats = stat_values[5:10] if len(stat_values) >= 10 else []
    
    recent_stat_avg = sum(recent_stats) / len(recent_stats) if recent_stats else 0
    older_stat_avg = sum(older_stats) / len(older_stats) if older_stats else recent_stat_avg
    performance_trend = 'up' if recent_stat_avg > older_stat_avg + 2 else 'down' if recent_stat_avg < older_stat_avg - 2 else 'stable'
    
    # Shooting efficiency trend
    fg_pct_recent = []
    for g in games_list[:5]:
        if g.get('fga', 0) > 0:
            fg_pct = g.get('fgm', 0) / g.get('fga', 1)
            fg_pct_recent.append(fg_pct)
    
    avg_fg_pct = sum(fg_pct_recent) / len(fg_pct_recent) if fg_pct_recent else None
    
    return {
        'recent_minutes_avg': round(recent_min_avg, 1),
        'older_minutes_avg': round(older_min_avg, 1) if older_minutes else None,
        'minutes_trend': 'up' if recent_min_avg > older_min_avg + 2 else 'down' if recent_min_avg < older_min_avg - 2 else 'stable',
        'minutes_variance': round(minutes_variance, 1),
        'dnp_count': len(dnp_games),
        'recent_dnp': recent_dnp > 0,
        'injury_risk': recent_dnp > 0 or len(dnp_games) > 0,
        'rotation_change': rotation_change,
        'performance_trend': performance_trend,
        'recent_stat_avg': round(recent_stat_avg, 1),
        'older_stat_avg': round(older_stat_avg, 1) if older_stats else None,
        'shooting_efficiency': round(avg_fg_pct * 100, 1) if avg_fg_pct else None,
            'games_analyzed': len(games_list)
    }

def calculate_advanced_metrics(games_list):
    """
    Calculate advanced metrics: TS%, efficiency, consistency.
    Oracle focuses on these, not basic PPG.
    """
    if not games_list:
        return None
    
    total_points = sum(g['stat_value'] for g in games_list)
    total_fgm = sum(g.get('fgm', 0) for g in games_list)
    total_fga = sum(g.get('fga', 0) for g in games_list)
    total_minutes = sum(g['minutes'] for g in games_list)
    
    # True Shooting Percentage (simplified - would need 3PA and FTA for full TS%)
    fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0
    
    # Points per 36 minutes (normalized efficiency)
    points_per_36 = (total_points / total_minutes * 36) if total_minutes > 0 else 0
    
    # Consistency (coefficient of variation)
    stat_values = [g['stat_value'] for g in games_list if g['stat_value'] > 0]
    if len(stat_values) > 1:
        mean_val = sum(stat_values) / len(stat_values)
        variance = sum((x - mean_val) ** 2 for x in stat_values) / len(stat_values)
        std_dev = math.sqrt(variance)
        consistency = (std_dev / mean_val * 100) if mean_val > 0 else 100
    else:
        consistency = 0
    
    return {
        'fg_pct': round(fg_pct, 1),
        'points_per_36': round(points_per_36, 1),
        'consistency': round(consistency, 1),  # Lower is better
        'games_with_data': len([g for g in games_list if g.get('fga', 0) > 0])
    }

def calculate_oracle_confidence(edge_data, factors, streak_info=None):
    """
    Calculate confidence tier (1-5 units) based on Oracle methodology.
    Factors: injury risk (-2), rotation change (-1), strong streak (+1), 
    large edge (+1), consistency (+0.5)
    """
    confidence = 2.0  # Base confidence
    
    if factors:
        # Injury risk severely reduces confidence
        if factors.get('injury_risk'):
            confidence -= 2.0
        if factors.get('recent_dnp'):
            confidence -= 1.5
        
        # Rotation changes reduce confidence
        if factors.get('rotation_change'):
            confidence -= 1.0
        
        # Performance trends
        if factors.get('performance_trend') == 'up':
            confidence += 0.5
        elif factors.get('performance_trend') == 'down':
            confidence -= 0.5
        
        # Consistency bonus
        if factors.get('minutes_variance', 100) < 5:
            confidence += 0.5
    
    # Streak bonus
    if streak_info and streak_info.get('active'):
        streak_count = streak_info.get('streak_count', 0)
        if streak_count >= 4:
            confidence += 1.0
        elif streak_count >= 3:
            confidence += 0.5
    
    # Edge size bonus
    diff = edge_data.get('difference', 0)
    if diff >= 5:
        confidence += 1.0
    elif diff >= 3:
        confidence += 0.5
    
    # Clamp between 1 and 5
    confidence = max(1.0, min(5.0, confidence))
    return round(confidence, 1)

def generate_oracle_verdict(edge_data, factors, streak_info=None):
    """
    Generate Oracle-style verdict with sharp angle, key data point, risk factor.
    """
    player = edge_data['player']
    line = edge_data['line']
    avg = edge_data['average']
    diff = edge_data['difference']
    recommendation = edge_data['recommendation']
    confidence = calculate_oracle_confidence(edge_data, factors, streak_info)
    
    # Sharp Angle
    sharp_angle = ""
    if streak_info and streak_info.get('active'):
        sharp_angle = f"{streak_info['streak_count']}-game {streak_info['streak_type']} streak. Market hasn't adjusted."
    elif diff >= 4:
        sharp_angle = f"L5 average ({avg}) vs line ({line}) = {diff:.1f}pt edge. Line is stale."
    else:
        sharp_angle = f"Recent form ({avg}) diverging from projection ({line})."
    
    # Key Data Point
    key_data = ""
    if factors:
        if factors.get('injury_risk'):
            key_data = f"⚠️ {factors.get('dnp_count', 0)} DNP games. Injury risk."
        elif factors.get('rotation_change'):
            key_data = f"🔄 Rotation shift: {factors.get('recent_minutes_avg', 0):.1f} min (was {factors.get('older_minutes_avg', 0):.1f})."
        elif factors.get('performance_trend') == 'up':
            key_data = f"📈 Performance trending up: {factors.get('recent_stat_avg', 0):.1f} vs {factors.get('older_stat_avg', 0):.1f} earlier."
        else:
            key_data = f"L5: {avg} | Line: {line} | Edge: {diff:.1f}pts"
    else:
        key_data = f"L5: {avg} | Line: {line} | Edge: {diff:.1f}pts"
    
    # Risk Factor
    risk_factor = ""
    if factors:
        if factors.get('injury_risk'):
            risk_factor = "Injury/rest risk. Minutes could be limited."
        elif factors.get('rotation_change'):
            risk_factor = "Rotation instability. Minutes variance = {:.1f}.".format(factors.get('minutes_variance', 0))
        elif factors.get('performance_trend') == 'down':
            risk_factor = "Performance declining. Recent form may not sustain."
        else:
            risk_factor = "Standard variance. Edge could normalize."
    else:
        risk_factor = "Standard variance. Edge could normalize."
    
    return {
        'player': player,
        'line': line,
        'verdict': f"{recommendation} {line:.1f}",
        'confidence': confidence,
        'sharp_angle': sharp_angle,
        'key_data': key_data,
        'risk_factor': risk_factor,
        'edge': edge_data
    }

def calculate_hit_probability(edge_data, factors, streak_info=None):
    """
    Calculate probability percentage (0-100%) that prop will hit.
    Converts confidence units to probability.
    """
    # Base probability from confidence units (1-5 scale)
    confidence = calculate_oracle_confidence(edge_data, factors, streak_info)
    
    # Convert 1-5 units to 50-90% probability range
    # 1 unit = 50%, 5 units = 90%
    base_prob = 50 + (confidence - 1) * 10
    
    # Adjustments based on factors
    if factors:
        # Injury risk reduces probability
        if factors.get('injury_risk'):
            base_prob -= 15
        if factors.get('recent_dnp'):
            base_prob -= 10
        
        # Strong trends increase probability
        if factors.get('performance_trend') == 'up' and edge_data.get('recommendation') == 'OVER':
            base_prob += 5
        elif factors.get('performance_trend') == 'down' and edge_data.get('recommendation') == 'UNDER':
            base_prob += 5
        
        # Consistency bonus
        if factors.get('minutes_variance', 100) < 5:
            base_prob += 3
    
    # Streak bonus
    if streak_info and streak_info.get('active'):
        streak_count = streak_info.get('streak_count', 0)
        if streak_count >= 4:
            base_prob += 8
        elif streak_count >= 3:
            base_prob += 5
    
    # Large edge bonus
    diff = edge_data.get('difference', 0)
    if diff >= 5:
        base_prob += 7
    elif diff >= 3:
        base_prob += 4
    
    # Clamp between 50% and 95%
    base_prob = max(50, min(95, base_prob))
    return round(base_prob, 1)

def generate_high_probability_reasoning(edge_data, factors, streak_info=None, probability=None):
    """
    Generate reasoning for why a prop has high probability of hitting.
    """
    if probability is None:
        probability = calculate_hit_probability(edge_data, factors, streak_info)
    
    reasons = []
    
    # Edge size reasoning
    diff = edge_data.get('difference', 0)
    if diff >= 5:
        reasons.append(f"Massive {diff:.1f}pt edge - L5 average ({edge_data.get('average', 0):.1f}) well above/below line ({edge_data.get('line', 0):.1f})")
    elif diff >= 3:
        reasons.append(f"Strong {diff:.1f}pt edge indicates line mispricing")
    
    # Streak reasoning
    if streak_info and streak_info.get('active'):
        streak_count = streak_info.get('streak_count', 0)
        reasons.append(f"{streak_count}-game {streak_info['streak_type']} streak - momentum factor")
    
    # Performance trend reasoning
    if factors:
        if factors.get('performance_trend') == 'up' and edge_data.get('recommendation') == 'OVER':
            reasons.append(f"Performance trending up ({factors.get('recent_stat_avg', 0):.1f} vs {factors.get('older_stat_avg', 0):.1f})")
        elif factors.get('performance_trend') == 'down' and edge_data.get('recommendation') == 'UNDER':
            reasons.append(f"Performance declining - favorable for UNDER")
        
        # Consistency reasoning
        if factors.get('minutes_variance', 100) < 5:
            reasons.append("High minutes consistency - predictable usage")
        
        # Matchup reasoning (if available)
        if not factors.get('injury_risk') and not factors.get('rotation_change'):
            reasons.append("No injury/rotation concerns - full minutes expected")
    
    # Default reasoning if none found
    if not reasons:
        reasons.append(f"Statistical edge ({diff:.1f}pts) with {probability:.0f}% confidence")
    
    return " | ".join(reasons)

def format_for_prizepicks(edge_data):
    """
    Format prop for PrizePicks/Underdog style (More/Less instead of Over/Under).
    """
    recommendation = edge_data.get('recommendation', 'OVER')
    line = edge_data.get('line', 0)
    stat_type = edge_data.get('stat_type', 'PTS')
    
    # Convert OVER/UNDER to More/Less
    prizepicks_direction = "More" if recommendation == "OVER" else "Less"
    
    return {
        'player': edge_data.get('player'),
        'direction': prizepicks_direction,
        'line': line,
        'stat_type': stat_type,
        'display': f"{edge_data.get('player')} {prizepicks_direction} {line:.1f} {stat_type}",
        'original': edge_data
    }

def filter_high_probability_props(edges, min_probability=70.0):
    """
    Filter edges with 70%+ hit probability and format for PrizePicks.
    """
    high_prob_props = []
    
    for edge in edges:
        factors = edge.get('factors', {})
        streak_info = edge.get('streak', {}) if edge.get('streak', {}).get('active') else None
        
        probability = calculate_hit_probability(edge, factors, streak_info)
        
        if probability >= min_probability:
            reasoning = generate_high_probability_reasoning(edge, factors, streak_info, probability)
            prizepicks_format = format_for_prizepicks(edge)
            
            high_prob_props.append({
                'edge': edge,
                'probability': probability,
                'reasoning': reasoning,
                'prizepicks': prizepicks_format,
                'oracle': edge.get('oracle', {}),
                'beneficiary': edge.get('beneficiary')
            })
    
    # Sort by probability (highest first)
    high_prob_props.sort(key=lambda x: x.get('probability', 0), reverse=True)
    
    return high_prob_props

def extract_team_from_matchup(matchup_str):
    """
    Extract opponent team abbreviation from matchup string.
    Format: "LAL @ BOS" or "BOS vs. LAL"
    """
    if not matchup_str:
        return None
    
    # Remove team's own abbreviation (usually at start)
    # Match pattern like "LAL @ BOS" or "vs. BOS"
    patterns = [
        r'@\s*([A-Z]{3})',  # @ BOS
        r'vs\.\s*([A-Z]{3})',  # vs. BOS
        r'vs\s+([A-Z]{3})',  # vs BOS
    ]
    
    for pattern in patterns:
        match = re.search(pattern, matchup_str)
        if match:
            return match.group(1)
    
    return None

def get_team_defensive_ranking(team_abbr, stat_type='PTS', season='2023-24'):
    """
    Get team's defensive ranking for a specific stat.
    Returns ranking (1-30, lower is worse defense) and average allowed.
    """
    try:
        # Use correct method to find team by abbreviation
        team_list = teams.find_teams_by_abbreviation(team_abbr)
        if not team_list or len(team_list) == 0:
            return None
        
        team_id = team_list[0]['id']
        
        # Get team game log to calculate defensive stats
        team_log = teamgamelog.TeamGameLog(team_id=team_id, season=season)
        df = team_log.get_data_frames()[0]
        
        if df.empty:
            return None
        
        # Calculate average points allowed (for PTS stat)
        if stat_type == 'PTS':
            avg_allowed = df['PTS'].mean() if 'PTS' in df.columns else None
            if avg_allowed is None:
                return None
            
            # This is simplified - in reality would need all teams to rank
            # For now, return relative ranking estimate
            # Higher avg_allowed = worse defense
            return {
                'avg_allowed': round(avg_allowed, 1),
                'ranking_estimate': 'top-10' if avg_allowed < 110 else 'bottom-10' if avg_allowed > 115 else 'middle',
                'is_weak': avg_allowed > 115
            }
        
        return None
    except Exception as e:
        # Suppress error logging for this function - it's not critical
        # print(f"Error getting defensive stats for {team_abbr}: {e}")
        return None

def analyze_player_vs_team_matchup(player_name, opponent_team, stat_type='PTS', season='2023-24'):
    """
    Analyze how player performs against specific opponent.
    Returns historical performance vs that team.
    """
    games_list = fetch_recent_games(player_name, stat_type, season, games=82)
    if not games_list:
        return None
    
    # Filter games vs this opponent
    vs_opponent = []
    for game in games_list:
        matchup = game.get('matchup', '')
        if opponent_team and opponent_team in matchup:
            vs_opponent.append(game)
    
    if not vs_opponent:
        return None
    
    # Calculate average vs opponent
    stat_values = [g['stat_value'] for g in vs_opponent]
    avg_vs_opponent = sum(stat_values) / len(stat_values) if stat_values else 0
    
    # Compare to overall average
    overall_avg = fetch_recent_stats(player_name, stat_type, season, games=10)
    
    return {
        'avg_vs_opponent': round(avg_vs_opponent, 1),
        'overall_avg': round(overall_avg, 1) if overall_avg else None,
        'games_vs_opponent': len(vs_opponent),
        'advantage': round(avg_vs_opponent - overall_avg, 1) if overall_avg else None
    }

def identify_statistical_beneficiary(edge_data, stat_type='PTS', season='2023-24'):
    """
    Phase 2: Identify the Statistical Beneficiary - player with biggest mismatch advantage.
    Returns Phase 2 micro-analysis report.
    """
    player_name = edge_data['player']
    line = edge_data['line']
    projection = edge_data['average']
    recommendation = edge_data['recommendation']
    
    # Get recent games to find opponent
    games_list = fetch_recent_games(player_name, stat_type, season, games=5)
    if not games_list:
        return None
    
    # Get next/current opponent from most recent game
    most_recent = games_list[0] if games_list else None
    if not most_recent:
        return None
    
    matchup = most_recent.get('matchup', '')
    opponent_team = extract_team_from_matchup(matchup)
    
    # Get player position (simplified - would need roster data)
    # For now, infer from stat type
    position = "Guard" if stat_type == 'PTS' else "Forward/Center"
    
    # Analyze matchup
    matchup_analysis = None
    defensive_stats = None
    mismatch_description = ""
    
    if opponent_team:
        try:
            matchup_analysis = analyze_player_vs_team_matchup(player_name, opponent_team, stat_type, season)
            defensive_stats = get_team_defensive_ranking(opponent_team, stat_type, season)
            
            if defensive_stats and defensive_stats.get('is_weak'):
                mismatch_description = f"Facing {opponent_team} - {defensive_stats.get('ranking_estimate', 'weak')} defense allowing {defensive_stats.get('avg_allowed', 0):.1f} {stat_type}/game"
            elif matchup_analysis and matchup_analysis.get('advantage', 0) > 2:
                mismatch_description = f"Historical advantage vs {opponent_team}: +{matchup_analysis['advantage']:.1f} {stat_type} above average"
            else:
                mismatch_description = f"Facing {opponent_team} - standard matchup"
        except Exception:
            # If matchup analysis fails, just use basic description
            mismatch_description = f"Facing {opponent_team} - standard matchup"
    
    # Consensus expectation (current line)
    consensus_expectation = line
    
    # Projection vs consensus
    projection_diff = projection - consensus_expectation
    projection_direction = "OVER" if projection > consensus_expectation else "UNDER"
    
    # Confidence logic
    confidence_logic = ""
    if defensive_stats and defensive_stats.get('is_weak'):
        confidence_logic = f"{opponent_team} allows {defensive_stats.get('avg_allowed', 0):.1f} {stat_type}/game (weak defense)."
    elif matchup_analysis and matchup_analysis.get('advantage', 0) > 2:
        confidence_logic = f"Player averages {matchup_analysis['avg_vs_opponent']:.1f} vs {opponent_team} (vs {matchup_analysis['overall_avg']:.1f} overall)."
    elif edge_data.get('difference', 0) > 3:
        confidence_logic = f"L5 average ({projection:.1f}) diverges {abs(projection_diff):.1f}pts from line ({consensus_expectation:.1f})."
    else:
        confidence_logic = f"Recent form ({projection:.1f}) vs market expectation ({consensus_expectation:.1f})."
    
    return {
        'player': player_name,
        'position': position,
        'mismatch': mismatch_description,
        'consensus_expectation': consensus_expectation,
        'projection': projection,
        'projection_direction': projection_direction,
        'projection_diff': round(projection_diff, 1),
        'confidence_logic': confidence_logic,
        'opponent': opponent_team,
        'matchup_data': matchup_analysis,
        'defensive_data': defensive_stats
    }

def check_for_edges(projections, threshold=2.0, stat_type='PTS', season='2023-24', include_streaks=True, min_streak=2, include_factors=True):
    """
    Check for betting edges by comparing recent performance vs projections.
    Also tracks active streaks where players consistently hit OVER/UNDER.
    
    Args:
        projections (dict): Dictionary mapping player names to betting lines
        threshold (float): Minimum difference to consider an edge (default: 2.0)
        stat_type (str): Stat type to check (default: 'PTS')
        season (str): NBA season (default: '2023-24')
        include_streaks (bool): Whether to include streak information (default: True)
        min_streak (int): Minimum consecutive games for a streak (default: 2)
    
    Returns:
        dict: Dictionary with 'edges' list and 'streaks' list
    """
    edges = []
    streaks = []
    
    for player_name, line in projections.items():
        avg = fetch_recent_stats(player_name, stat_type=stat_type, season=season)
        
        # Get performance factors
        factors = None
        if include_factors:
            factors = get_player_performance_factors(player_name, stat_type, season)
        
        # Check for edges
        if avg is not None:
            diff = avg - line
            if abs(diff) > threshold:
                status = "OVER" if avg > line else "UNDER"
                edge_data = {
                    'player': player_name,
                    'line': line,
                    'average': round(avg, 1),
                    'difference': round(abs(diff), 1),
                    'recommendation': status,
                    'stat_type': stat_type
                }
                
                # Add streak info if requested
                if include_streaks:
                    streak_info = calculate_streak(player_name, line, stat_type, season, min_streak)
                    edge_data['streak'] = streak_info
                
                # Add performance factors
                if factors:
                    edge_data['factors'] = factors
                    # Add advanced metrics
                    games_list = fetch_recent_games(player_name, stat_type, season, games=5)
                    if games_list:
                        advanced = calculate_advanced_metrics(games_list)
                        if advanced:
                            edge_data['advanced_metrics'] = advanced
                
                # Generate Oracle verdict
                oracle_verdict = generate_oracle_verdict(edge_data, factors, streak_info if include_streaks else None)
                edge_data['oracle'] = oracle_verdict
                
                # Phase 2: Statistical Beneficiary analysis
                beneficiary_analysis = identify_statistical_beneficiary(edge_data, stat_type, season)
                if beneficiary_analysis:
                    edge_data['beneficiary'] = beneficiary_analysis
                
                edges.append(edge_data)
        
        # Check for streaks (even if not an edge)
        if include_streaks:
            streak_info = calculate_streak(player_name, line, stat_type, season, min_streak)
            if streak_info['active']:
                # Get average for streak display
                avg = fetch_recent_stats(player_name, stat_type=stat_type, season=season)
                streak_data = {
                    'player': player_name,
                    'line': line,
                    'average': round(avg, 1) if avg else None,
                    'streak_count': streak_info['streak_count'],
                    'streak_type': streak_info['streak_type'],
                    'stat_type': stat_type
                }
                
                # Add performance factors
                if factors:
                    streak_data['factors'] = factors
                    # Add advanced metrics
                    games_list = fetch_recent_games(player_name, stat_type, season, games=5)
                    if games_list:
                        advanced = calculate_advanced_metrics(games_list)
                        if advanced:
                            streak_data['advanced_metrics'] = advanced
                
                # Generate Oracle verdict for streaks
                oracle_verdict = generate_oracle_verdict({
                    'player': player_name,
                    'line': line,
                    'average': round(avg, 1) if avg else 0,
                    'difference': abs(avg - line) if avg else 0,
                    'recommendation': streak_info['streak_type']
                }, factors, streak_info)
                streak_data['oracle'] = oracle_verdict
                
                # Only add if not already in edges (avoid duplicates)
                if not any(e['player'] == player_name for e in edges):
                    streaks.append(streak_data)
        
        # Prevent hitting API rate limits
        time.sleep(1)
    
    return {
        'edges': edges,
        'streaks': streaks
    }
