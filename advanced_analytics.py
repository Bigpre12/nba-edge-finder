"""
Advanced analytics for sports betting: Market edge, EV calculation, matchup grades, and tactical filters.
"""
import math
from typing import Dict, List, Optional

def calculate_expected_value(probability: float, odds: int, bet_amount: float = 100) -> Dict:
    """
    Calculate Expected Value (EV) for a bet.
    
    Args:
        probability: Win probability (0-100)
        odds: American odds (e.g., -110)
        bet_amount: Bet size in dollars (default: 100)
    
    Returns:
        Dictionary with EV metrics
    """
    prob_decimal = probability / 100.0
    
    # Convert American odds to decimal
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1
    
    # Calculate payout
    payout = bet_amount * (decimal_odds - 1)
    
    # Calculate EV
    ev = (prob_decimal * payout) - ((1 - prob_decimal) * bet_amount)
    ev_percentage = (ev / bet_amount) * 100
    
    # Calculate market edge
    implied_prob = 1 / decimal_odds
    market_edge = (prob_decimal - implied_prob) * 100
    
    # Kelly Criterion (fractional)
    kelly_fraction = (prob_decimal * decimal_odds - 1) / (decimal_odds - 1)
    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
    
    return {
        'ev': round(ev, 2),
        'ev_percentage': round(ev_percentage, 2),
        'market_edge': round(market_edge, 2),
        'implied_probability': round(implied_prob * 100, 2),
        'kelly_fraction': round(kelly_fraction * 100, 2),
        'payout': round(payout, 2),
        'is_positive_ev': ev > 0
    }


