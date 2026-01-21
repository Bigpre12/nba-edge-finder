"""
Essential stat categories for NBA betting props.
Supports individual stats and combinations.
"""

STAT_CATEGORIES = {
    'PTS': {
        'name': 'Points',
        'abbreviation': 'PTS',
        'description': 'Total points scored',
        'common_lines': [15, 20, 25, 30, 35, 40],
        'is_combination': False
    },
    'REB': {
        'name': 'Rebounds',
        'abbreviation': 'REB',
        'description': 'Total rebounds',
        'common_lines': [5, 7, 10, 12, 15],
        'is_combination': False
    },
    'AST': {
        'name': 'Assists',
        'abbreviation': 'AST',
        'description': 'Total assists',
        'common_lines': [5, 7, 10, 12, 15],
        'is_combination': False
    },
    'STL': {
        'name': 'Steals',
        'abbreviation': 'STL',
        'description': 'Total steals',
        'common_lines': [1, 2, 3, 4, 5],
        'is_combination': False
    },
    'BLK': {
        'name': 'Blocks',
        'abbreviation': 'BLK',
        'description': 'Total blocks',
        'common_lines': [1, 2, 3, 4, 5],
        'is_combination': False
    },
    '3PM': {
        'name': '3-Pointers Made',
        'abbreviation': '3PM',
        'description': 'Three-pointers made',
        'common_lines': [2, 3, 4, 5, 6],
        'is_combination': False
    },
    'PTS+REB': {
        'name': 'Points + Rebounds',
        'abbreviation': 'PTS+REB',
        'description': 'Combined points and rebounds',
        'common_lines': [20, 25, 30, 35, 40, 45],
        'is_combination': True,
        'components': ['PTS', 'REB']
    },
    'PTS+AST': {
        'name': 'Points + Assists',
        'abbreviation': 'PTS+AST',
        'description': 'Combined points and assists',
        'common_lines': [20, 25, 30, 35, 40, 45],
        'is_combination': True,
        'components': ['PTS', 'AST']
    },
    'REB+AST': {
        'name': 'Rebounds + Assists',
        'abbreviation': 'REB+AST',
        'description': 'Combined rebounds and assists',
        'common_lines': [10, 12, 15, 18, 20],
        'is_combination': True,
        'components': ['REB', 'AST']
    },
    'PTS+REB+AST': {
        'name': 'Points + Rebounds + Assists',
        'abbreviation': 'PRA',
        'description': 'Triple-double stat line',
        'common_lines': [30, 35, 40, 45, 50, 55],
        'is_combination': True,
        'components': ['PTS', 'REB', 'AST']
    },
    'STL+BLK': {
        'name': 'Steals + Blocks',
        'abbreviation': 'STL+BLK',
        'description': 'Combined steals and blocks',
        'common_lines': [2, 3, 4, 5, 6],
        'is_combination': True,
        'components': ['STL', 'BLK']
    }
}

def get_stat_categories():
    """Get all available stat categories."""
    return STAT_CATEGORIES

def get_individual_stats():
    """Get only individual stat categories (not combinations)."""
    return {k: v for k, v in STAT_CATEGORIES.items() if not v.get('is_combination', False)}

def get_combination_stats():
    """Get only combination stat categories."""
    return {k: v for k, v in STAT_CATEGORIES.items() if v.get('is_combination', False)}

def is_valid_stat_type(stat_type):
    """Check if stat type is valid."""
    return stat_type in STAT_CATEGORIES

def calculate_combination_stat(games_list, stat_type):
    """
    Calculate combined stat value for a game.
    
    Args:
        games_list: List of game dictionaries
        stat_type: Combination stat type (e.g., 'PTS+REB')
    
    Returns:
        List of combined stat values
    """
    if stat_type not in STAT_CATEGORIES:
        return None
    
    category = STAT_CATEGORIES[stat_type]
    if not category.get('is_combination'):
        return None
    
    components = category.get('components', [])
    combined_values = []
    
    for game in games_list:
        total = 0
        for component in components:
            # Get the stat value from the game
            # For combination stats, we need to fetch individual stats
            # This will be handled in nba_engine.py
            pass
        combined_values.append(total)
    
    return combined_values

def get_stat_display_name(stat_type):
    """Get display name for stat type."""
    return STAT_CATEGORIES.get(stat_type, {}).get('name', stat_type)

def get_stat_description(stat_type):
    """Get description for stat type."""
    return STAT_CATEGORIES.get(stat_type, {}).get('description', '')
