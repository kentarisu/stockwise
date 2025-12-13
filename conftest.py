"""
Global pytest configuration and fixtures for the StockWise Django project.
"""
import pytest
import os
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase


def pytest_configure():
    """Configure Django settings for pytest."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
    django.setup()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Set up the database for testing."""
    with django_db_blocker.unblock():
        call_command('migrate', verbosity=0, interactive=False)


@pytest.fixture
def db_access_without_rollback_and_truncate(request, django_db_setup, django_db_blocker):
    """Allow database access without rollback and truncate for specific tests."""
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture
def client():
    """Django test client fixture."""
    from django.test import Client
    return Client()


@pytest.fixture
def admin_client():
    """Django test client with admin user."""
    from django.test import Client
    from core.models import AppUser
    from passlib.hash import bcrypt
    
    client = Client()
    
    # Create admin user
    admin_user = AppUser.objects.create(
        username='admin',
        password=bcrypt.hash('admin123'),
        phone_number='1234567890',
        role='Admin'
    )
    
    # Mock authentication by setting session
    session = client.session
    session['user_id'] = admin_user.user_id
    session['app_role'] = 'admin'
    session.save()
    
    return client, admin_user


@pytest.fixture
def secretary_client():
    """Django test client with secretary user."""
    from django.test import Client
    from core.models import AppUser
    from passlib.hash import bcrypt
    
    client = Client()
    
    # Create secretary user
    secretary_user = AppUser.objects.create(
        username='secretary',
        password=bcrypt.hash('secretary123'),
        phone_number='0987654321',
        role='Secretary'
    )
    
    # Mock authentication by setting session
    session = client.session
    session['user_id'] = secretary_user.user_id
    session['app_role'] = 'secretary'
    session.save()
    
    return client, secretary_user


@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    from core.models import Product
    return Product.objects.create(
        name='Test Apple',
        variant='Red',
        status='active',
        price=50.00,
        cost=30.00,
        size='120',
        stock=100,
        low_stock_threshold=10,
        supplier='Test Supplier'
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    from core.models import AppUser
    from passlib.hash import bcrypt
    return AppUser.objects.create(
        username='testuser',
        password=bcrypt.hash('testpass123'),
        phone_number='1234567890',
        role='Secretary'
    )
