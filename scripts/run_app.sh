set -e

cd "$(dirname "$0")/.."

# Load env vars if .env exists
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

# Choose python executable
PYEXEC=python
if ! command -v "$PYEXEC" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYEXEC=python3
  else
    echo "No python interpreter found (python/python3)" >&2
    exit 1
  fi
fi

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  "$PYEXEC" -m venv venv
fi

. venv/bin/activate

echo "Installing requirements..."
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
elif [ -f "requirements-mac.txt" ]; then
  pip install -r requirements-mac.txt
elif [ -f "requirements-linux.txt" ]; then
  pip install -r requirements-linux.txt
else
  echo "No requirements file found."
fi

echo "Starting API"
"$PYEXEC" -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload