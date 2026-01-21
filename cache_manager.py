"""
Simple caching system for NBA API responses to reduce API calls and improve performance.
"""
import json
import os
from datetime import datetime, timedelta
from functools import wraps

CACHE_DIR = 'cache'
CACHE_DURATION = timedelta(hours=1)  # Cache for 1 hour

def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_key(player_name, stat_type, season, games):
    """Generate a cache key for a player's stats."""
    return f"{player_name}_{stat_type}_{season}_{games}"

def get_cache_file_path(cache_key):
    """Get the file path for a cache key."""
    ensure_cache_dir()
    # Sanitize filename
    safe_key = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in cache_key)
    return os.path.join(CACHE_DIR, f"{safe_key}.json")

def get_cached_data(cache_key):
    """Retrieve cached data if it exists and is still valid."""
    cache_file = get_cache_file_path(cache_key)
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is still valid
        cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
        if datetime.now() - cached_time > CACHE_DURATION:
            # Cache expired, delete it
            os.remove(cache_file)
            return None
        
        return cache_data.get('data')
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None

def set_cached_data(cache_key, data):
    """Store data in cache."""
    try:
        cache_file = get_cache_file_path(cache_key)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error writing cache: {e}")

def clear_old_cache():
    """Remove expired cache files."""
    ensure_cache_dir()
    try:
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(CACHE_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        cache_data = json.load(f)
                    cached_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                    if datetime.now() - cached_time > CACHE_DURATION:
                        os.remove(filepath)
                except:
                    # If we can't read it, delete it
                    os.remove(filepath)
    except Exception as e:
        print(f"Error clearing cache: {e}")

def cached_api_call(cache_key_func):
    """
    Decorator to cache API call results.
    
    Usage:
        @cached_api_call(lambda player_name, stat_type, season, games: get_cache_key(player_name, stat_type, season, games))
        def fetch_player_stats(player_name, stat_type, season, games):
            # API call here
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Try to get from cache
            cached_result = get_cached_data(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Cache the result if it's valid
            if result is not None:
                set_cached_data(cache_key, result)
            
            return result
        return wrapper
    return decorator
