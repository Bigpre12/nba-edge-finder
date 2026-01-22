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
timeout = 360  # 6 minutes - must be longer than edge calculation timeout (5 min) to allow graceful timeout
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
    import traceback
    traceback.print_exc()

def when_ready(server):
    """Called just after the server is started."""
    print(f"Server is ready. Spawning {server.num_workers} worker(s).")

def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting server...")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    print(f"Worker {worker.pid} initialized")

def worker_exit(server, worker):
    """Called just after a worker has been exited, in the master process."""
    print(f"Worker {worker.pid} exited (master process)")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"Worker {worker.pid} interrupted")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Server reloading workers")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker {worker.pid} forked")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Master process forking")
    print(f"Worker {worker.pid} received SIGABRT - aborting gracefully")