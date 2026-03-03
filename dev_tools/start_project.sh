#!/bin/bash

PROJECT_DIR="$HOME/WebstormProjects/PPDB-team4"
BACKEND_DIR="$PROJECT_DIR/server"
FRONTEND_DIR="$PROJECT_DIR/client"
VENV_DIR="$PROJECT_DIR/venv"
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

echo "Starting PPDB project..."

cd "$PROJECT_DIR" || exit 1

# --- Restart mode ---
if [ "$RESTART" = true ]; then
    echo "Stopping old processes..."
    pkill -f app.py
    pkill -f vite
    sleep 2
fi

# --- Clean mode ---
if [ "$CLEAN" = true ]; then
    echo "Cleaning venv and node_modules..."
    rm -rf "$VENV_DIR"
    rm -rf "$FRONTEND_DIR/node_modules"
fi

# --- Rebuild venv ---
if [ "$REBUILD" = true ] || [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment with $PYTHON_BIN..."
    rm -rf "$VENV_DIR"
    $PYTHON_BIN -m venv venv
fi

# --- Activate venv ---
source "$VENV_DIR/bin/activate"

# --- Install backend dependencies ---
if [ "$INSTALL" = true ] || [ "$REBUILD" = true ]; then
    echo "Installing backend dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# --- Install frontend dependencies ---
if [ "$INSTALL" = true ] || [ "$CLEAN" = true ]; then
    echo "Installing frontend dependencies..."
    cd "$FRONTEND_DIR" || exit 1
    npm install
    cd "$PROJECT_DIR" || exit 1
fi

# --- Start PostgreSQL ---
sudo systemctl start postgresql

# --- Start Backend ---
echo "Starting backend..."
cd "$BACKEND_DIR" || exit 1
$PYTHON_BIN app.py &
BACKEND_PID=$!

# --- Start Frontend ---
echo "Starting frontend..."
cd "$FRONTEND_DIR" || exit 1
npm run dev &
FRONTEND_PID=$!

echo "Backend: http://127.0.0.1:5000"
echo "Frontend: http://localhost:5173"

trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
