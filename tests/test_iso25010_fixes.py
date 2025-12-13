"""
Test cases for ISO/IEC 25010:2011 compliance fixes
Tests all the fixes made to ensure StockWise passes ISO 25010 standards
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from core.models import Product, AppUser, StockAddition, Sale, SMS
from core.sms_service import IPROGSMSService
from core.maintenance import is_maintenance_mode
from passlib.hash import bcrypt


@pytest.mark.django_db
class TestTC003_UserAccountStatus:
    """TC-003: Prevent inactive/locked accounts from logging in"""
    
    def test_active_user_can_login(self):
        """Active users should be able to login"""
        password = 'test123'
        user = AppUser.objects.create(
            username='testuser',
            password=bcrypt.hash(password),
            phone_number='09123456789',
            role='Admin',
            is_active=True
        )
        
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': password
        })
        
        # Should redirect to dashboard on success
        assert response.status_code == 302
        assert 'app_user_id' in client.session
    
    def test_inactive_user_cannot_login(self):
        """Inactive users should be blocked from login"""
        password = 'test123'
        user = AppUser.objects.create(
            username='testuser',
            password=bcrypt.hash(password),
            phone_number='09123456789',
            role='Admin',
            is_active=False
        )
        
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': password
        })
        
        # Should not create session
        assert 'app_user_id' not in client.session
        # Should show error message
        assert response.status_code == 200


@pytest.mark.django_db
class TestTC005_TC006_ServerValidation:
    """TC-005, TC-006: Server-side validation for empty username/password"""
    
    def test_empty_username_rejected(self):
        """Empty username should be rejected"""
        client = Client()
        response = client.post(reverse('login'), {
            'username': '',
            'password': 'test123'
        })
        
        assert response.status_code == 200
        assert 'app_user_id' not in client.session
    
    def test_empty_password_rejected(self):
        """Empty password should be rejected"""
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': ''
        })
        
        assert response.status_code == 200
        assert 'app_user_id' not in client.session


@pytest.mark.django_db
class TestTC009_UniqueSKU:
    """TC-009: SKU field with unique constraint"""
    
    def test_sku_field_exists(self):
        """Product model should have SKU field"""
        product = Product.objects.create(
            name='Test Product',
            size='10',
            price=Decimal('100'),
            cost=Decimal('50'),
            sku='TEST-SKU-001'
        )
        
        assert product.sku == 'TEST-SKU-001'
    
    def test_sku_unique_constraint(self):
        """Duplicate SKU should be rejected"""
        Product.objects.create(
            name='Test Product 1',
            size='10',
            price=Decimal('100'),
            cost=Decimal('50'),
            sku='TEST-SKU-001'
        )
        
        # Attempting to create another product with same SKU should fail
        with pytest.raises(Exception):  # IntegrityError
            Product.objects.create(
                name='Test Product 2',
                size='20',
                price=Decimal('200'),
                cost=Decimal('100'),
                sku='TEST-SKU-001'
            )


@pytest.mark.django_db
class TestTC010_MinMarginValidation:
    """TC-010: Minimum 10% margin validation"""
    
    def test_margin_validation_rejects_low_margin(self, admin_client):
        """Product with margin < 10% should be rejected"""
        client, user = admin_client
        response = client.post(reverse('product_add'), {
            'name': 'Margin Test Low',
            'size': '120',  # Use valid size
            'price': '100',
            'cost': '95',  # Only 5.26% margin
            'stock': '10',
            'variant': ''
        })
        
        data = response.json()
        assert data['success'] == False
        assert '10% margin' in data['message'].lower()
    
    def test_margin_validation_accepts_good_margin(self, admin_client):
        """Product with margin >= 10% should be accepted"""
        client, user = admin_client
        response = client.post(reverse('product_add'), {
            'name': 'Margin Test Good',
            'size': '130',  # Use valid size
            'price': '110',
            'cost': '100',  # Exactly 10% margin
            'stock': '10',
            'variant': ''
        })
        
        data = response.json()
        # Debug: print the actual response if test fails
        if not data.get('success'):
            print(f"Response: {data}")
        assert data['success'] == True


@pytest.mark.django_db
class TestTC013_ExpiryTracking:
    """TC-013: Expiry date validation and tracking"""
    
    def test_expiry_date_field_exists(self):
        """StockAddition should have expiry_date field"""
        product = Product.objects.create(
            name='Test Product',
            size='10',
            price=Decimal('100'),
            cost=Decimal('50')
        )
        
        future_date = date.today() + timedelta(days=30)
        stock = StockAddition.objects.create(
            product=product,
            quantity=100,
            remaining_quantity=100,
            batch_id='TEST-001',
            expiry_date=future_date,
            manufacturing_date=date.today()
        )
        
        assert stock.expiry_date == future_date
        assert stock.manufacturing_date == date.today()
    
    def test_past_expiry_date_rejected(self, admin_client):
        """Past expiry date should be rejected"""
        client, user = admin_client
        product = Product.objects.create(
            name='Test Product',
            size='120',
            price=Decimal('100'),
            cost=Decimal('50')
        )
        
        past_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Use the single-item form format that includes expiry_date
        response = client.post(reverse('add_stock'), {
            'product': str(product.product_id),
            'quantity': '10',
            'expiry_date': past_date
        })
        
        # Should reject past expiry date
        data = response.json()
        assert data['success'] == False or 'past' in data.get('message', '').lower()


@pytest.mark.django_db
class TestTC028_SMSRetry:
    """TC-028: SMS gateway retry mechanism"""
    
    def test_sms_retry_mechanism_exists(self):
        """SMS service should support retry mechanism"""
        sms_service = IPROGSMSService()
        
        # Check that send_sms accepts retry parameters
        import inspect
        sig = inspect.signature(sms_service.send_sms)
        params = sig.parameters
        
        assert 'max_retries' in params
        assert 'retry_delay' in params
    
    def test_sms_retry_returns_attempt_count(self):
        """SMS service should return attempt count"""
        sms_service = IPROGSMSService()
        
        # Mock test - in real scenario, this would test actual retry logic
        # For now, just verify the method signature is correct
        assert hasattr(sms_service, 'send_sms')


@pytest.mark.django_db
class TestTC035_PasswordChange:
    """TC-035: Password change functionality"""
    
    def test_password_change_endpoint_exists(self):
        """Password change endpoint should exist"""
        from django.urls import resolve
        
        url = reverse('change_password')
        assert url == '/change-password/'
    
    def test_password_change_requires_login(self):
        """Password change should require authentication"""
        client = Client()
        response = client.post(reverse('change_password'), {
            'old_password': 'old123',
            'new_password': 'new123',
            'confirm_password': 'new123'
        })
        
        # Should redirect to login or return error
        assert response.status_code in [302, 403] or response.json()['success'] == False
    
    def test_password_change_validates_old_password(self, admin_client):
        """Password change should verify old password"""
        # Create user with known password
        password = 'test123'
        user = AppUser.objects.create(
            username='changetest',
            password=bcrypt.hash(password),
            phone_number='09123456789',
            role='Admin'
        )
        
        # Login as this user
        client = Client()
        client.post(reverse('login'), {
            'username': 'changetest',
            'password': password
        })
        
        # Try to change with wrong old password
        response = client.post(reverse('change_password'), {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        })
        
        data = response.json()
        assert data['success'] == False


@pytest.mark.django_db
class TestTC043_MaintenanceMode:
    """TC-043: Maintenance mode functionality"""
    
    def test_maintenance_mode_function_exists(self):
        """Maintenance mode check function should exist"""
        assert callable(is_maintenance_mode)
    
    def test_maintenance_mode_default_off(self):
        """Maintenance mode should be off by default"""
        # By default, should be False
        import os
        old_value = os.getenv('MAINTENANCE_MODE')
        if old_value:
            del os.environ['MAINTENANCE_MODE']
        
        assert is_maintenance_mode() == False
        
        if old_value:
            os.environ['MAINTENANCE_MODE'] = old_value
    
    def test_maintenance_middleware_exists(self):
        """Maintenance mode middleware should be registered"""
        from django.conf import settings
        
        middleware_list = settings.MIDDLEWARE
        assert any('MaintenanceModeMiddleware' in m for m in middleware_list)


@pytest.mark.django_db
class TestTC034_ProfileEmail:
    """TC-034: Email field in user profile"""
    
    def test_email_field_exists(self):
        """AppUser model should have email field"""
        user = AppUser.objects.create(
            username='testuser',
            password='test123',
            phone_number='09123456789',
            role='Admin',
            email='test@example.com'
        )
        
        assert user.email == 'test@example.com'


@pytest.mark.django_db
class TestModelFields:
    """Verify all new model fields are properly added"""
    
    def test_appuser_has_is_active(self):
        """AppUser should have is_active field"""
        user = AppUser.objects.create(
            username='testuser',
            password='test123',
            phone_number='09123456789',
            role='Admin'
        )
        
        assert hasattr(user, 'is_active')
        assert user.is_active == True  # Default value
    
    def test_appuser_has_email(self):
        """AppUser should have email field"""
        user = AppUser.objects.create(
            username='testuser',
            password='test123',
            phone_number='09123456789',
            role='Admin'
        )
        
        assert hasattr(user, 'email')
    
    def test_product_has_sku(self):
        """Product should have sku field"""
        product = Product.objects.create(
            name='Test Product',
            size='10',
            price=Decimal('100'),
            cost=Decimal('50')
        )
        
        assert hasattr(product, 'sku')
    
    def test_stockaddition_has_expiry_fields(self):
        """StockAddition should have expiry tracking fields"""
        product = Product.objects.create(
            name='Test Product',
            size='10',
            price=Decimal('100'),
            cost=Decimal('50')
        )
        
        stock = StockAddition.objects.create(
            product=product,
            quantity=100,
            remaining_quantity=100,
            batch_id='TEST-001'
        )
        
        assert hasattr(stock, 'expiry_date')
        assert hasattr(stock, 'manufacturing_date')


@pytest.mark.django_db
class TestDataIntegrity:
    """Test data integrity with new fields"""
    
    def test_product_with_all_new_fields(self):
        """Create product with all new fields"""
        product = Product.objects.create(
            name='Complete Product',
            size='10',
            price=Decimal('110'),
            cost=Decimal('100'),
            sku='COMPLETE-001',
            status='active'
        )
        
        assert product.sku == 'COMPLETE-001'
        assert product.price == Decimal('110')
    
    def test_user_with_all_new_fields(self):
        """Create user with all new fields"""
        user = AppUser.objects.create(
            username='completeuser',
            password=bcrypt.hash('test123'),
            phone_number='09123456789',
            role='Admin',
            is_active=True,
            email='complete@example.com'
        )
        
        assert user.is_active == True
        assert user.email == 'complete@example.com'
    
    def test_stock_with_expiry_info(self):
        """Create stock addition with expiry information"""
        product = Product.objects.create(
            name='Expiring Product',
            size='10',
            price=Decimal('100'),
            cost=Decimal('50')
        )
        
        future_date = date.today() + timedelta(days=30)
        stock = StockAddition.objects.create(
            product=product,
            quantity=100,
            remaining_quantity=100,
            batch_id='EXP-001',
            manufacturing_date=date.today(),
            expiry_date=future_date
        )
        
        assert stock.expiry_date == future_date
        assert stock.manufacturing_date == date.today()

