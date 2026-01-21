"""
Simple authentication for private access.
Set AUTH_USERNAME and AUTH_PASSWORD environment variables.
"""
import os
from functools import wraps
from flask import request, Response

def check_auth(username, password):
    """Check if username/password is valid."""
    expected_username = os.environ.get('AUTH_USERNAME', 'admin')
    expected_password = os.environ.get('AUTH_PASSWORD', 'changeme')
    return username == expected_username and password == expected_password

def authenticate():
    """Sends a 401 response that enables basic auth."""
    return Response(
        'Authentication required. Please enter your credentials.',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip auth if no credentials are set (for public access)
        if not os.environ.get('AUTH_USERNAME') and not os.environ.get('AUTH_PASSWORD'):
            return f(*args, **kwargs)
        
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
