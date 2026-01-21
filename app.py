from flask import Flask, render_template, jsonify, request
from datetime import datetime
from nba_engine import check_for_edges, get_all_active_players, generate_projections_from_active_players
import json
import os

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
