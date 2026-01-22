"""
Glitched Props tracking system.
Tracks props with pricing errors, anomalies, or glitches.
Includes source tracking, validation, and staleness detection.
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

GLITCHED_PROPS_FILE = 'glitched_props.json'

# Valid source types
SOURCE_TYPES = ['manual', 'auto_scan', 'api']

# Expected ranges for sanity checks
RATING_MIN = 1
RATING_MAX = 10
STALE_THRESHOLD_HOURS = 24  # Data older than this is considered stale
WARNING_THRESHOLD_HOURS = 6  # Data older than this shows warning

def load_glitched_props():
    """Load glitched props from file."""
    if os.path.exists(GLITCHED_PROPS_FILE):
        try:
            with open(GLITCHED_PROPS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading glitched props: {e}")
            return []
    return []

def save_glitched_props(props: List[Dict]):
    """Save glitched props to file."""
    try:
        with open(GLITCHED_PROPS_FILE, 'w') as f:
            json.dump(props, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving glitched props: {e}")
        return False

def add_glitched_prop(prop: str, reasoning: str, rating: int, platform: str, 
                      source: str = 'manual', source_detail: str = None):
    """
    Add a new glitched prop.
    
    Args:
        prop: The prop description (e.g., "LeBron James O 24.5 PTS")
        reasoning: Why it's glitched (e.g., "Line is 3 points off market average")
        rating: Rating 1-10 (10 = most glitched/valuable)
        platform: Platform name (e.g., "PrizePicks", "Underdog", "DraftKings")
        source: Source type ('manual', 'auto_scan', 'api')
        source_detail: Detailed source info (e.g., "PrizePicks API", "User submitted")
    
    Returns:
        bool: True if added successfully
    """
    props = load_glitched_props()
    
    # Validate source type
    if source not in SOURCE_TYPES:
        source = 'manual'
    
    # Default source_detail based on source
    if source_detail is None:
        source_detail = {
            'manual': 'User submitted',
            'auto_scan': 'Automated scanner',
            'api': 'External API'
        }.get(source, 'Unknown')
    
    # Check if prop already exists
    for existing in props:
        if existing.get('prop') == prop and existing.get('platform') == platform:
            # Update existing
            existing['reasoning'] = reasoning
            existing['rating'] = rating
            existing['source'] = source
            existing['source_detail'] = source_detail
            existing['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return save_glitched_props(props)
    
    # Add new prop
    new_prop = {
        'id': len(props) + 1,
        'prop': prop,
        'reasoning': reasoning,
        'rating': rating,
        'platform': platform,
        'source': source,
        'source_detail': source_detail,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    props.append(new_prop)
    return save_glitched_props(props)

def validate_glitched_prop(prop: Dict) -> Dict:
    """
    Validate a glitched prop and return validation status with warnings.
    
    Args:
        prop: The prop dictionary to validate
        
    Returns:
        Dict with 'is_valid', 'warnings', 'is_stale', 'staleness_level'
    """
    warnings = []
    is_valid = True
    is_stale = False
    staleness_level = 'fresh'  # 'fresh', 'warning', 'stale'
    hours_old = None
    
    # Check rating range
    rating = prop.get('rating', 0)
    if rating < RATING_MIN or rating > RATING_MAX:
        warnings.append(f'Invalid rating: {rating} (expected {RATING_MIN}-{RATING_MAX})')
        is_valid = False
    
    # Check prop format - should contain a number (the line)
    prop_text = prop.get('prop', '')
    if not re.search(r'\d+\.?\d*', prop_text):
        warnings.append('No line number found in prop')
        is_valid = False
    
    # Check for required fields
    required_fields = ['prop', 'platform', 'reasoning']
    for field in required_fields:
        if not prop.get(field):
            warnings.append(f'Missing required field: {field}')
            is_valid = False
    
    # Check staleness
    updated_at = prop.get('updated_at') or prop.get('created_at')
    if updated_at:
        try:
            update_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
            hours_old = (datetime.now() - update_time).total_seconds() / 3600
            
            if hours_old >= STALE_THRESHOLD_HOURS:
                is_stale = True
                staleness_level = 'stale'
                warnings.append(f'Data is {int(hours_old)} hours old (stale)')
            elif hours_old >= WARNING_THRESHOLD_HOURS:
                staleness_level = 'warning'
                warnings.append(f'Data is {int(hours_old)} hours old')
        except Exception:
            warnings.append('Invalid timestamp format')
    else:
        warnings.append('No timestamp found')
        is_stale = True
        staleness_level = 'stale'
    
    # Check platform is valid
    valid_platforms = ['PrizePicks', 'Underdog', 'DraftKings', 'FanDuel', 'BetMGM', 'Caesars', 'PointsBet', 'Other']
    platform = prop.get('platform', '')
    if platform and platform not in valid_platforms:
        warnings.append(f'Unknown platform: {platform}')
    
    return {
        'is_valid': is_valid,
        'warnings': warnings,
        'is_stale': is_stale,
        'staleness_level': staleness_level,
        'hours_old': hours_old
    }


def get_glitched_props(include_validation: bool = True):
    """
    Get all glitched props, sorted by rating (highest first).
    
    Args:
        include_validation: If True, include validation status for each prop
    """
    props = load_glitched_props()
    
    # Add validation info and ensure source fields exist
    for prop in props:
        # Ensure source fields exist for older props
        if 'source' not in prop:
            prop['source'] = 'manual'
        if 'source_detail' not in prop:
            prop['source_detail'] = 'Legacy entry'
        
        # Add validation if requested
        if include_validation:
            prop['validation'] = validate_glitched_prop(prop)
    
    # Sort by rating descending, then by updated_at descending
    props.sort(key=lambda x: (x.get('rating', 0), x.get('updated_at', '')), reverse=True)
    return props

def remove_glitched_prop(prop_id: int):
    """Remove a glitched prop by ID."""
    props = load_glitched_props()
    props = [p for p in props if p.get('id') != prop_id]
    return save_glitched_props(props)

def update_glitched_prop(prop_id: int, prop: str = None, reasoning: str = None, 
                         rating: int = None, platform: str = None):
    """Update a glitched prop."""
    props = load_glitched_props()
    for p in props:
        if p.get('id') == prop_id:
            if prop is not None:
                p['prop'] = prop
            if reasoning is not None:
                p['reasoning'] = reasoning
            if rating is not None:
                p['rating'] = rating
            if platform is not None:
                p['platform'] = platform
            p['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return save_glitched_props(props)
    return False
