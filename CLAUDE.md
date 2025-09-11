# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repo is for a workshop on opentelemetry with python

It will contain a simple toy django application that generates memes, by combining top/bottom text with images.

## Getting Started

Since this is an empty repository, you'll need to:

1. Initialize the project with the appropriate language and framework structure
2. Set up build tools, dependency management, and development workflows
3. Configure testing frameworks and CI/CD as needed

## Development Guidelines

This is a python project, a set of toy django webs apps for teaching a workshop on opentelemetry

It should use uv for tooling, and use python 3.13
It should use normal django idioms, using function based views, not class based views.
It should use gunicorn for serving, whitenoise for staticfiles, httpx for http requests, and pytest for tests.
It should use a sqlite db, but set up in WAL mode and other settings for concurrent access.
It should only use vanilla js, with no js tooling, and native js module loading.
It should use pillow for the image manipulation

It should *not* have any opentelemetry packages installed by default. The workshop participants will be adding that.

Python style:
 - use ruff defaults for formatting
 - never use relative imports, always fully qualify
 - never use unittest.mock.
 - prefer full functional tests where possible


## Common Commands

