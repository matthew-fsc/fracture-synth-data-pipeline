# Testing Guide

This directory contains tests for the synthetic data generation pipeline.

## Running Tests

### Run All Tests

```bash
# From repository root
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_pipeline.py -v
pytest tests/test_schema_validator.py -v
pytest tests/test_company_profiler.py -v
```

### Run Tests with Coverage

```bash
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

Coverage reports are generated in:
- HTML: `htmlcov/index.html`
- Terminal: Displayed in console
- XML: `coverage.xml` (for CI integration)

### Run Only Unit Tests

```bash
pytest tests/ -v -m "unit"
```

### Run Only Integration Tests

```bash
pytest tests/ -v -m "integration"
```

## Test Structure

### Unit Tests

- **`test_pipeline.py`**: Tests for the optimized pipeline flow
  - Basic pipeline functionality
  - JSON and CSV output validation
  - Schema validation integration
  - Realism validation (with/without)
  - Scenario generation
  - Pipeline optimizations (shared validator, timestamp consistency)

- **`test_schema_validator.py`**: Tests for schema validation
  - Schema validator initialization
  - Company profile validation
  - System manifest validation

- **`test_company_profiler.py`**: Tests for company profile generation
  - Profile generation
  - Operational metrics
  - KPI generation
  - Industry-specific profiles

### Fixtures

- **`conftest.py`**: Shared pytest fixtures
  - `temp_output_dir`: Temporary directory for test outputs
  - `sample_company_profile`: Mock company profile
  - `sample_system_manifest`: Mock system manifest
  - `mock_config`: Mock configuration with Azure credentials
  - `mock_config_no_azure`: Mock configuration without Azure

## Test Coverage Goals

- **Target**: 70%+ code coverage
- **Critical paths**: 90%+ coverage
- **Edge cases**: All major error paths tested

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure

```python
"""Tests for module X."""

import pytest
from unittest.mock import Mock, patch

from tests.conftest import temp_output_dir, sample_company_profile


class TestModuleX:
    """Test module X functionality."""
    
    def test_basic_functionality(self, temp_output_dir):
        """Test basic functionality."""
        # Arrange
        # Act
        # Assert
        pass
    
    @patch('module_x.ExternalDependency')
    def test_with_mock(self, mock_dependency, sample_company_profile):
        """Test with mocked dependencies."""
        # Setup mock
        mock_dependency.return_value.method.return_value = "result"
        
        # Run test
        result = function_under_test(sample_company_profile)
        
        # Assert
        assert result == "expected"
        mock_dependency.assert_called_once()
```

### Best Practices

1. **Use fixtures** from `conftest.py` for common setup
2. **Mock external dependencies** (Azure, OpenAI, file I/O)
3. **Test both success and failure paths**
4. **Use descriptive test names** that explain what is being tested
5. **Keep tests fast** - use mocks instead of real API calls
6. **Test one thing per test** - single assertion or related assertions
7. **Clean up** - use temporary directories and fixtures

## Test Markers

Tests can be marked with:

- `@pytest.mark.unit`: Fast, isolated unit tests
- `@pytest.mark.integration`: Integration tests (may require external deps)
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.requires_azure`: Tests requiring Azure credentials
- `@pytest.mark.requires_openai`: Tests requiring OpenAI/Azure OpenAI

### Running Tests by Marker

```bash
# Run only unit tests
pytest tests/ -v -m "unit"

# Skip slow tests
pytest tests/ -v -m "not slow"

# Run integration tests
pytest tests/ -v -m "integration"
```

## CI/CD Integration

Tests are automatically run in CI/CD pipelines:

- **Unit tests**: Run on every commit
- **Integration tests**: Run on pull requests
- **Coverage**: Must meet 70% threshold
- **All tests must pass** before merge

## Troubleshooting

### Import Errors

If you encounter import errors, ensure you're running tests from the repository root:

```bash
cd /path/to/fracture-synth-data-pipeline
pytest tests/
```

### Mock Issues

If mocks aren't working correctly:

1. Check that you're patching the correct import path
2. Use `@patch('src.module.Class')` not `@patch('module.Class')`
3. Ensure mock return values match expected types

### Temporary Files

Tests use `temp_output_dir` fixture which automatically cleans up. If you see leftover files:

1. Check that fixtures are being used correctly
2. Ensure `yield` is used in fixtures (not `return`)
3. Manually clean up if necessary in `finally` blocks

## Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Ensure tests pass** before submitting PR
3. **Maintain coverage** - add tests for new code paths
4. **Update this README** if adding new test patterns or fixtures