def calculate_confidence_score(probability: float, ev_data: Dict, edge_data: Dict = None, 
                                factors: Dict = None, streak_info: Dict = None) -> Dict:
    """
    Calculate comprehensive confidence score with grade, risk tier, and stake suggestion.
    
    Args:
        probability: Win probability (0-100)
        ev_data: EV calculation results
        edge_data: Edge data dictionary
        factors: Performance factors dictionary
        streak_info: Streak information dictionary
    
    Returns:
        Dictionary with confidence score, grade, risk tier, and stake suggestion
    """
    # Base confidence from probability (weighted 40%)
    prob_score = probability * 0.4
    
    # EV contribution (weighted 25%)
    ev = ev_data.get('ev', 0)
    ev_pct = ev_data.get('ev_percentage', 0)
    # Normalize EV: $0-20 EV maps to 0-25 points
    ev_score = min(25, max(0, ev_pct * 2.5)) if ev > 0 else 0
    
    # Market edge contribution (weighted 20%)
    market_edge = ev_data.get('market_edge', 0)
    # Normalize: 0-15% edge maps to 0-20 points
    edge_score = min(20, max(0, market_edge * 1.33)) if market_edge > 0 else 0
    
    # Streak bonus (weighted 10%) - enhanced with analytics
    streak_score = 0
    streak_ev_adjustment = 0
    if streak_info and streak_info.get('active'):
        streak_count = streak_info.get('streak_count', 0)
        streak_score = min(10, streak_count * 2.5)  # 2-4 streak = 5-10 points
        
        # Apply streak EV adjustment from enhanced analytics
        if streak_info.get('analytics') and streak_info['analytics'].get('ev_adjustment'):
            streak_ev_adjustment = streak_info['analytics']['ev_adjustment'].get('adjustment_pct', 0)
            # Convert EV adjustment to score contribution (max 5 points either way)
            streak_score += max(-5, min(5, streak_ev_adjustment / 2))
        
        # Reduce score for high regression risk
        if streak_info.get('analytics') and streak_info['analytics'].get('regression'):
            regression_risk = streak_info['analytics']['regression'].get('risk_level', 'low')
            if regression_risk == 'high':
                streak_score = max(0, streak_score - 5)
            elif regression_risk == 'medium':
                streak_score = max(0, streak_score - 2)
    
    # Factors bonus (weighted 5%)
    factor_score = 0
    if factors:
        # Positive minutes trend
        if factors.get('minutes_trend') == 'up':
            factor_score += 2
        # Low variance
        cv = factors.get('minutes_cv', 0)
        if cv and cv < 15:
            factor_score += 2
        # Not injured
        if not factors.get('recent_dnp', False):
            factor_score += 1
    
    # Calculate total confidence score (0-100)
    raw_score = prob_score + ev_score + edge_score + streak_score + factor_score
    confidence_score = round(min(100, max(0, raw_score)), 1)
    
    # Determine letter grade
    if confidence_score >= 95:
        grade = 'A+'
        grade_description = 'Elite Lock'
    elif confidence_score >= 90:
        grade = 'A'
        grade_description = 'Strong Play'
    elif confidence_score >= 85:
        grade = 'A-'
        grade_description = 'Very Good'
    elif confidence_score >= 80:
        grade = 'B+'
        grade_description = 'Good Value'
    elif confidence_score >= 75:
        grade = 'B'
        grade_description = 'Solid'
    elif confidence_score >= 70:
        grade = 'B-'
        grade_description = 'Above Average'
    elif confidence_score >= 65:
        grade = 'C+'
        grade_description = 'Moderate'
    elif confidence_score >= 60:
        grade = 'C'
        grade_description = 'Average'
    elif confidence_score >= 55:
        grade = 'C-'
        grade_description = 'Below Average'
    elif confidence_score >= 50:
        grade = 'D'
        grade_description = 'Risky'
    else:
        grade = 'F'
        grade_description = 'Avoid'
    
    # Determine risk tier based on multiple factors
    risk_factors = 0
    
    # Low probability = higher risk
    if probability < 60:
        risk_factors += 2
    elif probability < 70:
        risk_factors += 1
    
    # Negative EV = higher risk
    if ev < 0:
        risk_factors += 2
    elif ev < 5:
        risk_factors += 1
    
    # High variance player = higher risk
    if factors and factors.get('minutes_cv', 0) > 20:
        risk_factors += 1
    
    # Recent DNP = higher risk
    if factors and factors.get('recent_dnp'):
        risk_factors += 2
    
    # Negative trend = higher risk
    if factors and factors.get('minutes_trend') == 'down':
        risk_factors += 1
    
    # No streak = slightly higher risk
    if not streak_info or not streak_info.get('active'):
        risk_factors += 0.5
    
    # Determine risk tier
    if risk_factors <= 1:
        risk_tier = 'Low'
        risk_color = 'green'
        risk_description = 'Safe bet with strong fundamentals'
    elif risk_factors <= 3:
        risk_tier = 'Medium'
        risk_color = 'yellow'
        risk_description = 'Reasonable risk with good upside'
    else:
        risk_tier = 'High'
        risk_color = 'red'
        risk_description = 'Elevated risk - bet with caution'
    
    # Calculate suggested stake (% of bankroll)
    # Based on modified Kelly Criterion with risk adjustment
    kelly = ev_data.get('kelly_fraction', 0) / 100  # Convert from percentage
    
    # Apply risk multiplier
    risk_multiplier = {'Low': 1.0, 'Medium': 0.7, 'High': 0.4}.get(risk_tier, 0.5)
    
    # Apply confidence multiplier
    confidence_multiplier = confidence_score / 100
    
    # Calculate suggested stake
    base_stake = kelly * risk_multiplier * confidence_multiplier
    
    # Apply stake limits based on confidence
    if confidence_score >= 90:
        min_stake, max_stake = 0.03, 0.05  # 3-5% for elite plays
    elif confidence_score >= 80:
        min_stake, max_stake = 0.02, 0.04  # 2-4% for strong plays
    elif confidence_score >= 70:
        min_stake, max_stake = 0.01, 0.03  # 1-3% for good plays
    elif confidence_score >= 60:
        min_stake, max_stake = 0.005, 0.02  # 0.5-2% for moderate plays
    else:
        min_stake, max_stake = 0.005, 0.01  # 0.5-1% for risky plays
    
    suggested_stake = max(min_stake, min(max_stake, base_stake))
    suggested_stake_pct = round(suggested_stake * 100, 2)
    
    # Calculate unit size (1 unit = 1% of bankroll)
    units = round(suggested_stake * 100, 1)
    
    # Generate stake description
    if suggested_stake_pct >= 4:
        stake_label = 'MAX BET'
    elif suggested_stake_pct >= 3:
        stake_label = 'Strong'
    elif suggested_stake_pct >= 2:
        stake_label = 'Standard'
    elif suggested_stake_pct >= 1:
        stake_label = 'Light'
    else:
        stake_label = 'Minimal'
    
    return {
        'confidence_score': confidence_score,
        'grade': grade,
        'grade_description': grade_description,
        'risk_tier': risk_tier,
        'risk_color': risk_color,
        'risk_description': risk_description,
        'risk_factors': round(risk_factors, 1),
        'suggested_stake_pct': suggested_stake_pct,
        'units': units,
        'stake_label': stake_label,
        'breakdown': {
            'probability_contribution': round(prob_score, 1),
            'ev_contribution': round(ev_score, 1),
            'edge_contribution': round(edge_score, 1),
            'streak_contribution': round(streak_score, 1),
            'factor_contribution': round(factor_score, 1)
        }
    }


