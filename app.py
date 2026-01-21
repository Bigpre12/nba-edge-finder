from flask import Flask, render_template, jsonify, request
from datetime import datetime, time
from nba_engine import check_for_edges, get_all_active_players, generate_projections_from_active_players
from line_tracker import (
    track_line_changes, get_line_changes, add_to_chase_list, get_chase_list,
    remove_from_chase_list, add_alt_line, get_alt_lines, update_line
)
from auth import requires_auth
from cache_manager import clear_old_cache
from parlay_calculator import recommend_parlays, calculate_parlay_payout, format_parlay_display
from advanced_analytics import (
    enhance_edge_with_analytics, sort_edges_by_ev, sort_edges_by_market_edge,
    sort_edges_by_grade, apply_tactical_filters, get_sort_options, get_filter_options
)
from stat_categories import (
    get_stat_categories, get_individual_stats, get_combination_stats,
    get_stat_display_name, is_valid_stat_type
)
import json
import os
import atexit

# Try to import scheduler, but don't fail if it's not available
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("Warning: APScheduler not available. Scheduled updates disabled.")

app = Flask(__name__)

# Enable response compression for faster loading
try:
    from flask_compress import Compress
    Compress(app)
    print("Response compression enabled")
except ImportError:
    print("Flask-Compress not available, compression disabled (optional)")

# File to store projections
PROJECTIONS_FILE = 'projections.json'

# Default market projections - Update these as needed
DEFAULT_PROJECTIONS = {
    "LeBron James": 24.5,
    "Kevin Durant": 26.5,
    "Stephen Curry": 28.5
}

