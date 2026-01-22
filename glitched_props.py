"""
Glitched Props tracking system.
Tracks props with pricing errors, anomalies, or glitches.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

GLITCHED_PROPS_FILE = 'glitched_props.json'

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

def add_glitched_prop(prop: str, reasoning: str, rating: int, platform: str):
    """
    Add a new glitched prop.
    
    Args:
        prop: The prop description (e.g., "LeBron James O 24.5 PTS")
        reasoning: Why it's glitched (e.g., "Line is 3 points off market average")
        rating: Rating 1-10 (10 = most glitched/valuable)
        platform: Platform name (e.g., "PrizePicks", "Underdog", "DraftKings")
    
    Returns:
        bool: True if added successfully
    """
    props = load_glitched_props()
    
    # Check if prop already exists
    for existing in props:
        if existing.get('prop') == prop and existing.get('platform') == platform:
            # Update existing
            existing['reasoning'] = reasoning
            existing['rating'] = rating
            existing['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return save_glitched_props(props)
    
    # Add new prop
    new_prop = {
        'id': len(props) + 1,
        'prop': prop,
        'reasoning': reasoning,
        'rating': rating,
        'platform': platform,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    props.append(new_prop)
    return save_glitched_props(props)

def get_glitched_props():
    """Get all glitched props, sorted by rating (highest first)."""
    props = load_glitched_props()
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