def grade_matchup(edge_data: Dict, factors: Optional[Dict] = None, matchup_data: Optional[Dict] = None) -> Dict:
    """
    Grade a matchup from A+ to F based on multiple factors.
    
    Args:
        edge_data: Edge data dictionary
        factors: Performance factors dictionary
        matchup_data: Matchup analysis dictionary
    
    Returns:
        Dictionary with grade and reasoning
    """
    score = 0.0
    reasons = []
    
    # Base score from probability
    probability = edge_data.get('probability', 0)
    if probability >= 85:
        score += 30
        reasons.append("Exceptional probability (85%+)")
    elif probability >= 80:
        score += 25
        reasons.append("High probability (80%+)")
    elif probability >= 75:
        score += 20
        reasons.append("Strong probability (75%+)")
    elif probability >= 70:
        score += 15
        reasons.append("Good probability (70%+)")
    else:
        score += 10
        reasons.append("Moderate probability")
    
    # Edge size
    difference = edge_data.get('difference', 0)
    if difference >= 5:
        score += 20
        reasons.append("Large edge (5+ points)")
    elif difference >= 3:
        score += 15
        reasons.append("Significant edge (3+ points)")
    elif difference >= 2:
        score += 10
        reasons.append("Moderate edge (2+ points)")
    else:
        score += 5
        reasons.append("Small edge")
    
    # Performance factors
    if factors:
        # Trend
        trend = factors.get('performance_trend', 'stable')
        if trend == 'up':
            score += 10
            reasons.append("Upward trend")
        elif trend == 'down':
            score -= 10
            reasons.append("Downward trend")
        
        # Minutes stability
        if not factors.get('rotation_change', False):
            score += 5
            reasons.append("Stable rotation")
        else:
            score -= 5
            reasons.append("Rotation change")
        
        # Injury risk
        if factors.get('injury_risk', False):
            score -= 15
            reasons.append("Injury risk")
        elif not factors.get('recent_dnp', False):
            score += 5
            reasons.append("No recent DNP")
        
        # Consistency
        if factors.get('minutes_variance', 100) < 5:
            score += 5
            reasons.append("Consistent minutes")
    
    # Matchup advantage
    if matchup_data:
        advantage = matchup_data.get('advantage', 0)
        if advantage >= 3:
            score += 15
            reasons.append(f"Strong matchup advantage (+{advantage})")
        elif advantage >= 1:
            score += 10
            reasons.append(f"Matchup advantage (+{advantage})")
        elif advantage <= -2:
            score -= 10
            reasons.append(f"Matchup disadvantage ({advantage})")
    
    # Streak bonus
    streak = edge_data.get('streak', {})
    if streak.get('active', False):
        streak_count = streak.get('streak_count', 0)
        if streak_count >= 4:
            score += 15
            reasons.append(f"Strong streak ({streak_count} games)")
        elif streak_count >= 2:
            score += 10
            reasons.append(f"Active streak ({streak_count} games)")
    
    # Convert score to grade
    if score >= 90:
        grade = "A+"
        grade_numeric = 4.3
    elif score >= 85:
        grade = "A"
        grade_numeric = 4.0
    elif score >= 80:
        grade = "A-"
        grade_numeric = 3.7
    elif score >= 75:
        grade = "B+"
        grade_numeric = 3.3
    elif score >= 70:
        grade = "B"
        grade_numeric = 3.0
    elif score >= 65:
        grade = "B-"
        grade_numeric = 2.7
    elif score >= 60:
        grade = "C+"
        grade_numeric = 2.3
    elif score >= 55:
        grade = "C"
        grade_numeric = 2.0
    elif score >= 50:
        grade = "C-"
        grade_numeric = 1.7
    elif score >= 45:
        grade = "D+"
        grade_numeric = 1.3
    elif score >= 40:
        grade = "D"
        grade_numeric = 1.0
    else:
        grade = "F"
        grade_numeric = 0.0
    
    return {
        'grade': grade,
        'grade_numeric': grade_numeric,
        'score': round(score, 1),
        'reasons': reasons[:5],  # Top 5 reasons
        'confidence': 'high' if score >= 75 else 'medium' if score >= 60 else 'low'
    }

