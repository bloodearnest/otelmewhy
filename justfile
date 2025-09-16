# Top-level justfile for meme generator project
set dotenv-load := true

# Default recipe
default:
    @just --list

# Run servers for specific projects or both (usage: just run [backend] [frontend])
run *projects="backend frontend":
    #!/usr/bin/env bash
    set -euo pipefail

    test -f .env || cp .env.defaults .env
    echo "Starting servers for: {{ projects }}"
    echo "Backend will be available at: http://127.0.0.1:8001"
    echo "Frontend will be available at: http://127.0.0.1:8000"
    echo "Press Ctrl+C to stop servers"

    # Function to cleanup background processes on exit
    cleanup() {
        echo ""
        echo "Stopping servers..."
        jobs -p | xargs -r kill
        wait
        echo "All servers stopped."
    }
    trap cleanup EXIT INT TERM

    # Start each project in background
    for project in {{ projects }}; do
        echo "Starting $project server..."
        just $project/run &
        sleep 1
    done

    # Wait for all processes
    echo "All servers running. Press Ctrl+C to stop."
    wait


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
