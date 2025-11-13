# Tests - Documentation

## Purpose
The `tests` directory contains test files for the backend application.

## Test Structure
Tests should mirror the application structure:
- `test_api/`: Tests for API routes
- `test_services/`: Tests for services
- `test_models/`: Tests for models
- `test_core/`: Tests for core functionality

## Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api/test_people.py
```

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

