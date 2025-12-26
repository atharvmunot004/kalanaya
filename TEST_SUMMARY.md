# Test Summary

## Overview
This document summarizes the test suite for the Kalanaya project. The test suite includes both unit tests and end-to-end tests covering all major components of the application.

## Test Structure

### Unit Tests

#### Pipeline Tests (`tests/pipeline/`)
- **test_level3_validation.py**: Tests for Level 3 validation module
  - ISO 8601 datetime validation
  - Datetime parsing
  - Create event validation
  - Update event validation
  - Delete event validation
  - List events validation
  - Main validate_fields function

- **test_pipeline.py**: Tests for main pipeline module
  - User input processing
  - Intent classification flow
  - Field extraction flow
  - Validation flow
  - Payload conversion

#### Actions Tests (`tests/actions/`)
- **test_calendar_actions.py**: Tests for calendar actions
  - RFC3339 parsing helpers
  - Create event functionality
  - List events functionality
  - Update event functionality
  - Delete event functionality
  - Find events functionality

#### Router Tests (`tests/router/`)
- **test_router.py**: Tests for router module
  - Route function for different actions
  - Event finding by title
  - Update dictionary building
  - Error handling

#### Utils Tests (`tests/utils/`)
- **test_validators.py**: Tests for validation utilities
  - Intent validation
  - Event parameters validation
  - Error handling

### End-to-End Tests (`tests/`)
- **test_e2e.py**: End-to-end tests
  - Full pipeline flow (create_event)
  - Full pipeline flow (list_events)
  - Low confidence handling
  - Validation failure handling
  - Main module integration

## Test Results

**Total Tests: 72**
- ✅ **72 passed**
- ❌ **0 failed**

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Unit Tests Only
```bash
python -m pytest tests/pipeline/ tests/actions/ tests/router/ tests/utils/ -v
```

### Run End-to-End Tests Only
```bash
python -m pytest tests/test_e2e.py -v
```

### Run Specific Test File
```bash
python -m pytest tests/pipeline/test_level3_validation.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
```

### Using the Test Runner Script
```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py --type unit

# Run end-to-end tests only
python run_tests.py --type e2e

# Run quietly
python run_tests.py --quiet
```

## Test Coverage

The test suite covers:
- ✅ Intent classification (Level 1)
- ✅ Field extraction (Level 2)
- ✅ Validation (Level 3)
- ✅ Pipeline orchestration
- ✅ Calendar actions (CRUD operations)
- ✅ Router logic
- ✅ Utility functions
- ✅ End-to-end flows
- ✅ Error handling
- ✅ Edge cases

## Dependencies

Test dependencies are listed in `requirements.txt`:
- pytest>=7.0.0
- pytest-mock>=3.10.0
- pytest-cov>=4.0.0
- requests-mock>=1.10.0

## Notes

- Tests use mocking to avoid requiring actual Google Calendar API access
- Ollama API calls are mocked to avoid requiring a running Ollama instance
- Speech tests are excluded from the main test suite (require audio hardware)
- All tests are designed to run independently and in parallel