def calculate_contextual_grade(edge_data: Dict, factors: Optional[Dict] = None) -> Dict:
    """
    Calculate contextual grade based on game situation, opponent, and player form.
    
    Args:
        edge_data: Edge data dictionary
        factors: Performance factors dictionary
    
    Returns:
        Dictionary with contextual analysis
    """
    context_score = 0.0
    context_factors = []
    
    # Recent form
    if factors:
        recent_avg = factors.get('recent_stat_avg', 0)
        older_avg = factors.get('older_stat_avg', 0)
        if recent_avg and older_avg:
            if recent_avg > older_avg + 3:
                context_score += 15
                context_factors.append("Strong recent form")
            elif recent_avg < older_avg - 3:
                context_score -= 10
                context_factors.append("Declining form")
    
    # Minutes trend
    if factors:
        min_trend = factors.get('minutes_trend', 'stable')
        if min_trend == 'up':
            context_score += 10
            context_factors.append("Increasing minutes")
        elif min_trend == 'down':
            context_score -= 10
            context_factors.append("Decreasing minutes")
    
    # Consistency
    if factors:
        variance = factors.get('minutes_variance', 100)
        if variance < 3:
            context_score += 10
            context_factors.append("Very consistent")
        elif variance < 5:
            context_score += 5
            context_factors.append("Consistent")
        elif variance > 10:
            context_score -= 5
            context_factors.append("Inconsistent minutes")
    
    # Convert to grade
    if context_score >= 25:
        grade = "A"
    elif context_score >= 15:
        grade = "B"
    elif context_score >= 5:
        grade = "C"
    elif context_score >= -5:
        grade = "D"
    else:
        grade = "F"
    
    return {
        'grade': grade,
        'score': round(context_score, 1),
        'factors': context_factors
    }

def enhance_edge_with_analytics(edge: Dict, default_odds: int = -110) -> Dict:
    """
    Enhance an edge dictionary with advanced analytics.
    
    Args:
        edge: Edge dictionary
        default_odds: Default American odds (default: -110)
    
    Returns:
        Enhanced edge dictionary
    """
    probability = edge.get('probability', 0)
    factors = edge.get('factors', {})
    streak_info = edge.get('streak', {}) if edge.get('streak', {}).get('active') else None
    matchup_data = edge.get('beneficiary', {}).get('matchup_data') if edge.get('beneficiary') else None
    
    # Calculate EV
    ev_data = calculate_expected_value(probability, default_odds)
    edge['ev'] = ev_data
    
    # Calculate confidence score with grade, risk tier, and stake suggestion
    confidence_data = calculate_confidence_score(
        probability=probability,
        ev_data=ev_data,
        edge_data=edge,
        factors=factors,
        streak_info=streak_info
    )
    edge['confidence'] = confidence_data
    
    # Grade matchup
    matchup_grade = grade_matchup(edge, factors, matchup_data)
    edge['matchup_grade'] = matchup_grade
    
    # Contextual grade
    contextual_grade = calculate_contextual_grade(edge, factors)
    edge['contextual_grade'] = contextual_grade
    
    # Market edge
    edge['market_edge'] = ev_data['market_edge']
    edge['is_positive_ev'] = ev_data['is_positive_ev']
    
    return edge

def sort_edges_by_ev(edges: List[Dict], reverse: bool = True) -> List[Dict]:
    """Sort edges by Expected Value (highest first)."""
    return sorted(edges, key=lambda x: x.get('ev', {}).get('ev', 0), reverse=reverse)

def sort_edges_by_market_edge(edges: List[Dict], reverse: bool = True) -> List[Dict]:
    """Sort edges by market edge (highest first)."""
    return sorted(edges, key=lambda x: x.get('market_edge', 0), reverse=reverse)

def sort_edges_by_grade(edges: List[Dict], reverse: bool = True) -> List[Dict]:
    """Sort edges by matchup grade (highest first)."""
    return sorted(edges, key=lambda x: x.get('matchup_grade', {}).get('grade_numeric', 0), reverse=reverse)

