from flask import Flask, render_template, jsonify, request
from datetime import datetime, time
from nba_engine import check_for_edges, get_all_active_players, generate_projections_from_active_players
from line_tracker import (
    track_line_changes, get_line_changes, add_to_chase_list, get_chase_list,
    remove_from_chase_list, add_alt_line, get_alt_lines, update_line
)
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
import atexit

app = Flask(__name__)

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
        with open(PROJECTIONS_FILE, 'w') as f:
            json.dump(projections, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving projections: {e}")
        return False

# Load projections on startup
MARKET_PROJECTIONS = load_projections()

# Initialize scheduler for daily updates
scheduler = BackgroundScheduler()
scheduler.start()

def daily_update_job():
    """Run daily update at 8am - refresh edges and track line changes."""
    global MARKET_PROJECTIONS
    print(f"[{datetime.now()}] Running daily update at 8am...")
    
    try:
        # Reload projections
        MARKET_PROJECTIONS = load_projections()
        
        # Track line changes
        changes = track_line_changes(MARKET_PROJECTIONS)
        if changes:
            print(f"Line changes detected: {len(changes)} players")
            for player, change in changes.items():
                print(f"  {player}: {change['previous']} → {change['current']} ({change['direction']})")
        
        # Refresh edges data (pre-cache for faster access)
        get_edges_data()
        
        print("Daily update complete!")
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
atexit.register(lambda: scheduler.shutdown())

def get_edges_data():
    """
    Helper function to fetch edges data.
    """
    try:
        from nba_engine import filter_high_probability_props
        
        result = check_for_edges(MARKET_PROJECTIONS, threshold=2.0, include_streaks=True, min_streak=2, include_factors=True)
        edges = result.get('edges', [])
        streaks = result.get('streaks', [])
        
        # Sort streaks by streak count (longest first)
        streaks.sort(key=lambda x: x.get('streak_count', 0), reverse=True)
        
        # Sort edges by factors (injuries/rotation changes first)
        def sort_key(edge):
            factors = edge.get('factors', {})
            score = 0
            if factors.get('injury_risk'):
                score += 100
            if factors.get('rotation_change'):
                score += 50
            if factors.get('recent_dnp'):
                score += 75
            return score
        
        edges.sort(key=sort_key, reverse=True)
        
        # Filter for 70%+ probability props
        high_prob_props = filter_high_probability_props(edges, min_probability=70.0)
        
        return edges, streaks, high_prob_props, None
    except Exception as e:
        error_message = f"Error fetching edges: {str(e)}"
        return [], [], [], error_message

@app.route('/')
def index():
    """
    Main route that displays NBA betting edges.
    """
    global MARKET_PROJECTIONS
    MARKET_PROJECTIONS = load_projections()  # Reload from file
    edges, streaks, high_prob_props, error = get_edges_data()
    return render_template('index.html', edges=edges, streaks=streaks, high_prob_props=high_prob_props, projections=MARKET_PROJECTIONS, error=error)

@app.route('/api/edges')
def api_edges():
    """
    API endpoint that returns edges data as JSON for real-time updates.
    """
    global MARKET_PROJECTIONS
    MARKET_PROJECTIONS = load_projections()  # Reload in case it changed
    edges, streaks, high_prob_props, error = get_edges_data()
    return jsonify({
        'edges': edges,
        'streaks': streaks,
        'high_prob_props': high_prob_props,
        'projections': MARKET_PROJECTIONS,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'error': error
    })

@app.route('/api/active-players')
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
def api_load_all_players():
    """
    API endpoint to generate projections for all active players.
    This may take several minutes due to API rate limits.
    """
    try:
        data = request.get_json() or {}
        season = data.get('season', '2023-24')
        stat_type = data.get('stat_type', 'PTS')
        
        # Generate projections for all active players
        projections = generate_projections_from_active_players(
            stat_type=stat_type,
            season=season
        )
        
        # Save to file
        if save_projections(projections):
            global MARKET_PROJECTIONS
            MARKET_PROJECTIONS = projections
            return jsonify({
                'success': True,
                'message': f'Loaded {len(projections)} players',
                'count': len(projections)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save projections'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/projections', methods=['GET', 'POST'])
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
    MARKET_PROJECTIONS = load_projections()
    return jsonify({
        'projections': MARKET_PROJECTIONS,
        'count': len(MARKET_PROJECTIONS)
    })

@app.route('/api/line-changes')
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
def api_daily_update_status():
    """Get status of daily update scheduler."""
    jobs = scheduler.get_jobs()
    daily_job = next((job for job in jobs if job.id == 'daily_update'), None)
    
    status = {
        'scheduler_running': scheduler.running,
        'daily_update_scheduled': daily_job is not None,
        'next_run': daily_job.next_run_time.isoformat() if daily_job and daily_job.next_run_time else None,
        'last_update': None  # Could track this in a file
    }
    
    return jsonify(status)

@app.route('/api/trigger-update', methods=['POST'])
def api_trigger_update():
    """Manually trigger daily update."""
    try:
        daily_update_job()
        return jsonify({
            'success': True,
            'message': 'Update triggered successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Development mode
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Production mode - disable debug
    app.config['DEBUG'] = False