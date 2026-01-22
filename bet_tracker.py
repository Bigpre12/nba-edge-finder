"""
Bet tracking module for recording and analyzing betting history.
Stores bets with timestamps, odds, results, and calculates ROI.
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

BETS_FILE = 'bets_history.json'

def load_bets() -> List[Dict]:
    """Load all bets from file."""
    if os.path.exists(BETS_FILE):
        try:
            with open(BETS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading bets: {e}")
            return []
    return []

def save_bets(bets: List[Dict]) -> bool:
    """Save bets to file."""
    try:
        with open(BETS_FILE, 'w') as f:
            json.dump(bets, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving bets: {e}")
        return False

def add_bet(
    player: str,
    prop_type: str,
    line: float,
    pick: str,  # OVER or UNDER
    odds_placed: int,  # American odds at time of bet
    stake: float,
    platform: str = 'Unknown',
    confidence_grade: str = None,
    confidence_score: float = None
) -> Optional[Dict]:
    """
    Add a new bet to history.
    
    Args:
        player: Player name
        prop_type: Stat type (PTS, REB, AST, etc.)
        line: Betting line
        pick: OVER or UNDER
        odds_placed: American odds when bet was placed
        stake: Amount wagered
        platform: Betting platform
        confidence_grade: Grade from system (A+, A, B+, etc.)
        confidence_score: Score from system (0-100)
    
    Returns:
        The created bet dict or None on error
    """
    bets = load_bets()
    
    bet = {
        'id': str(uuid.uuid4())[:8],
        'player': player,
        'prop_type': prop_type,
        'line': line,
        'pick': pick,
        'odds_placed': odds_placed,
        'odds_closing': None,  # Updated when game starts/closes
        'stake': stake,
        'platform': platform,
        'confidence_grade': confidence_grade,
        'confidence_score': confidence_score,
        'time_placed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'game_date': datetime.now().strftime('%Y-%m-%d'),
        'result': None,  # WIN, LOSS, PUSH, PENDING
        'actual_stat': None,
        'payout': None,
        'profit': None,
        'settled_at': None
    }
    
    bets.append(bet)
    if save_bets(bets):
        return bet
    return None

def update_closing_odds(bet_id: str, closing_odds: int) -> Optional[Dict]:
    """Update the closing odds for a bet."""
    bets = load_bets()
    for bet in bets:
        if bet['id'] == bet_id:
            bet['odds_closing'] = closing_odds
            save_bets(bets)
            return bet
    return None

def settle_bet(bet_id: str, actual_stat: float, closing_odds: int = None) -> Optional[Dict]:
    """
    Settle a bet with the actual result.
    
    Args:
        bet_id: Bet ID
        actual_stat: Actual stat value achieved
        closing_odds: Closing odds (optional, updates if provided)
    
    Returns:
        Updated bet dict or None
    """
    bets = load_bets()
    for bet in bets:
        if bet['id'] == bet_id:
            bet['actual_stat'] = actual_stat
            bet['settled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if closing_odds:
                bet['odds_closing'] = closing_odds
            
            # Determine result
            line = bet['line']
            pick = bet['pick']
            
            if actual_stat > line:
                bet['result'] = 'WIN' if pick == 'OVER' else 'LOSS'
            elif actual_stat < line:
                bet['result'] = 'WIN' if pick == 'UNDER' else 'LOSS'
            else:
                bet['result'] = 'PUSH'
            
            # Calculate payout and profit
            stake = bet['stake']
            odds = bet['odds_placed']
            
            if bet['result'] == 'WIN':
                if odds > 0:
                    payout = stake + (stake * odds / 100)
                else:
                    payout = stake + (stake * 100 / abs(odds))
                bet['payout'] = round(payout, 2)
                bet['profit'] = round(payout - stake, 2)
            elif bet['result'] == 'PUSH':
                bet['payout'] = stake
                bet['profit'] = 0
            else:  # LOSS
                bet['payout'] = 0
                bet['profit'] = -stake
            
            save_bets(bets)
            return bet
    return None

def get_bets_by_date(date_str: str) -> List[Dict]:
    """Get all bets for a specific date."""
    bets = load_bets()
    return [b for b in bets if b.get('game_date') == date_str]

def get_yesterdays_bets() -> List[Dict]:
    """Get all bets from yesterday."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return get_bets_by_date(yesterday)

