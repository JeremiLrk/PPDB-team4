#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/server"
FRONTEND_DIR="$PROJECT_DIR/client"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="python3.11"

REBUILD=false
INSTALL=false
CLEAN=false
RESTART=false
QUIET=false
SEED=false

# --- Parse parameters ---
for arg in "$@"
do
    case $arg in
        --rebuild)
        REBUILD=true
        shift
        ;;
        --install)
        INSTALL=true
        shift
        ;;
        --clean)
        CLEAN=true
        shift
        ;;
        --restart)
        RESTART=true
        shift
        ;;
        --quiet)
        QUIET=true
        shift
        ;;
        --seed)
        SEED=true
        shift
        ;;
        --python=*)
        PYTHON_BIN="${arg#*=}"
        shift
        ;;
    esac
done

# --- Logging helpers ---
# info: always shown
# detail: hidden with --quiet
info()   { echo -e "$1"; }
detail() { [ "$QUIET" = false ] && echo -e "$1" || true; }

# --- Quiet mode: redirect command details to /dev/null ---
if [ "$QUIET" = true ]; then
    DEVNULL=">/dev/null 2>&1"
    PIPE_NULL() { "$@" > /dev/null 2>&1; }
else
    DEVNULL=""
    PIPE_NULL() { "$@"; }
fi

info "\033[1;34mStarting PPDB project...\033[0m"
[ "$QUIET" = true ] && info "\033[2m(quiet mode — only essential output shown)\033[0m"
[ "$SEED"  = true ] && info "\033[33mSeed mode enabled — database will be seeded on startup.\033[0m"

cd "$PROJECT_DIR" || exit 1

# --- Restart mode ---
if [ "$RESTART" = true ]; then
    info "\033[33mStopping old processes...\033[0m"
    pkill -f "python.*wsgi" || true
    pkill -f vite           || true
    sleep 2
fi

# --- Clean mode ---
if [ "$CLEAN" = true ]; then
    info "\033[33mCleaning venv and node_modules...\033[0m"
    rm -rf "$VENV_DIR"
    rm -rf "$FRONTEND_DIR/node_modules"
fi

# --- Rebuild venv ---
if [ "$REBUILD" = true ] || [ ! -d "$VENV_DIR" ]; then
    info "\033[32mCreating virtual environment with $PYTHON_BIN...\033[0m"
    rm -rf "$VENV_DIR"
    PIPE_NULL $PYTHON_BIN -m venv "$VENV_DIR"
fi

# --- Activate venv ---
source "$VENV_DIR/bin/activate"

# --- Install backend dependencies ---
if [ "$INSTALL" = true ] || [ "$REBUILD" = true ]; then
    info "\033[32mInstalling backend dependencies...\033[0m"
    PIPE_NULL pip install --upgrade pip
    PIPE_NULL pip install -r requirements.txt
fi

# --- Install frontend dependencies ---
if [ "$INSTALL" = true ] || [ "$CLEAN" = true ]; then
    info "\033[32mInstalling frontend dependencies...\033[0m"
    cd "$FRONTEND_DIR" || exit 1
    PIPE_NULL npm install
    cd "$PROJECT_DIR" || exit 1
fi

# --- Start PostgreSQL ---
detail "\033[32mStarting PostgreSQL...\033[0m"
sudo systemctl is-active --quiet postgresql || sudo systemctl start postgresql

# --- Seed env vars ---
SEED_ENV=""
if [ "$SEED" = true ]; then
    SEED_ENV="SEED_ON_STARTUP=1"
fi
VERBOSE_SEED_ENV=""
if [ "$QUIET" = true ]; then
    VERBOSE_SEED_ENV="SEED_VERBOSE=0"
fi

# --- Start Backend ---
info "\033[34mStarting backend...\033[0m"
cd "$PROJECT_DIR" || exit 1
env $SEED_ENV $VERBOSE_SEED_ENV stdbuf -oL python -m server.wsgi 2>&1 | tee "$PROJECT_DIR/backend.log" &
BACKEND_PID=$!
detail "\033[35mBackend PID: $BACKEND_PID (logs: backend.log)\033[0m"

# --- Start Frontend ---
info "\033[34mStarting frontend...\033[0m"
cd "$FRONTEND_DIR" || exit 1
if [ "$QUIET" = true ]; then
    stdbuf -oL npm run dev 2>&1 | grep -E "(Local|Network|error|Error|warn|WARN)" | tee "$PROJECT_DIR/frontend.log" &
else
    stdbuf -oL npm run dev 2>&1 | tee "$PROJECT_DIR/frontend.log" &
fi
FRONTEND_PID=$!
detail "\033[35mFrontend PID: $FRONTEND_PID (logs: frontend.log)\033[0m"

info "\033[32mBackend:  http://127.0.0.1:5000\033[0m"
info "\033[32mFrontend: http://localhost:5173\033[0m"

trap "echo -e '\033[31mStopping processes...\033[0m'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
