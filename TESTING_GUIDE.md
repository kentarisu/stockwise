# StockWise Testing Guide

This guide explains how to run tests for the StockWise Django application using pytest.

## Overview

The StockWise application now has a comprehensive test suite using pytest and pytest-django. The test suite includes:

- **Basic Tests**: Core functionality tests for models, views, and calculations
- **Integration Tests**: End-to-end workflow tests
- **Model Tests**: Django model functionality tests
- **View Tests**: Django view functionality tests
- **Management Command Tests**: Django management command tests
- **Utility Tests**: Helper function and business logic tests

## Prerequisites

Make sure you have the required packages installed:

```bash
pip install -r requirements.txt
```

Required packages:
- pytest==8.0.0
- pytest-django==4.8.0
- pytest-cov==4.1.0
- factory-boy==3.3.0

## Running Tests

### 1. Run All Tests

```bash
python -m pytest tests/ -v
```

### 2. Run Specific Test Files

```bash
# Run basic tests only
python -m pytest tests/test_basic.py -v

# Run integration tests only
python -m pytest tests/test_integration.py -v

# Run model tests only
python -m pytest tests/test_models.py -v

# Run view tests only
python -m pytest tests/test_views.py -v
```

### 3. Run Tests with Coverage

```bash
python -m pytest tests/ --cov=core --cov-report=html --cov-report=term-missing
```

### 4. Run Fast Tests Only (Skip Slow Tests)

```bash
python -m pytest tests/ -m "not slow"
```

### 5. Using the Test Runner Script

```bash
# Run basic tests
python run_tests.py --type basic

# Run all tests with coverage
python run_tests.py --type all

# Run specific test file
python run_tests.py --type specific --test tests/test_basic.py
```

## Test Structure

### Test Files

- **`tests/test_basic.py`**: Basic functionality tests (23 tests)
  - Model creation and validation
  - View redirects and basic functionality
  - Calculation logic
  - Data validation
  - Model relationships

- **`tests/test_integration.py`**: Integration tests (10 tests)
  - Complete product workflows
  - Sales calculations with multiple products
  - FIFO stock management
  - SMS notification workflows
  - User authentication and authorization
  - Data integrity and constraints
  - Business logic and edge cases

- **`tests/test_models.py`**: Django model tests (17 tests)
  - Product model tests
  - User model tests
  - Stock addition model tests
  - Sale model tests
  - SMS model tests
  - Report model tests

- **`tests/test_views.py`**: Django view tests (24 tests)
  - Authentication views
  - Product management views
  - Stock management views
  - Sales views
  - Dashboard views
  - Reports views
  - Profile views
  - SMS views
  - Print views
  - Permission tests

- **`tests/test_management_commands.py`**: Management command tests (11 tests)
  - SMS notification commands
  - Data import commands
  - User creation commands
  - Product management commands
  - Error handling tests

- **`tests/test_utils.py`**: Utility function tests (15 tests)
  - Pricing AI functionality
  - SMS service functionality
  - Stock management utilities
  - Sales calculations
  - Data validation
  - Report generation

### Test Categories

#### Basic Tests (test_basic.py)
- **TestBasicModels**: Core model functionality
- **TestBasicViews**: View redirects and basic functionality
- **TestBasicCalculations**: Mathematical calculations
- **TestBasicDataValidation**: Input validation
- **TestBasicModelRelationships**: Model relationships

#### Integration Tests (test_integration.py)
- **TestProductWorkflow**: Complete product lifecycle
- **TestSalesCalculations**: Multi-product sales scenarios
- **TestStockManagement**: FIFO stock management
- **TestSMSIntegration**: SMS notification workflows
- **TestUserAuthentication**: User roles and permissions
- **TestDataIntegrity**: Database constraints
- **TestBusinessLogic**: Edge cases and business rules

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = stockwise_py.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=core
    --cov-report=html
    --cov-report=term-missing
    --reuse-db
testpaths = .
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### conftest.py
Global pytest configuration with fixtures for:
- Database setup
- Test clients (admin, secretary)
- Sample data (products, users)
- Authentication helpers

## Test Fixtures

The test suite includes several useful fixtures:

- **`client`**: Basic Django test client
- **`admin_client`**: Test client with admin user
- **`secretary_client`**: Test client with secretary user
- **`sample_product`**: Pre-created test product
- **`sample_user`**: Pre-created test user

## Writing New Tests

### 1. Basic Test Structure

```python
import pytest
from decimal import Decimal
from core.models import Product

class TestNewFeature:
    """Test cases for new feature."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('25.00')
        )
        
        # Act
        result = some_function(product)
        
        # Assert
        assert result == expected_value
```

### 2. Using Fixtures

```python
def test_with_fixture(self, sample_product, admin_client):
    """Test using fixtures."""
    client, user = admin_client
    
    response = client.get('/some-url/')
    assert response.status_code == 200
```

### 3. Testing Views

```python
def test_view_functionality(self, admin_client):
    """Test view functionality."""
    client, user = admin_client
    
    response = client.get(reverse('view_name'))
    assert response.status_code == 200
```

## Test Results

### Current Test Status

- **Total Tests**: 100+ tests
- **Basic Tests**: 23 tests (all passing)
- **Integration Tests**: 10 tests (all passing)
- **Model Tests**: 17 tests (most passing)
- **View Tests**: 24 tests (most passing)
- **Management Command Tests**: 11 tests (most passing)
- **Utility Tests**: 15 tests (most passing)

### Coverage

Run tests with coverage to see code coverage:

```bash
python -m pytest tests/ --cov=core --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

## Troubleshooting

### Common Issues

1. **Database Issues**: Tests use a separate test database
2. **Import Errors**: Make sure all dependencies are installed
3. **Authentication**: Use the provided fixtures for authenticated tests
4. **URL Issues**: Check that URL names match those in `core/urls.py`

### Debugging Tests

```bash
# Run with verbose output
python -m pytest tests/test_basic.py -v -s

# Run with full traceback
python -m pytest tests/test_basic.py --tb=long

# Run specific test
python -m pytest tests/test_basic.py::TestBasicModels::test_product_creation -v
```

## Continuous Integration

The test suite is designed to work with CI/CD systems:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ --cov=core --cov-report=xml

# Generate coverage report
coverage xml
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: Leverage pytest fixtures for common setup
5. **Mock External Services**: Use mocks for external dependencies
6. **Test Edge Cases**: Include boundary conditions and error cases
7. **Keep Tests Fast**: Avoid slow operations in tests

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain or improve test coverage
4. Update this documentation if needed
5. Run the full test suite before submitting changes

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Coverage](https://pytest-cov.readthedocs.io/)
