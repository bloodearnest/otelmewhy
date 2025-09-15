# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repo is for a workshop on opentelemetry with python

It contains two separate Django applications for teaching a workshop on opentelemetry:
- **Backend**: API service that generates memes by combining top/bottom text with images
- **Frontend**: Web UI that provides a form to create memes via the backend API

## Project Structure

```
/
├── backend/           # Django API service (port 8000)
│   ├── manage.py
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── backend/       # Django settings
│   └── memes/         # Memes API app
└── frontend/          # Django web UI service (port 8001)
    ├── manage.py
    ├── pyproject.toml
    ├── uv.lock
    ├── frontend/      # Django settings
    └── ui/            # Web UI app
```

## Getting Started

### Backend Service
```bash
cd backend
uv sync
uv run python manage.py runserver 8000
```

### Frontend Service
```bash
cd frontend
uv sync
BACKEND_URL=http://127.0.0.1:8000 uv run python manage.py runserver 8001
```

Then visit http://127.0.0.1:8001 for the web UI.

## Development Guidelines

This is a Python project with two separate Django sites for teaching a workshop on OpenTelemetry.

**Backend Dependencies**: Django, Pillow, gunicorn, whitenoise, django-cors-headers
**Frontend Dependencies**: Django, httpx, gunicorn, whitenoise

Both services:
- Use uv for tooling and Python 3.13
- Use normal Django idioms with function-based views (not class-based views)
- Use gunicorn for serving, whitenoise for static files, pytest for tests
- Backend uses SQLite in WAL mode for concurrent access
- Use vanilla JS with no JS tooling, native JS module loading
- Should *not* have any OpenTelemetry packages by default (workshop participants add them)

Python style:
- Use ruff defaults for formatting
- Never use relative imports, always fully qualify
- Never use unittest.mock
- Prefer full functional tests where possible

## Common Commands

### Backend
```bash
cd backend
uv run python manage.py test           # Run tests
uv run python manage.py migrate       # Apply migrations
uv run ruff format .                   # Format code
```

### Frontend
```bash
cd frontend
uv run python manage.py test           # Run tests
uv run python manage.py collectstatic  # Collect static files
uv run ruff format .                   # Format code
```

