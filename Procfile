# Procfile for Render deployment
# Uses gunicorn as production WSGI server
# - workers: Number of worker processes (2 for small-medium traffic)
# - threads: Threads per worker (2 for I/O-bound operations)
# - timeout: Request timeout in seconds (120 for large APK uploads/downloads)
# - bind: Listen on all interfaces, port from $PORT env var (set by Render)
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
