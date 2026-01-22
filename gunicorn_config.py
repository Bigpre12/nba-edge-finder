# Gunicorn configuration file
import os

# Bind to the port provided by the platform (Render, Railway, etc.)
# Most platforms set PORT environment variable
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Worker configuration - use 1 worker to reduce crashes and memory usage
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increased timeout for slow API calls
keepalive = 5
graceful_timeout = 30

# Worker lifecycle - restart workers after N requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Prevent worker crashes from killing the whole app
worker_tmp_dir = "/dev/shm"  # Use shared memory if available, falls back to /tmp

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "thepropauditor"

# Preload app for faster startup (but can cause issues with some imports)
preload_app = False

# Better error handling
def on_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker {worker.pid} exited")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker {worker.pid} received SIGABRT - aborting gracefully")
