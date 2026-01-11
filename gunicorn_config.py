# Gunicorn configuration file for Flask application

# Bind to 0.0.0.0:5000 to make it accessible from outside the container
bind = "0.0.0.0:5000"

# Number of worker processes (typically 2-4 x number of CPU cores)
workers = 4

# Worker class - sync is good for general Flask applications
worker_class = "sync"

# Timeout for worker processes (seconds)
timeout = 120

# Number of requests a worker will process before restarting
max_requests = 1000

# Log level
loglevel = "info"

# Access log file
accesslog = "-"

# Error log file
errorlog = "-"

# Enable graceful shutdown
graceful_timeout = 30

# Keep alive connections
keepalive = 2
