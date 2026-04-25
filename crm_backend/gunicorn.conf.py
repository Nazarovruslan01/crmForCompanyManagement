"""Gunicorn production configuration."""

import multiprocessing

bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"

# Workers: 2-4 x $(NUM_CORES) — capped at 8 for I/O-bound Django
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
threads = 4

# Prevent memory leaks in long-running workers
max_requests = 10000
max_requests_jitter = 1000
timeout = 60
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s %(M)s %(request_id)s'

# Server mechanics
preload_app = True

# Process naming
proc_name = "crm_backend"


def post_fork(server: object, worker: object) -> None:
    """Reset RNG after fork to avoid shared state."""
    import random

    random.seed()