def filter_positive_ev(edges: List[Dict]) -> List[Dict]:
    """Filter to only positive EV edges."""
    return [e for e in edges if e.get('is_positive_ev', False)]

def filter_by_grade(edges: List[Dict], min_grade: str = 'B') -> List[Dict]:
    """Filter edges by minimum grade."""
    grade_order = {'A+': 4.3, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                   'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0}
    min_grade_num = grade_order.get(min_grade, 0.0)
    return [e for e in edges if e.get('matchup_grade', {}).get('grade_numeric', 0) >= min_grade_num]

def filter_by_probability(edges: List[Dict], min_probability: float = 70.0) -> List[Dict]:
    """Filter edges by minimum probability."""
    return [e for e in edges if e.get('probability', 0) >= min_probability]

def filter_by_market_edge(edges: List[Dict], min_edge: float = 5.0) -> List[Dict]:
    """Filter edges by minimum market edge."""
    return [e for e in edges if e.get('market_edge', 0) >= min_edge]

def apply_tactical_filters(edges: List[Dict], filters: Dict) -> List[Dict]:
    """
    Apply multiple tactical filters to edges.
    
    Args:
        edges: List of edge dictionaries
        filters: Dictionary with filter criteria:
            - min_probability: Minimum probability
            - min_ev: Minimum EV
            - min_market_edge: Minimum market edge
            - min_grade: Minimum grade (A+, A, B+, etc.)
            - positive_ev_only: Only positive EV
            - exclude_injuries: Exclude injury risks
            - exclude_rotation_changes: Exclude rotation changes
    
    Returns:
        Filtered list of edges
    """
    filtered = edges.copy()
    
    if filters.get('min_probability'):
        filtered = filter_by_probability(filtered, filters['min_probability'])
    
    if filters.get('min_grade'):
        filtered = filter_by_grade(filtered, filters['min_grade'])
    
    if filters.get('min_market_edge'):
        filtered = filter_by_market_edge(filtered, filters['min_market_edge'])
    
    if filters.get('positive_ev_only'):
        filtered = filter_positive_ev(filtered)
    
    if filters.get('exclude_injuries'):
        filtered = [e for e in filtered if not e.get('factors', {}).get('injury_risk', False)]
    
    if filters.get('exclude_rotation_changes'):
        filtered = [e for e in filtered if not e.get('factors', {}).get('rotation_change', False)]
    
    if filters.get('min_ev'):
        filtered = [e for e in filtered if e.get('ev', {}).get('ev', 0) >= filters['min_ev']]
    
    return filtered

def get_sort_options() -> List[Dict]:
    """Get available sort options."""
    return [
        {'value': 'ev', 'label': 'Expected Value (EV)', 'desc': 'Sort by highest EV'},
        {'value': 'market_edge', 'label': 'Market Edge', 'desc': 'Sort by market edge %'},
        {'value': 'probability', 'label': 'Probability', 'desc': 'Sort by hit probability'},
        {'value': 'grade', 'label': 'Matchup Grade', 'desc': 'Sort by matchup grade (A+ to F)'},
        {'value': 'edge', 'label': 'Edge Size', 'desc': 'Sort by point difference'},
        {'value': 'kelly', 'label': 'Kelly Criterion', 'desc': 'Sort by Kelly fraction'},
    ]

def get_filter_options() -> List[Dict]:
    """Get available filter options."""
    return [
        {'key': 'min_probability', 'type': 'number', 'label': 'Min Probability %', 'default': 70},
        {'key': 'min_ev', 'type': 'number', 'label': 'Min EV ($)', 'default': 0},
        {'key': 'min_market_edge', 'type': 'number', 'label': 'Min Market Edge %', 'default': 0},
        {'key': 'min_grade', 'type': 'select', 'label': 'Min Grade', 'options': ['A+', 'A', 'B+', 'B', 'C+', 'C'], 'default': 'B'},
        {'key': 'positive_ev_only', 'type': 'checkbox', 'label': 'Positive EV Only', 'default': False},
        {'key': 'exclude_injuries', 'type': 'checkbox', 'label': 'Exclude Injury Risks', 'default': False},
        {'key': 'exclude_rotation_changes', 'type': 'checkbox', 'label': 'Exclude Rotation Changes', 'default': False},
    ]
