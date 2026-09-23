set -e
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
python -m uvicorn app.main:app --host $HOST --port $PORT --app-dir backend
