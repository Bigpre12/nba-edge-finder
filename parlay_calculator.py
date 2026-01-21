"""
Parlay calculator and recommendation system for sports betting.
Calculates payouts and recommends best parlay combinations.
"""
import math
from itertools import combinations
from typing import List, Dict, Tuple

def calculate_parlay_payout(bets: List[Dict], odds_format: str = 'american') -> Dict:
    """
    Calculate parlay payout for a list of bets.
    
    Args:
        bets: List of bet dictionaries with 'odds' and 'probability' keys
        odds_format: 'american' or 'decimal' (default: 'american')
    
    Returns:
        Dictionary with payout information
    """
    if not bets or len(bets) < 2:
        return {
            'valid': False,
            'error': 'Parlay requires at least 2 bets'
        }
    
    # Convert odds to decimal if needed
    decimal_odds = []
    probabilities = []
    
    for bet in bets:
        odds = bet.get('odds', 0)
        prob = bet.get('probability', 0) / 100.0  # Convert percentage to decimal
        
        if odds_format == 'american':
            if odds > 0:
                decimal = (odds / 100) + 1
            else:
                decimal = (100 / abs(odds)) + 1
        else:
            decimal = odds
        
        decimal_odds.append(decimal)
        probabilities.append(prob)
    
    # Calculate combined probability
    combined_prob = math.prod(probabilities)
    
    # Calculate combined odds (decimal)
    combined_decimal = math.prod(decimal_odds)
    
    # Convert back to American odds
    if combined_decimal >= 2:
        american_odds = int((combined_decimal - 1) * 100)
    else:
        american_odds = int(-100 / (combined_decimal - 1))
    
    # Calculate payouts for $100 bet
    payout_100 = (combined_decimal - 1) * 100
    profit_100 = payout_100
    
    return {
        'valid': True,
        'num_bets': len(bets),
        'combined_probability': round(combined_prob * 100, 2),
        'decimal_odds': round(combined_decimal, 3),
        'american_odds': american_odds,
        'payout_per_100': round(payout_100, 2),
        'profit_per_100': round(profit_100, 2),
        'implied_probability': round((1 / combined_decimal) * 100, 2),
        'edge': round((combined_prob * 100) - ((1 / combined_decimal) * 100), 2),
        'expected_value': round((combined_prob * payout_100) - 100, 2)
    }

def find_best_parlays(edges: List[Dict], parlay_size: int, max_recommendations: int = 10) -> List[Dict]:
    """
    Find the best parlay combinations from a list of edges.
    
    Args:
        edges: List of edge dictionaries with 'probability' and 'player' keys
        parlay_size: Size of parlay (2, 3, 4, or 6)
        max_recommendations: Maximum number of recommendations to return
    
    Returns:
        List of recommended parlay dictionaries
    """
    if len(edges) < parlay_size:
        return []
    
    # Filter to only high-probability edges (70%+)
    high_prob_edges = [e for e in edges if e.get('probability', 0) >= 70.0]
    
    if len(high_prob_edges) < parlay_size:
        return []
    
    # Generate all combinations
    all_combinations = list(combinations(high_prob_edges, parlay_size))
    
    # Calculate metrics for each combination
    parlays = []
    for combo in all_combinations:
        # Estimate odds for each bet (assuming -110 for most props)
        bets = []
        for edge in combo:
            # Use actual probability to estimate fair odds
            prob = edge.get('probability', 70) / 100.0
            
            # Convert probability to American odds
            if prob >= 0.5:
                # Favorite
                american_odds = int(-100 * prob / (1 - prob))
            else:
                # Underdog
                american_odds = int(100 * (1 - prob) / prob)
            
            # Standardize to -110 for props (can be adjusted)
            american_odds = -110
            
            bets.append({
                'player': edge.get('player', ''),
                'line': edge.get('line', 0),
                'recommendation': edge.get('recommendation', ''),
                'probability': edge.get('probability', 70),
                'odds': american_odds,
                'edge': edge.get('edge', 0)
            })
        
        # Calculate parlay payout
        payout_info = calculate_parlay_payout(bets)
        
        if payout_info.get('valid'):
            parlays.append({
                'bets': bets,
                'payout': payout_info,
                'total_probability': payout_info['combined_probability'],
                'expected_value': payout_info.get('expected_value', 0),
                'edge': payout_info.get('edge', 0),
                'score': payout_info.get('expected_value', 0) + (payout_info.get('edge', 0) * 10)
            })
    
    # Sort by score (expected value + edge)
    parlays.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top recommendations
    return parlays[:max_recommendations]

def recommend_parlays(edges: List[Dict]) -> Dict:
    """
    Generate parlay recommendations for 2-man, 3-man, 4-man, and 6-man parlays.
    
    Args:
        edges: List of edge dictionaries
    
    Returns:
        Dictionary with recommendations for each parlay size
    """
    recommendations = {
        '2_man': [],
        '3_man': [],
        '4_man': [],
        '6_man': []
    }
    
    # Get recommendations for each size
    recommendations['2_man'] = find_best_parlays(edges, 2, max_recommendations=5)
    recommendations['3_man'] = find_best_parlays(edges, 3, max_recommendations=5)
    recommendations['4_man'] = find_best_parlays(edges, 4, max_recommendations=5)
    recommendations['6_man'] = find_best_parlays(edges, 6, max_recommendations=3)
    
    return recommendations

def format_parlay_display(parlay: Dict) -> Dict:
    """
    Format a parlay for display in the UI.
    
    Args:
        parlay: Parlay dictionary from find_best_parlays
    
    Returns:
        Formatted dictionary for UI display
    """
    bets = parlay.get('bets', [])
    payout = parlay.get('payout', {})
    
    return {
        'bets': [
            {
                'player': bet.get('player', ''),
                'line': bet.get('line', 0),
                'recommendation': bet.get('recommendation', ''),
                'probability': bet.get('probability', 0),
                'odds': bet.get('odds', -110)
            }
            for bet in bets
        ],
        'num_bets': len(bets),
        'combined_probability': payout.get('combined_probability', 0),
        'american_odds': payout.get('american_odds', 0),
        'payout_per_100': payout.get('payout_per_100', 0),
        'expected_value': payout.get('expected_value', 0),
        'edge': payout.get('edge', 0),
        'score': parlay.get('score', 0)
    }
