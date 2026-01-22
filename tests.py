"""
Comprehensive unit tests for NBA Edge Finder
Run with: python -m pytest tests.py -v
"""
import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

# Ensure the app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestImports(unittest.TestCase):
    """Test all module imports work correctly"""
    
    def test_flask_import(self):
        """Test Flask can be imported"""
        from flask import Flask
        self.assertTrue(Flask)
    
    def test_app_import(self):
        """Test main app module imports"""
        try:
            import app
            self.assertTrue(hasattr(app, 'app'))
        except Exception as e:
            self.fail(f"Failed to import app: {e}")
    
    def test_nba_engine_import(self):
        """Test nba_engine module imports"""
        try:
            import nba_engine
            self.assertTrue(hasattr(nba_engine, 'check_for_edges'))
        except Exception as e:
            self.fail(f"Failed to import nba_engine: {e}")
    
    def test_parlay_calculator_import(self):
        """Test parlay_calculator module imports"""
        try:
            from parlay_calculator import calculate_parlay_payout, find_best_parlays
            self.assertTrue(callable(calculate_parlay_payout))
            self.assertTrue(callable(find_best_parlays))
        except Exception as e:
            self.fail(f"Failed to import parlay_calculator: {e}")
    
    def test_line_tracker_import(self):
        """Test line_tracker module imports"""
        try:
            import line_tracker
            self.assertTrue(hasattr(line_tracker, 'track_line_changes'))
        except Exception as e:
            self.fail(f"Failed to import line_tracker: {e}")
    
    def test_stat_categories_import(self):
        """Test stat_categories module imports"""
        try:
            from stat_categories import get_stat_categories
            cats = get_stat_categories()
            self.assertIsInstance(cats, dict)
            self.assertIn('PTS', cats)
        except Exception as e:
            self.fail(f"Failed to import stat_categories: {e}")


class TestParlayCalculator(unittest.TestCase):
    """Test parlay calculator functions"""
    
    def test_calculate_parlay_payout_minimum_bets(self):
        """Test parlay requires at least 2 bets"""
        from parlay_calculator import calculate_parlay_payout
        
        result = calculate_parlay_payout([])
        self.assertFalse(result['valid'])
        
        result = calculate_parlay_payout([{'odds': -110, 'probability': 70}])
        self.assertFalse(result['valid'])
    
    def test_calculate_parlay_payout_valid(self):
        """Test valid parlay calculation"""
        from parlay_calculator import calculate_parlay_payout
        
        bets = [
            {'odds': -110, 'probability': 70},
            {'odds': -110, 'probability': 70}
        ]
        result = calculate_parlay_payout(bets)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['num_bets'], 2)
        self.assertIn('combined_probability', result)
        self.assertIn('american_odds', result)
        self.assertIn('payout_per_100', result)
    
    def test_find_best_parlays_insufficient_edges(self):
        """Test find_best_parlays with insufficient edges"""
        from parlay_calculator import find_best_parlays
        
        edges = [{'probability': 75, 'player': 'Test'}]
        result = find_best_parlays(edges, 2)
        
        self.assertEqual(result, [])
    
    def test_find_best_parlays_valid(self):
        """Test find_best_parlays with valid edges"""
        from parlay_calculator import find_best_parlays
        
        edges = [
            {'probability': 75, 'player': 'Player1', 'line': 20.5, 'recommendation': 'OVER'},
            {'probability': 72, 'player': 'Player2', 'line': 18.5, 'recommendation': 'UNDER'},
            {'probability': 70, 'player': 'Player3', 'line': 25.5, 'recommendation': 'OVER'}
        ]
        result = find_best_parlays(edges, 2, max_recommendations=2)
        
        self.assertIsInstance(result, list)
        if len(result) > 0:
            self.assertIn('bets', result[0])
            self.assertIn('payout', result[0])


class TestStatCategories(unittest.TestCase):
    """Test stat categories module"""
    
    def test_get_stat_categories(self):
        """Test get_stat_categories returns valid dict"""
        from stat_categories import get_stat_categories
        
        cats = get_stat_categories()
        self.assertIsInstance(cats, dict)
        self.assertIn('PTS', cats)
        self.assertIn('REB', cats)
        self.assertIn('AST', cats)
    
    def test_get_individual_stats(self):
        """Test get_individual_stats returns valid list"""
        from stat_categories import get_individual_stats
        
        stats = get_individual_stats()
        self.assertIsInstance(stats, (list, dict))
    
    def test_is_valid_stat_type(self):
        """Test stat type validation"""
        from stat_categories import is_valid_stat_type
        
        self.assertTrue(is_valid_stat_type('PTS'))
        self.assertTrue(is_valid_stat_type('REB'))
        self.assertFalse(is_valid_stat_type('INVALID'))