def get_todays_bets() -> List[Dict]:
    """Get all bets from today."""
    today = datetime.now().strftime('%Y-%m-%d')
    return get_bets_by_date(today)

def get_pending_bets() -> List[Dict]:
    """Get all unsettled bets."""
    bets = load_bets()
    return [b for b in bets if b.get('result') is None or b.get('result') == 'PENDING']

def get_recent_bets(days: int = 7) -> List[Dict]:
    """Get bets from the last N days."""
    bets = load_bets()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    return [b for b in bets if b.get('game_date', '') >= cutoff]

def calculate_roi(bets: List[Dict]) -> Dict:
    """
    Calculate ROI and stats for a list of bets.
    
    Returns:
        Dict with total_stake, total_profit, roi_pct, record, etc.
    """
    if not bets:
        return {
            'total_bets': 0,
            'settled_bets': 0,
            'pending_bets': 0,
            'wins': 0,
            'losses': 0,
            'pushes': 0,
            'total_stake': 0,
            'total_profit': 0,
            'roi_pct': 0,
            'win_rate': 0,
            'avg_odds_placed': 0,
            'avg_odds_closing': 0,
            'clv': 0  # Closing Line Value
        }
    
    settled = [b for b in bets if b.get('result') and b['result'] != 'PENDING']
    pending = [b for b in bets if not b.get('result') or b['result'] == 'PENDING']
    
    wins = len([b for b in settled if b['result'] == 'WIN'])
    losses = len([b for b in settled if b['result'] == 'LOSS'])
    pushes = len([b for b in settled if b['result'] == 'PUSH'])
    
    total_stake = sum(b.get('stake', 0) for b in settled)
    total_profit = sum(b.get('profit', 0) for b in settled if b.get('profit') is not None)
    
    roi_pct = (total_profit / total_stake * 100) if total_stake > 0 else 0
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    # Calculate average odds
    odds_placed = [b.get('odds_placed', -110) for b in settled]
    odds_closing = [b.get('odds_closing') for b in settled if b.get('odds_closing')]
    
    avg_odds_placed = sum(odds_placed) / len(odds_placed) if odds_placed else 0
    avg_odds_closing = sum(odds_closing) / len(odds_closing) if odds_closing else 0
    
    # Calculate CLV (Closing Line Value) - measures if you beat the closing line
    clv_total = 0
    clv_count = 0
    for b in settled:
        if b.get('odds_placed') and b.get('odds_closing'):
            placed = b['odds_placed']
            closing = b['odds_closing']
            # Convert to implied probability to compare
            if placed < 0:
                implied_placed = abs(placed) / (abs(placed) + 100)
            else:
                implied_placed = 100 / (placed + 100)
            
            if closing < 0:
                implied_closing = abs(closing) / (abs(closing) + 100)
            else:
                implied_closing = 100 / (closing + 100)
            
            # CLV = closing implied - placed implied (positive = got better odds)
            clv_total += (implied_closing - implied_placed) * 100
            clv_count += 1
    
    clv = clv_total / clv_count if clv_count > 0 else 0
    
    return {
        'total_bets': len(bets),
        'settled_bets': len(settled),
        'pending_bets': len(pending),
        'wins': wins,
        'losses': losses,
        'pushes': pushes,
        'total_stake': round(total_stake, 2),
        'total_profit': round(total_profit, 2),
        'roi_pct': round(roi_pct, 2),
        'win_rate': round(win_rate, 1),
        'avg_odds_placed': round(avg_odds_placed),
        'avg_odds_closing': round(avg_odds_closing) if avg_odds_closing else None,
        'clv': round(clv, 2)
    }

def delete_bet(bet_id: str) -> bool:
    """Delete a bet by ID."""
    bets = load_bets()
    original_len = len(bets)
    bets = [b for b in bets if b['id'] != bet_id]
    if len(bets) < original_len:
        return save_bets(bets)
    return False

def get_all_bets() -> List[Dict]:
    """Get all bets."""
    return load_bets()
