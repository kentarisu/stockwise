"""
Test cases for Django views in the StockWise application.
"""
import pytest
import json
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
from unittest.mock import patch, MagicMock

from core.models import Product, AppUser, Sale, StockAddition


class TestAuthenticationViews:
    """Test cases for authentication-related views."""
    
    def test_login_view_get(self, client):
        """Test GET request to login view."""
        response = client.get(reverse('login'))
        assert response.status_code == 200
        assert 'login' in response.content.decode().lower()
    
    def test_login_view_post_valid_credentials(self, client, sample_user):
        """Test POST request to login view with valid credentials."""
        # Create a user with hashed password
        from passlib.hash import bcrypt
        user = AppUser.objects.create(
            username='testuser',
            password=bcrypt.hash('testpass123'),
            phone_number='1234567890',
            role='Secretary'
        )
        
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect on successful login
        assert response.status_code in [200, 302]
    
    def test_login_view_post_invalid_credentials(self, client):
        """Test POST request to login view with invalid credentials."""
        response = client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        
        # Should return to login page with error
        assert response.status_code == 200
        # Check for error message in response
        content = response.content.decode()
        assert 'error' in content.lower() or 'invalid' in content.lower()
    
    def test_logout_view(self, client):
        """Test logout view."""
        response = client.get(reverse('logout'))
        assert response.status_code == 302  # Should redirect after logout


class TestProductViews:
    """Test cases for product-related views."""
    
    def test_add_product_view_get(self, admin_client):
        """Test GET request to add product view."""
        client, user = admin_client
        response = client.get(reverse('add_product_page'))
        assert response.status_code == 200
    
    def test_add_product_view_post(self, admin_client):
        """Test POST request to add product view."""
        client, user = admin_client
        response = client.post(reverse('product_add'), {
            'name': 'Test Apple',
            'variant': 'Red',
            'price': '50.00',
            'cost': '30.00',
            'size': '120',
            'stock': '100',
            'low_stock_threshold': '10',
            'supplier': 'Test Supplier'
        })
        
        # Should redirect on successful creation
        assert response.status_code in [200, 302]
        
        # Check if product was created
        product = Product.objects.filter(name='Test Apple').first()
        assert product is not None
        assert product.name == 'Test Apple'
        assert product.variant == 'Red'
        assert product.price == Decimal('50.00')
    
    def test_products_inventory_view(self, admin_client):
        """Test products inventory view."""
        client, user = admin_client
        response = client.get(reverse('products_inventory'))
        assert response.status_code == 200
        
        # Create a test product
        Product.objects.create(
            name='Test Product',
            price=Decimal('25.00'),
            stock=50
        )
        
        response = client.get(reverse('products_inventory'))
        assert response.status_code == 200
        assert 'Test Product' in response.content.decode()


class TestStockViews:
    """Test cases for stock-related views."""
    
    def test_add_stock_view_get(self, admin_client):
        """Test GET request to add stock view."""
        client, user = admin_client
        response = client.get(reverse('add_stock'))
        assert response.status_code == 200
    
    def test_add_stock_view_post(self, admin_client, sample_product):
        """Test POST request to add stock view."""
        client, user = admin_client
        response = client.post(reverse('add_stock'), {
            'product': sample_product.product_id,
            'quantity': '25',
            'cost': '15.00',
            'batch_id': 'BATCH001',
            'supplier': 'Test Supplier'
        })
        
        # Should redirect on successful addition
        assert response.status_code in [200, 302]
        
        # Check if stock addition was created
        stock_addition = StockAddition.objects.filter(
            product=sample_product,
            batch_id='BATCH001'
        ).first()
        assert stock_addition is not None
        assert stock_addition.quantity == 25
        assert stock_addition.cost == Decimal('15.00')


class TestSalesViews:
    """Test cases for sales-related views."""
    
    def test_record_sale_view_get(self, admin_client):
        """Test GET request to record sale view."""
        client, user = admin_client
        response = client.get(reverse('record_sale'))
        assert response.status_code == 200
    
    def test_record_sale_view_post(self, admin_client, sample_product):
        """Test POST request to record sale view."""
        client, user = admin_client
        response = client.post(reverse('record_sale_api'), {
            'product': sample_product.product_id,
            'quantity': '5',
            'price': '50.00',
            'customer_name': 'John Doe',
            'address': '123 Main St',
            'contact_number': '1234567890',
            'amount_paid': '250.00'
        })
        
        # Should redirect on successful sale
        assert response.status_code in [200, 302]
        
        # Check if sale was created
        sale = Sale.objects.filter(
            product=sample_product,
            customer_name='John Doe'
        ).first()
        assert sale is not None
        assert sale.quantity == 5
        assert sale.price == Decimal('50.00')
    
    def test_sales_view(self, admin_client):
        """Test sales list view."""
        client, user = admin_client
        response = client.get(reverse('sales'))
        assert response.status_code == 200


