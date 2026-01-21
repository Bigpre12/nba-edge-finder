#!/usr/bin/env python3
"""
Simple test to verify the app can start without errors.
Run this before deploying to catch startup issues.
"""

import sys

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from flask import Flask
        print("[OK] Flask imported")
        
        from nba_engine import check_for_edges, get_all_active_players
        print("[OK] nba_engine imported")
        
        from line_tracker import track_line_changes
        print("[OK] line_tracker imported")
        
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            print("[OK] APScheduler imported")
        except ImportError:
            print("[WARN] APScheduler not available (optional)")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_app_creation():
    """Test that Flask app can be created."""
    print("\nTesting app creation...")
    try:
        # Import app module
        import app
        print("[OK] App module imported")
        
        # Check if app exists
        if hasattr(app, 'app'):
            print("[OK] Flask app created")
            return True
        else:
            print("[FAIL] Flask app not found")
            return False
    except Exception as e:
        print(f"[FAIL] App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gunicorn():
    """Test that gunicorn can find the app."""
    print("\nTesting gunicorn compatibility...")
    try:
        import app
        if hasattr(app, 'app'):
            print("[OK] App is accessible as 'app.app' (gunicorn compatible)")
            return True
        return False
    except Exception as e:
        print(f"[FAIL] Gunicorn test failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Flask App Startup Test")
    print("=" * 50)
    
    results = []
    results.append(test_imports())
    results.append(test_app_creation())
    results.append(test_gunicorn())
    
    print("\n" + "=" * 50)
    if all(results):
        print("[SUCCESS] All tests passed! App should start successfully.")
        sys.exit(0)
    else:
        print("[FAIL] Some tests failed. Check errors above.")
        sys.exit(1)