class TestLineTracker(unittest.TestCase):
    """Test line tracker functions"""
    
    def test_track_line_changes(self):
        """Test line change tracking"""
        from line_tracker import track_line_changes
        
        projections = {'Player1': 20.5, 'Player2': 18.5}
        # Should not raise an error
        try:
            track_line_changes(projections)
        except Exception as e:
            self.fail(f"track_line_changes raised: {e}")
    
    def test_get_line_changes(self):
        """Test getting line changes"""
        from line_tracker import get_line_changes
        
        changes = get_line_changes()
        self.assertIsInstance(changes, dict)


class TestFlaskApp(unittest.TestCase):
    """Test Flask application routes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test client"""
        # Mock auth for testing
        os.environ['AUTH_USERNAME'] = 'test'
        os.environ['AUTH_PASSWORD'] = 'test'
        
        from app import app
        app.config['TESTING'] = True
        cls.client = app.test_client()
        cls.app = app
    
    def get_auth_headers(self):
        """Get basic auth headers"""
        import base64
        credentials = base64.b64encode(b'test:test').decode('utf-8')
        return {'Authorization': f'Basic {credentials}'}
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn(data['status'], ['ok', 'healthy'])
    
    def test_ping_endpoint(self):
        """Test /ping endpoint"""
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)
        # Ping returns text, not JSON
        self.assertIn(b'pong', response.data.lower())
    
    def test_index_requires_auth(self):
        """Test index page requires authentication"""
        response = self.client.get('/')
        # Should either redirect or return 401
        self.assertIn(response.status_code, [401, 302])
    
    def test_index_with_auth(self):
        """Test index page with authentication"""
        response = self.client.get('/', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
    
    def test_api_edges_requires_auth(self):
        """Test /api/edges requires authentication"""
        response = self.client.get('/api/edges')
        self.assertIn(response.status_code, [401, 302])
    
    def test_api_edges_with_auth(self):
        """Test /api/edges with authentication"""
        response = self.client.get('/api/edges', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('edges', data)
    
    def test_api_line_changes(self):
        """Test /api/line-changes endpoint"""
        response = self.client.get('/api/line-changes', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('changes', data)
    
    def test_api_chase_list(self):
        """Test /api/chase-list endpoint"""
        response = self.client.get('/api/chase-list', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('chase_list', data)
    
    def test_api_alt_lines(self):
        """Test /api/alt-lines endpoint"""
        response = self.client.get('/api/alt-lines', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('alt_lines', data)
    
    def test_api_parlay_calculator_get(self):
        """Test /api/parlay-calculator GET endpoint"""
        response = self.client.get('/api/parlay-calculator', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('recommendations', data)
    
    def test_api_glitched_props(self):
        """Test /api/glitched-props endpoint"""
        response = self.client.get('/api/glitched-props', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_api_loading_status(self):
        """Test /api/loading-status endpoint"""
        response = self.client.get('/api/loading-status', headers=self.get_auth_headers())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('loading_in_progress', data)
        self.assertIn('player_count', data)


class TestGlitchedProps(unittest.TestCase):
    """Test glitched props module"""
    
    def test_get_glitched_props(self):
        """Test getting glitched props"""
        from glitched_props import get_glitched_props
        
        props = get_glitched_props()
        self.assertIsInstance(props, list)
    
    def test_validate_glitched_prop(self):
        """Test glitched prop validation"""
        from glitched_props import validate_glitched_prop
        
        valid_prop = {
            'id': 1,
            'player': 'Test Player',
            'platform': 'Test',
            'line': 20.5,
            'rating': 4,
            'reasoning': 'Test reason',
            'updated_at': '2024-01-01 12:00:00'
        }
        result = validate_glitched_prop(valid_prop)
        self.assertIn('warnings', result)


class TestBetTracker(unittest.TestCase):
    """Test bet tracker module"""
    
    def test_get_all_bets(self):
        """Test getting all bets"""
        from bet_tracker import get_all_bets
        
        bets = get_all_bets()
        self.assertIsInstance(bets, list)
    
    def test_get_yesterdays_bets(self):
        """Test getting yesterday's bets"""
        from bet_tracker import get_yesterdays_bets
        
        bets = get_yesterdays_bets()
        self.assertIsInstance(bets, list)
    
    def test_calculate_roi(self):
        """Test ROI calculation"""
        from bet_tracker import calculate_roi
        
        roi = calculate_roi([])
        self.assertIsInstance(roi, dict)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