def load_projections():
    """Load projections from file or return defaults."""
    if os.path.exists(PROJECTIONS_FILE):
        try:
            with open(PROJECTIONS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading projections: {e}")
            return DEFAULT_PROJECTIONS.copy()
    return DEFAULT_PROJECTIONS.copy()

def save_projections(projections):
    """Save projections to file."""
    try:
        if not projections or len(projections) == 0:
            print("⚠️ Warning: Attempted to save empty projections")
            return False
        
        file_path = os.path.abspath(PROJECTIONS_FILE)
        print(f"💾 Saving {len(projections)} players to: {file_path}")
        
        with open(PROJECTIONS_FILE, 'w') as f:
            json.dump(projections, f, indent=2)
        
        # Verify it was saved
        if os.path.exists(PROJECTIONS_FILE):
            file_size = os.path.getsize(PROJECTIONS_FILE)
            print(f"✅ Successfully saved {len(projections)} players to {PROJECTIONS_FILE}")
            print(f"   File size: {file_size} bytes")
            print(f"   Sample players saved: {', '.join(list(projections.keys())[:5])}...")
            return True
        else:
            print(f"❌ File was not created at {file_path}")
            return False
    except PermissionError as e:
        print(f"❌ Permission denied saving to {PROJECTIONS_FILE}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error saving projections: {e}")
        import traceback
        traceback.print_exc()
        return False

# Load projections on startup (lazy load to avoid blocking)
MARKET_PROJECTIONS = {}
_projections_loaded = False
def get_market_projections(force_reload=False):
    """Lazy load projections to avoid blocking startup."""
    global MARKET_PROJECTIONS, _projections_loaded
    if not _projections_loaded or force_reload:
        MARKET_PROJECTIONS = load_projections()
        _projections_loaded = True
        print(f"📊 Current market projections: {len(MARKET_PROJECTIONS)} players")
    return MARKET_PROJECTIONS

# Initialize scheduler for daily updates (only start if not already running)
scheduler = None

def init_scheduler():
    """Initialize and start the scheduler."""
    global scheduler
    if not SCHEDULER_AVAILABLE:
        print("Scheduler not available - skipping initialization")
        return
    
    try:
        if scheduler is None or (hasattr(scheduler, 'running') and not scheduler.running):
            scheduler = BackgroundScheduler(daemon=True)
            scheduler.start()
            
            def daily_update_job():
                """Run daily update at 8am - load all active players and refresh edges."""
                global MARKET_PROJECTIONS
                print(f"[{datetime.now()}] Running daily update at 8am...")
                
                try:
                    # Clear old cache before updating
                    print("Clearing expired cache...")
                    clear_old_cache()
                    
                    # Auto-load all active players and generate projections
                    print("Loading all active NBA players...")
                    new_projections = generate_projections_from_active_players(stat_type='PTS', season='2023-24')
                    
                    # Track line changes before updating
                    old_projections = load_projections()
                    changes = track_line_changes(new_projections)
                    if changes:
                        print(f"Line changes detected: {len(changes)} players")
                        for player, change in changes.items():
                            print(f"  {player}: {change['previous']} → {change['current']} ({change['direction']})")
                    
                    # Save new projections
                    MARKET_PROJECTIONS = new_projections
                    save_projections(MARKET_PROJECTIONS)
                    
                    # Refresh edges data (pre-cache for faster access)
                    get_edges_data()
                    
                    print(f"Daily update complete! Loaded {len(MARKET_PROJECTIONS)} active players.")
                except Exception as e:
                    print(f"Error in daily update: {e}")
            
            # Schedule daily update at 8am
            scheduler.add_job(
                func=daily_update_job,
                trigger="cron",
                hour=8,
                minute=0,
                id='daily_update',
                name='Daily 8am Update',
                replace_existing=True
            )
            
            # Shut down scheduler on app exit
            atexit.register(lambda: scheduler.shutdown() if scheduler and hasattr(scheduler, 'shutdown') else None)
            print("Scheduler initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize scheduler: {e}")
        print("Daily updates will not run automatically, but app will still work")

def get_edges_data(show_only_70_plus=True, stat_type='PTS', 
                   sort_by='ev', min_probability=70.0, min_ev=0.0, min_market_edge=0.0,
                   min_grade=None, positive_ev_only=False, exclude_injuries=False, exclude_rotation=False):
    """
    Helper function to fetch edges data with filtering and sorting.
    Only returns 70%+ probability props by default.
    Uses caching to improve performance.
    
    Args:
        show_only_70_plus: Filter to 70%+ probability props
        stat_type: Stat category to analyze (default: 'PTS')
        sort_by: Sort method ('ev', 'market_edge', 'probability', 'grade', 'edge', 'kelly')
        min_probability: Minimum hit probability (default: 70.0)
        min_ev: Minimum expected value (default: 0.0)
        min_market_edge: Minimum market edge percentage (default: 0.0)
        min_grade: Minimum grade (e.g., 'B', 'A', 'A+') or None
        positive_ev_only: Only show positive EV bets
        exclude_injuries: Exclude players with injury risks
        exclude_rotation: Exclude players with rotation changes
    """
    try:
        # Clear old cache periodically (every 10 calls)
        import random
        if random.randint(1, 10) == 1:
            clear_old_cache()
        from nba_engine import filter_high_probability_props, calculate_hit_probability
        
        # Track line changes before checking edges
        # Reload projections in case they were updated in background
        global MARKET_PROJECTIONS
        MARKET_PROJECTIONS = get_market_projections(force_reload=True)
        
        # Note: Don't generate projections here - it blocks the request
        # Use the "Load All Active Players" button or wait for background load
        # For different stat types, we'll use the same projections but check edges for that stat
        
        track_line_changes(MARKET_PROJECTIONS)
        
        result = check_for_edges(MARKET_PROJECTIONS, threshold=2.0, stat_type=stat_type, include_streaks=True, min_streak=2, include_factors=True)
        all_edges = result.get('edges', [])
        streaks = result.get('streaks', [])
        
        # Calculate probability and enhance with analytics for each edge
        edges = []
        for edge in all_edges:
            factors = edge.get('factors', {})
            streak_info = edge.get('streak', {}) if edge.get('streak', {}).get('active') else None
            probability = calculate_hit_probability(edge, factors, streak_info)
            edge['probability'] = probability
            
            # Enhance with advanced analytics (EV, grades, etc.)
            edge = enhance_edge_with_analytics(edge, default_odds=-110)
            edges.append(edge)
        
        # Apply tactical filters
        filter_dict = {
            'min_probability': min_probability,
            'min_ev': min_ev,
            'min_market_edge': min_market_edge,
            'min_grade': min_grade,
            'positive_ev_only': positive_ev_only,
            'exclude_injuries': exclude_injuries,
            'exclude_rotation_changes': exclude_rotation
        }
        filtered_edges = apply_tactical_filters(edges, filter_dict)
        
        # Filter to 70%+ if requested (but respect min_probability if higher)
        if show_only_70_plus:
            min_prob = max(70.0, min_probability)
            filtered_edges = [e for e in filtered_edges if e.get('probability', 0) >= min_prob]
        else:
            filtered_edges = [e for e in filtered_edges if e.get('probability', 0) >= min_probability]
        
        # Apply sorting
        if sort_by == 'ev':
            filtered_edges = sort_edges_by_ev(filtered_edges, reverse=True)
        elif sort_by == 'market_edge':
            filtered_edges = sort_edges_by_market_edge(filtered_edges, reverse=True)
        elif sort_by == 'probability':
            filtered_edges.sort(key=lambda x: x.get('probability', 0), reverse=True)
        elif sort_by == 'grade':
            filtered_edges = sort_edges_by_grade(filtered_edges, reverse=True)
        elif sort_by == 'edge':
            filtered_edges.sort(key=lambda x: abs(x.get('difference', 0)), reverse=True)
        elif sort_by == 'kelly':
            filtered_edges.sort(key=lambda x: x.get('analytics', {}).get('kelly_fraction', 0), reverse=True)
        else:
            # Default sort by EV
            filtered_edges = sort_edges_by_ev(filtered_edges, reverse=True)
        
        # Sort streaks by streak count (longest first)
        streaks.sort(key=lambda x: x.get('streak_count', 0), reverse=True)
        
        # Filter for 70%+ probability props (for high prob section)
        high_prob_props = filter_high_probability_props(filtered_edges, min_probability=70.0)
        
        # Generate parlay recommendations
        try:
            parlay_recommendations = recommend_parlays(high_prob_props)
        except Exception as e:
            print(f"Error generating parlay recommendations: {e}")
            parlay_recommendations = {}
        
        return filtered_edges, streaks, high_prob_props, parlay_recommendations, None
    except Exception as e:
        error_message = f"Error fetching edges: {str(e)}"
        import traceback
        traceback.print_exc()
        return [], [], [], {}, error_message

@app.route('/health')
def health():
    """Health check endpoint for deployment platforms - no auth required."""
    return jsonify({'status': 'ok', 'message': 'App is running'}), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for quick health checks - no auth required."""
    return 'pong', 200

@app.route('/')
@requires_auth
def index():
    """
    Main route that displays NBA betting edges.
    Only shows 70%+ probability props by default.
    """
    try:
        global MARKET_PROJECTIONS
        MARKET_PROJECTIONS = get_market_projections()  # Lazy load
        
        # Auto-load all active players if projections file is empty or has default values
        # Do this in background to avoid blocking startup
        if len(MARKET_PROJECTIONS) <= 3:  # Only default players
            import threading
            import time
            def background_load():
                print("Auto-loading all active players in background...")
                try:
                    # Load for PTS first (most common)
                    new_projections = generate_projections_from_active_players(stat_type='PTS', season='2023-24')
                    if new_projections and len(new_projections) > 3:
                        save_projections(new_projections)
                        global MARKET_PROJECTIONS
                        MARKET_PROJECTIONS = new_projections
                        print(f"✅ Successfully loaded {len(MARKET_PROJECTIONS)} active players for PTS")
                        print(f"   Players loaded: {', '.join(list(new_projections.keys())[:10])}...")
                    else:
                        print(f"⚠️ Warning: Only loaded {len(new_projections) if new_projections else 0} players")
                        print("   This might be due to NBA API rate limits or network issues.")
                except Exception as e:
                    print(f"❌ Error auto-loading players: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start in background thread, don't wait
            load_thread = threading.Thread(target=background_load, daemon=True)
            load_thread.start()
            print(f"🚀 Started background thread to load all active players...")
        
        # Get selected stat type from request or default to PTS
        stat_type = request.args.get('stat_type', 'PTS')
        try:
            if not is_valid_stat_type(stat_type):
                stat_type = 'PTS'
        except Exception as e:
            print(f"Error validating stat type: {e}")
            stat_type = 'PTS'
        
        # Get edges - only 70%+ probability by default
        # This will work even if players are still loading
        try:
            edges, streaks, high_prob_props, parlay_recommendations, error = get_edges_data(show_only_70_plus=True, stat_type=stat_type)
        except Exception as e:
            print(f"Error getting edges data: {e}")
            import traceback
            traceback.print_exc()
            edges, streaks, high_prob_props, parlay_recommendations, error = [], [], [], {}, f"Error loading edges: {str(e)}"
        
        # Get stat categories for UI - with error handling
        try:
            stat_categories = get_stat_categories()
            individual_stats = get_individual_stats()
            combination_stats = get_combination_stats()
        except Exception as e:
            print(f"Error getting stat categories: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to default PTS only
            stat_categories = {'PTS': {'name': 'Points', 'abbreviation': 'PTS', 'description': 'Total points scored'}}
            individual_stats = {'PTS': stat_categories['PTS']}
            combination_stats = {}
        
        return render_template('index.html', 
                             edges=edges, 
                             streaks=streaks, 
                             high_prob_props=high_prob_props, 
                             parlay_recommendations=parlay_recommendations, 
                             projections=MARKET_PROJECTIONS, 
                             error=error,
                             stat_categories=stat_categories,
                             individual_stats=individual_stats,
                             combination_stats=combination_stats,
                             current_stat_type=stat_type)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Fatal error in index route: {e}")
        print(error_trace)
        return f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: monospace; padding: 20px; background: #1a1a1a; color: #fff;">
            <h1 style="color: #e74c3c;">Internal Server Error</h1>
            <p>An error occurred while loading the page.</p>
            <pre style="background: #2a2a2a; padding: 15px; border-radius: 4px; overflow-x: auto;">{error_trace}</pre>
            <p><a href="/ping" style="color: #3498db;">Test ping endpoint</a></p>
        </body>
        </html>
        """, 500

@app.route('/api/edges')
@requires_auth
def api_edges():
    """
    API endpoint that returns edges data as JSON for real-time updates.
    Supports filtering and sorting via query parameters.
    """
    global MARKET_PROJECTIONS
    MARKET_PROJECTIONS = load_projections()  # Reload in case it changed
    
    # Get selected stat type
    stat_type = request.args.get('stat_type', 'PTS')
    try:
        if not is_valid_stat_type(stat_type):
            stat_type = 'PTS'
    except Exception as e:
        print(f"Error validating stat type in API: {e}")
        stat_type = 'PTS'
    
    # Check if we should show all or just 70%+
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    
    # Get filter parameters
    sort_by = request.args.get('sort_by', 'ev')
    min_probability = float(request.args.get('min_probability', 70.0))
    min_ev = float(request.args.get('min_ev', 0.0))
    min_market_edge = float(request.args.get('min_market_edge', 0.0))
    min_grade = request.args.get('min_grade') or None
    positive_ev_only = request.args.get('positive_ev_only', 'false').lower() == 'true'
    exclude_injuries = request.args.get('exclude_injuries', 'false').lower() == 'true'
    exclude_rotation = request.args.get('exclude_rotation', 'false').lower() == 'true'
    
    try:
        edges, streaks, high_prob_props, parlay_recommendations, error = get_edges_data(
            show_only_70_plus=not show_all,
            stat_type=stat_type,
            sort_by=sort_by,
            min_probability=min_probability,
            min_ev=min_ev,
            min_market_edge=min_market_edge,
            min_grade=min_grade,
            positive_ev_only=positive_ev_only,
            exclude_injuries=exclude_injuries,
            exclude_rotation=exclude_rotation
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        edges, streaks, high_prob_props, parlay_recommendations, error = [], [], [], {}, f"Error: {str(e)}"
    
    return jsonify({
        'edges': edges,
        'streaks': streaks,
        'high_prob_props': high_prob_props,
        'parlay_recommendations': parlay_recommendations,
        'projections': MARKET_PROJECTIONS,
        'total_players_loaded': len(MARKET_PROJECTIONS),
        'showing_70_plus_only': not show_all,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'error': error
    })

@app.route('/api/active-players')
@requires_auth
def api_active_players():
    """
    API endpoint that returns all active NBA players.
    """
    try:
        active_players = get_all_active_players()
        return jsonify({
            'players': active_players,
            'count': len(active_players)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'players': [], 'count': 0}), 500

@app.route('/api/load-all-players', methods=['POST'])
@requires_auth
def api_load_all_players():
    """
    API endpoint to generate projections for all active players.
    This may take several minutes due to API rate limits.
    Runs in background to avoid blocking.
    """
    try:
        data = request.get_json() or {}
        season = data.get('season', '2023-24')
        stat_type = data.get('stat_type', 'PTS')
        
        # Run in background thread to avoid blocking
        import threading
        def background_load():
            try:
                print(f"Loading all active players for {stat_type}...")
                projections = generate_projections_from_active_players(
                    stat_type=stat_type,
                    season=season
                )
                
                if projections and len(projections) > 0:
                    save_projections(projections)
                    global MARKET_PROJECTIONS
                    MARKET_PROJECTIONS = projections
                    print(f"Successfully loaded {len(projections)} players for {stat_type}")
                else:
                    print(f"Warning: No players loaded for {stat_type}")
            except Exception as e:
                print(f"Error loading players: {e}")
                import traceback
                traceback.print_exc()
        
        # Start background thread
        thread = threading.Thread(target=background_load, daemon=True)
        thread.start()
        
        # Return immediately
        return jsonify({
            'success': True,
            'message': 'Loading players in background. This may take 10-15 minutes. Check back later.',
            'status': 'started'
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/projections', methods=['GET', 'POST'])
@requires_auth
def api_projections():
    """
    API endpoint to get or update projections.
    """
    global MARKET_PROJECTIONS
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            if 'projections' in data:
                MARKET_PROJECTIONS = data['projections']
                if save_projections(MARKET_PROJECTIONS):
                    return jsonify({'success': True, 'message': 'Projections updated'})
                else:
                    return jsonify({'success': False, 'error': 'Failed to save'}), 500
            else:
                return jsonify({'success': False, 'error': 'No projections provided'}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # GET request
    MARKET_PROJECTIONS = get_market_projections()
    return jsonify({
        'projections': MARKET_PROJECTIONS,
        'count': len(MARKET_PROJECTIONS)
    })

@app.route('/api/line-changes')
@requires_auth
def api_line_changes():
    """Get line changes since last update."""
    global MARKET_PROJECTIONS
    MARKET_PROJECTIONS = load_projections()
    changes = track_line_changes(MARKET_PROJECTIONS)
    return jsonify({
        'changes': changes,
        'count': len(changes),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/chase-list', methods=['GET', 'POST', 'DELETE'])
@requires_auth
def api_chase_list():
    """Manage chase list - props to track/follow."""
    if request.method == 'POST':
        data = request.get_json()
        player = data.get('player')
        line = data.get('line')
        stat_type = data.get('stat_type', 'PTS')
        reason = data.get('reason', '')
        
        if add_to_chase_list(player, line, stat_type, reason):
            return jsonify({'success': True, 'message': 'Added to chase list'})
        return jsonify({'success': False, 'error': 'Failed to add'}), 400
    
    elif request.method == 'DELETE':
        data = request.get_json()
        player = data.get('player')
        stat_type = data.get('stat_type', 'PTS')
        
        if remove_from_chase_list(player, stat_type):
            return jsonify({'success': True, 'message': 'Removed from chase list'})
        return jsonify({'success': False, 'error': 'Failed to remove'}), 400
    
    # GET request
    chase_list = get_chase_list()
    return jsonify({
        'chase_list': chase_list,
        'count': len(chase_list)
    })

@app.route('/api/alt-lines', methods=['GET', 'POST'])
@requires_auth
def api_alt_lines():
    """Manage alternative lines."""
    if request.method == 'POST':
        data = request.get_json()
        player = data.get('player')
        main_line = data.get('main_line')
        alt_line = data.get('alt_line')
        stat_type = data.get('stat_type', 'PTS')
        source = data.get('source', '')
        
        if add_alt_line(player, main_line, alt_line, stat_type, source):
            return jsonify({'success': True, 'message': 'Alternative line added'})
        return jsonify({'success': False, 'error': 'Failed to add'}), 400
    
    # GET request
    player = request.args.get('player')
    stat_type = request.args.get('stat_type', 'PTS')
    alt_lines = get_alt_lines(player, stat_type)
    return jsonify({
        'alt_lines': alt_lines,
        'player': player,
        'stat_type': stat_type
    })

@app.route('/api/update-line', methods=['POST'])
@requires_auth
def api_update_line():
    """Update a line even after it's been sent off."""
    global MARKET_PROJECTIONS
    data = request.get_json()
    player = data.get('player')
    old_line = data.get('old_line')
    new_line = data.get('new_line')
    stat_type = data.get('stat_type', 'PTS')
    
    if not all([player, old_line is not None, new_line is not None]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Update in projections
    MARKET_PROJECTIONS[player] = new_line
    save_projections(MARKET_PROJECTIONS)
    
    # Track the change
    changes = update_line(player, old_line, new_line, stat_type)
    
    return jsonify({
        'success': True,
        'message': f'Line updated: {old_line} → {new_line}',
        'changes': changes
    })

@app.route('/api/daily-update-status')
@requires_auth
def api_daily_update_status():
    """Get status of daily update scheduler."""
    global scheduler
    try:
        if scheduler and hasattr(scheduler, 'running') and scheduler.running:
            jobs = scheduler.get_jobs()
            daily_job = next((job for job in jobs if job.id == 'daily_update'), None)
            
            status = {
                'scheduler_running': True,
                'daily_update_scheduled': daily_job is not None,
                'next_run': daily_job.next_run_time.isoformat() if daily_job and daily_job.next_run_time else None,
                'last_update': None
            }
        else:
            status = {
                'scheduler_running': False,
                'daily_update_scheduled': False,
                'next_run': None,
                'last_update': None,
                'note': 'Scheduler not initialized or not available'
            }
    except Exception as e:
        status = {
            'scheduler_running': False,
            'daily_update_scheduled': False,
            'next_run': None,
            'error': str(e)
        }
    
    return jsonify(status)

@app.route('/api/trigger-update', methods=['POST'])
@requires_auth
def api_trigger_update():
    """Manually trigger daily update."""
    global MARKET_PROJECTIONS
    try:
        print(f"[{datetime.now()}] Manual update triggered...")
        
        # Auto-load all active players and generate projections
        print("Loading all active NBA players...")
        new_projections = generate_projections_from_active_players(stat_type='PTS', season='2023-24')
        
        # Track line changes before updating
        old_projections = load_projections()
        changes = track_line_changes(new_projections)
        if changes:
            print(f"Line changes detected: {len(changes)} players")
        
        # Save new projections
        MARKET_PROJECTIONS = new_projections
        save_projections(MARKET_PROJECTIONS)
        
        # Refresh edges data
        get_edges_data()
        
        return jsonify({
            'success': True,
            'message': f'Update triggered successfully. Loaded {len(MARKET_PROJECTIONS)} players.',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/parlay-calculator', methods=['POST'])
@requires_auth
def api_parlay_calculator():
    """Calculate parlay payout for custom bets."""
    try:
        data = request.get_json()
        bets = data.get('bets', [])
        odds_format = data.get('odds_format', 'american')
        
        if not bets or len(bets) < 2:
            return jsonify({
                'success': False,
                'error': 'Parlay requires at least 2 bets'
            }), 400
        
        payout_info = calculate_parlay_payout(bets, odds_format)
        
        return jsonify({
            'success': True,
            'payout': payout_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Development mode
    try:
        init_scheduler()
    except Exception as e:
        print(f"Warning: Scheduler initialization failed: {e}")
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Production mode - disable debug
    app.config['DEBUG'] = False
    # Initialize scheduler for production (delayed to avoid blocking startup)
    # Use a simple thread to initialize scheduler after app starts
    import threading
    def delayed_scheduler_init():
        import time
        time.sleep(2)  # Wait 2 seconds for app to fully start
        try:
            init_scheduler()
        except Exception as e:
            print(f"Warning: Scheduler initialization failed: {e}")
    
    scheduler_thread = threading.Thread(target=delayed_scheduler_init, daemon=True)
    scheduler_thread.start()
    print("App starting in production mode. Scheduler will initialize in background.")