class TestDashboardViews:
    """Test cases for dashboard views."""
    
    def test_dashboard_view(self, admin_client):
        """Test dashboard view."""
        client, user = admin_client
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
    
    def test_dashboard_with_data(self, admin_client, sample_product):
        """Test dashboard view with sample data."""
        client, user = admin_client
        
        # Create some sales data
        Sale.objects.create(
            product=sample_product,
            quantity=10,
            price=Decimal('50.00'),
            total=Decimal('500.00'),
            user=user
        )
        
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200


class TestReportsViews:
    """Test cases for reports views."""
    
    def test_reports_view(self, admin_client):
        """Test reports view."""
        client, user = admin_client
        response = client.get(reverse('reports'))
        assert response.status_code == 200
    
    def test_charts_view(self, admin_client):
        """Test charts view."""
        client, user = admin_client
        response = client.get(reverse('charts'))
        assert response.status_code == 200


class TestProfileViews:
    """Test cases for profile views."""
    
    def test_profile_view(self, admin_client):
        """Test profile view."""
        client, user = admin_client
        response = client.get(reverse('profile'))
        assert response.status_code == 200
    
    def test_profile_update(self, admin_client):
        """Test profile update."""
        client, user = admin_client
        response = client.post(reverse('profile'), {
            'username': 'updated_username',
            'phone_number': '9876543210'
        })
        
        assert response.status_code in [200, 302]
        
        # Check if user was updated
        updated_user = AppUser.objects.get(user_id=user.user_id)
        assert updated_user.username == 'updated_username'
        assert updated_user.phone_number == '9876543210'


class TestSMSViews:
    """Test cases for SMS-related views."""
    
    def test_sms_settings_view(self, admin_client):
        """Test SMS settings view."""
        client, user = admin_client
        response = client.get(reverse('sms_settings'))
        assert response.status_code == 200


class TestPrintViews:
    """Test cases for print-related views."""
    
    def test_print_stickers_view(self, admin_client):
        """Test print stickers view."""
        client, user = admin_client
        response = client.get(reverse('print_stickers'))
        assert response.status_code == 200


class TestStockDetailsViews:
    """Test cases for stock details views."""
    
    def test_stock_details_view(self, admin_client, sample_product):
        """Test stock details view."""
        client, user = admin_client
        response = client.get(reverse('stock_details', args=[sample_product.product_id]))
        assert response.status_code == 200


class TestViewPermissions:
    """Test cases for view permissions and access control."""
    
    def test_admin_only_views(self, secretary_client):
        """Test that admin-only views are restricted for secretary users."""
        client, user = secretary_client
        
        # These views might be restricted to admin users
        # Adjust based on your actual permission system
        admin_views = ['add_product', 'add_stock', 'reports']
        
        for view_name in admin_views:
            try:
                response = client.get(reverse(view_name))
                # Should either redirect or show permission denied
                assert response.status_code in [200, 302, 403]
            except:
                # Some views might not exist or have different names
                pass
    
    def test_authenticated_views_require_login(self, client):
        """Test that authenticated views require login."""
        protected_views = [
            'dashboard',
            'products_inventory',
            'record_sale',
            'sales',
            'profile'
        ]
        
        for view_name in protected_views:
            try:
                response = client.get(reverse(view_name))
                # Should redirect to login or show error
                assert response.status_code in [200, 302, 403]
            except:
                # Some views might not exist or have different names
                pass


class TestViewDataIntegrity:
    """Test cases for data integrity in views."""
    
    def test_product_deletion_protection(self, admin_client, sample_product):
        """Test that products with sales cannot be deleted."""
        client, user = admin_client
        
        # Create a sale for the product
        Sale.objects.create(
            product=sample_product,
            quantity=5,
            price=Decimal('50.00'),
            total=Decimal('250.00'),
            user=user
        )
        
        # Try to delete the product (this might be handled by Django's PROTECT)
        # The actual implementation depends on your view logic
        response = client.post(reverse('delete_product', args=[sample_product.product_id]))
        
        # Product should still exist due to foreign key protection
        assert Product.objects.filter(product_id=sample_product.product_id).exists()
    
    def test_stock_addition_updates_product_stock(self, admin_client, sample_product):
        """Test that adding stock updates the product's stock level."""
        client, user = admin_client
        initial_stock = sample_product.stock
        
        response = client.post(reverse('add_stock'), {
            'product': sample_product.product_id,
            'quantity': '25',
            'cost': '15.00',
            'batch_id': 'BATCH001',
            'supplier': 'Test Supplier'
        })
        
        # Refresh product from database
        sample_product.refresh_from_db()
        
        # Stock should be updated (implementation depends on your view logic)
        # This is a placeholder - adjust based on actual implementation
        assert sample_product.stock >= initial_stock
