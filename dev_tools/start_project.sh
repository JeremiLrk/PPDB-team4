#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

PROJECT_DIR="$HOME/Documents/PPDB/PPDB-team4"
BACKEND_DIR="$PROJECT_DIR/server"
FRONTEND_DIR="$PROJECT_DIR/client"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_BIN="python3.11"

REBUILD=false
INSTALL=false
CLEAN=false
RESTART=false

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
        --python=*)
        PYTHON_BIN="${arg#*=}"
        shift
        ;;
    esac
done

echo -e "\033[1;34mStarting PPDB project...\033[0m"

cd "$PROJECT_DIR" || exit 1

# --- Restart mode ---
if [ "$RESTART" = true ]; then
    echo -e "\033[33mStopping old processes...\033[0m"
    pkill -f "python.*wsgi"
    pkill -f vite
    sleep 2
fi

# --- Clean mode ---
if [ "$CLEAN" = true ]; then
    echo -e "\033[33mCleaning venv and node_modules...\033[0m"
    rm -rf "$VENV_DIR"
    rm -rf "$FRONTEND_DIR/node_modules"
fi

# --- Rebuild venv ---
if [ "$REBUILD" = true ] || [ ! -d "$VENV_DIR" ]; then
    echo -e "\033[32mCreating virtual environment with $PYTHON_BIN...\033[0m"
    rm -rf "$VENV_DIR"
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# --- Activate venv ---
source "$VENV_DIR/bin/activate"

# --- Install backend dependencies ---
if [ "$INSTALL" = true ] || [ "$REBUILD" = true ]; then
    echo -e "\033[32mInstalling backend dependencies...\033[0m"
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# --- Install frontend dependencies ---
if [ "$INSTALL" = true ] || [ "$CLEAN" = true ]; then
    echo -e "\033[32mInstalling frontend dependencies...\033[0m"
    cd "$FRONTEND_DIR" || exit 1
    npm install
    cd "$PROJECT_DIR" || exit 1
fi

# --- Start PostgreSQL ---
echo -e "\033[32mStarting PostgreSQL...\033[0m"
sudo systemctl is-active --quiet postgresql || sudo systemctl start postgresql

# --- Start Backend ---
echo -e "\033[34mStarting backend...\033[0m"
cd "$PROJECT_DIR" || exit 1
stdbuf -oL python -m server.wsgi 2>&1 | tee "$PROJECT_DIR/backend.log" &
BACKEND_PID=$!
echo -e "\033[35mBackend PID: $BACKEND_PID (logs: backend.log)\033[0m"

# --- Start Frontend ---
echo -e "\033[34mStarting frontend...\033[0m"
cd "$FRONTEND_DIR" || exit 1
stdbuf -oL npm run dev 2>&1 | tee "$PROJECT_DIR/frontend.log" &
FRONTEND_PID=$!
echo -e "\033[35mFrontend PID: $FRONTEND_PID (logs: frontend.log)\033[0m"

echo -e "\033[32mBackend: http://127.0.0.1:5000\033[0m"
echo -e "\033[32mFrontend: http://localhost:5173\033[0m"

trap "echo -e '\033[31mStopping processes...\033[0m'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
