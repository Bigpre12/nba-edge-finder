# Gunicorn configuration file
import os

# Bind to the port provided by the platform (Render, Railway, etc.)
# Most platforms set PORT environment variable
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Increased timeout for slow startup
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "thepropauditor"

# Preload app for faster startup
preload_app = False
