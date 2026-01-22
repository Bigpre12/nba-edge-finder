# Gunicorn configuration file
import os

# Bind to the port provided by the platform (Render, Railway, etc.)
# Most platforms set PORT environment variable
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Worker configuration - use 1 worker to reduce crashes and memory usage
# CRITICAL: Only 1 worker to prevent multiple worker crashes
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Reduced to 2 minutes - edge calculation has its own 5-minute timeout
keepalive = 5
graceful_timeout = 30

# Memory management - restart workers more frequently to prevent memory leaks
max_requests = 100  # Restart after 100 requests to free memory and prevent leaks
max_requests_jitter = 10

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
