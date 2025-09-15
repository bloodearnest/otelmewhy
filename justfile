# Top-level justfile for meme generator project

# Default recipe
default:
    @just --list

# Run both backend and frontend Django servers concurrently
run:
    @echo "Starting both backend (port 8001) and frontend (port 8000) servers..."
    @echo "Backend will be available at: http://127.0.0.1:8001"
    @echo "Frontend will be available at: http://127.0.0.1:8000"
    @echo "Press Ctrl+C to stop both servers"
    just run-parallel

# Run both servers in parallel using background processes
run-parallel:
    #!/usr/bin/env bash
    set -euo pipefail

    # Function to cleanup background processes on exit
    cleanup() {
        echo ""
        echo "Stopping servers..."
        jobs -p | xargs -r kill
        wait
        echo "All servers stopped."
    }
    trap cleanup EXIT INT TERM

    # Start backend in background
    echo "Starting backend server..."
    cd backend && uv run python manage.py runserver 8001 &
    BACKEND_PID=$!

    # Wait a moment for backend to start
    sleep 2

    # Start frontend in background
    echo "Starting frontend server..."
    cd frontend && uv run python manage.py runserver 8000 &
    FRONTEND_PID=$!

    # Wait for both processes
    echo "Both servers running. Press Ctrl+C to stop."
    wait

# Run only the backend server
run-backend:
    @echo "Starting backend server on port 8001..."
    just backend/run

# Run only the frontend server
run-frontend:
    @echo "Starting frontend server on port 8000..."
    just frontend/run

# Run tests for specific projects or both (usage: just test [backend] [frontend])
test *projects="backend frontend":
    #!/usr/bin/env bash
    for project in {{ projects }}; do
        echo "Running $project tests..."
        just $project/test
    done

# Run checks for specific projects or both (usage: just check [backend] [frontend])
check *projects="backend frontend":
    #!/usr/bin/env bash
    for project in {{ projects }}; do
        echo "Running $project checks..."
        just $project/check
    done

# Run database migrations for backend
migrate:
    @echo "Running backend database migrations..."
    just backend/migrate

# Format code for specific projects or both (usage: just format [backend] [frontend])
format *projects="backend frontend":
    #!/usr/bin/env bash
    for project in {{ projects }}; do
        echo "Formatting $project code..."
        just $project/format
    done

# Lint code for specific projects or both (usage: just lint [backend] [frontend])
lint *projects="backend frontend":
    #!/usr/bin/env bash
    for project in {{ projects }}; do
        echo "Linting $project code..."
        just $project/lint
    done

# Install/update dependencies for specific projects or both (usage: just sync [backend] [frontend])
sync *projects="backend frontend":
    #!/usr/bin/env bash
    for project in {{ projects }}; do
        echo "Syncing $project dependencies..."
        just $project/sync
    done

# Show project status and URLs
status:
    @echo "=== Meme Generator Project Status ==="
    @echo ""
    @echo "Backend Project (API):"
    @echo "  Location: ./backend/"
    @echo "  Port: 8001"
    @echo "  Health check: http://127.0.0.1:8001/"
    @echo "  API endpoint: http://127.0.0.1:8001/api/create/"
    @echo ""
    @echo "Frontend Project (Web UI):"
    @echo "  Location: ./frontend/"
    @echo "  Port: 8000"
    @echo "  Web UI: http://127.0.0.1:8000/"
    @echo ""
    @echo "To run both: just run"
    @echo "To run individually: just run-backend or just run-frontend"

# Clean up generated files in both projects
clean:
    @echo "Cleaning up generated files..."
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.sqlite3-wal" -delete 2>/dev/null || true
    find . -name "*.sqlite3-shm" -delete 2>/dev/null || true
    @echo "Cleanup complete."
