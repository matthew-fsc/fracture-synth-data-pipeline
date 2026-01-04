# Contributing to Synthetic Data Pipeline

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting (line length: 100)
- Use Ruff for linting
- Use type hints where possible
- Write docstrings for all public functions and classes

## Testing

- Write tests for all new features
- Ensure all tests pass: `pytest tests/ -v`
- Aim for >80% code coverage
- Add integration tests for new pipeline components

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Ensure all tests pass and code is formatted
4. Update documentation as needed
5. Submit a pull request with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/examples if applicable

## Issue Management

- Check [issues.md](issues.md) for existing issues
- Create new issues for bugs or feature requests
- Use appropriate labels
- Provide clear reproduction steps for bugs

## Adding New Features

When adding new features:

1. Update relevant schemas if data structures change
2. Add validation logic if needed
3. Update tests
4. Update documentation (README, docstrings)
5. Add to issues.md if it's a significant enhancement

## Questions?

Open an issue or contact the maintainers.

