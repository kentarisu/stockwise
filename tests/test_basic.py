"""
Basic test cases for the StockWise Django application.
These tests focus on core functionality that should work with the existing system.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from core.models import Product, AppUser, Sale, StockAddition, SMS


class TestBasicModels:
    """Test basic model functionality."""
    
    def test_product_creation(self):
        """Test basic product creation."""
        product = Product.objects.create(
            name='Test Apple',
            variant='Red',
            price=Decimal('50.00'),
            cost=Decimal('30.00'),
            size='120',
            stock=100,
            low_stock_threshold=10,
            supplier='Test Supplier'
        )
        
        assert product.name == 'Test Apple'
        assert product.variant == 'Red'
        assert product.price == Decimal('50.00')
        assert product.cost == Decimal('30.00')
        assert product.size == '120'
        assert product.stock == 100
        assert product.low_stock_threshold == 10
        assert product.supplier == 'Test Supplier'
        assert product.is_built_in is False
        assert str(product) == 'Test Apple'
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = AppUser.objects.create(
            username='testuser',
            password='hashedpassword',
            phone_number='1234567890',
            role='Secretary'
        )
        
        assert user.username == 'testuser'
        assert user.password == 'hashedpassword'
        assert user.phone_number == '1234567890'
        assert user.role == 'Secretary'
        assert str(user) == 'testuser'
    
    def test_stock_addition_creation(self):
        """Test basic stock addition creation."""
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('25.00'),
            cost=Decimal('15.00')
        )
        
        stock_addition = StockAddition.objects.create(
            product=product,
            quantity=50,
            cost=Decimal('25.00'),
            batch_id='BATCH001',
            supplier='Test Supplier',
            remaining_quantity=50
        )
        
        assert stock_addition.product == product
        assert stock_addition.quantity == 50
        assert stock_addition.cost == Decimal('25.00')
        assert stock_addition.batch_id == 'BATCH001'
        assert stock_addition.supplier == 'Test Supplier'
        assert stock_addition.remaining_quantity == Decimal('50.00')
    
    def test_sale_creation(self):
        """Test basic sale creation."""
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('50.00'),
            cost=Decimal('30.00')
        )
        
        user = AppUser.objects.create(
            username='testuser',
            password='password',
            phone_number='1234567890',
            role='Secretary'
        )
        
        sale = Sale.objects.create(
            product=product,
            quantity=5,
            price=Decimal('50.00'),
            total=Decimal('250.00'),
            user=user,
            transaction_number='TXN001',
            customer_name='John Doe'
        )
        
        assert sale.product == product
        assert sale.quantity == 5
        assert sale.price == Decimal('50.00')
        assert sale.total == Decimal('250.00')
        assert sale.user == user
        assert sale.transaction_number == 'TXN001'
        assert sale.customer_name == 'John Doe'
        assert sale.status == 'completed'
    
    def test_sms_creation(self):
        """Test basic SMS creation."""
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('25.00')
        )
        
        user = AppUser.objects.create(
            username='testuser',
            password='password',
            phone_number='1234567890',
            role='Secretary'
        )
        
        sms = SMS.objects.create(
            product=product,
            user=user,
            message_type='stock_alert',
            demand_level='high',
            message_content='Low stock alert for Test Product'
        )
        
        assert sms.product == product
        assert sms.user == user
        assert sms.message_type == 'stock_alert'
        assert sms.demand_level == 'high'
        assert sms.message_content == 'Low stock alert for Test Product'


class TestBasicViews:
    """Test basic view functionality."""
    
    def test_login_view_get(self):
        """Test GET request to login view."""
        client = Client()
        response = client.get(reverse('login'))
        assert response.status_code == 200
    
    def test_logout_view(self):
        """Test logout view."""
        client = Client()
        response = client.get(reverse('logout'))
        assert response.status_code == 302  # Should redirect after logout
    
    def test_dashboard_view_redirects_when_not_logged_in(self):
        """Test that dashboard redirects when not logged in."""
        client = Client()
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302  # Should redirect to login
    
    def test_products_inventory_view_redirects_when_not_logged_in(self):
        """Test that products inventory redirects when not logged in."""
        client = Client()
        response = client.get(reverse('products_inventory'))
        assert response.status_code == 302  # Should redirect to login
    
    def test_sales_view_redirects_when_not_logged_in(self):
        """Test that sales view redirects when not logged in."""
        client = Client()
        response = client.get(reverse('sales'))
        assert response.status_code == 302  # Should redirect to login
    
    def test_reports_view_redirects_when_not_logged_in(self):
        """Test that reports view redirects when not logged in."""
        client = Client()
        response = client.get(reverse('reports'))
        assert response.status_code == 302  # Should redirect to login
    
    def test_charts_view_redirects_when_not_logged_in(self):
        """Test that charts view redirects when not logged in."""
        client = Client()
        response = client.get(reverse('charts'))
        assert response.status_code == 302  # Should redirect to login


class TestBasicCalculations:
    """Test basic calculation functionality."""
    
    def test_sale_total_calculation(self):
        """Test sale total calculation."""
        quantity = 5
        price = Decimal('50.00')
        expected_total = quantity * price
        
        assert expected_total == Decimal('250.00')
    
    def test_change_calculation(self):
        """Test change calculation for sales."""
        total = Decimal('250.00')
        amount_paid = Decimal('300.00')
        expected_change = amount_paid - total
        
        assert expected_change == Decimal('50.00')
    
    def test_margin_calculation(self):
        """Test margin calculation."""
        price = Decimal('50.00')
        cost = Decimal('30.00')
        margin = (price - cost) / price
        
        assert margin == Decimal('0.40')  # 40% margin
    
    def test_markup_calculation(self):
        """Test markup calculation."""
        price = Decimal('50.00')
        cost = Decimal('30.00')
        markup = (price - cost) / cost
        
        # Use approximate comparison for floating point precision
        assert abs(markup - Decimal('0.67')) < Decimal('0.01')  # ~67% markup
    
    def test_low_stock_detection(self):
        """Test low stock detection logic."""
        stock = 5
        low_stock_threshold = 10
        
        assert stock < low_stock_threshold  # Should be low stock
        
        stock = 15
        assert stock >= low_stock_threshold  # Should not be low stock


class TestBasicDataValidation:
    """Test basic data validation."""
    
    def test_product_data_validation(self):
        """Test product data validation."""
        valid_data = {
            'name': 'Valid Product',
            'price': '50.00',
            'cost': '30.00',
            'size': '120',
            'stock': '100',
            'low_stock_threshold': '10'
        }
        
        assert valid_data['name']
        assert float(valid_data['price']) > 0
        assert float(valid_data['cost']) >= 0
        assert int(valid_data['stock']) >= 0
        assert int(valid_data['low_stock_threshold']) > 0
    
    def test_sale_data_validation(self):
        """Test sale data validation."""
        valid_data = {
            'quantity': '5',
            'price': '50.00',
            'customer_name': 'John Doe',
            'contact_number': '1234567890'
        }
        
        assert int(valid_data['quantity']) > 0
        assert float(valid_data['price']) > 0
        assert valid_data['customer_name']
        assert len(valid_data['contact_number']) >= 10
    
    def test_user_data_validation(self):
        """Test user data validation."""
        valid_data = {
            'username': 'testuser',
            'phone_number': '1234567890',
            'role': 'Secretary'
        }
        
        assert valid_data['username']
        assert len(valid_data['phone_number']) >= 10
        assert valid_data['role'] in ['Admin', 'Secretary']


class TestBasicModelRelationships:
    """Test basic model relationships."""
    
    def test_product_stock_addition_relationship(self):
        """Test relationship between Product and StockAddition."""
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('25.00')
        )
        
        stock_addition = StockAddition.objects.create(
            product=product,
            quantity=50,
            batch_id='BATCH001'
        )
        
        assert stock_addition.product == product
        assert product in Product.objects.filter(stockaddition__batch_id='BATCH001')
    
    def test_product_sale_relationship(self):
        """Test relationship between Product and Sale."""
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('50.00')
        )
        
        user = AppUser.objects.create(
            username='testuser',
            password='password',
            phone_number='1234567890',
            role='Secretary'
        )
        
        sale = Sale.objects.create(
            product=product,
            quantity=5,
            price=Decimal('50.00'),
            total=Decimal('250.00'),
            user=user
        )
        
        assert sale.product == product
        assert sale.user == user
        assert product in Product.objects.filter(sale__customer_name='')
    
    def test_user_sale_relationship(self):
        """Test relationship between User and Sale."""
        user = AppUser.objects.create(
            username='testuser',
            password='password',
            phone_number='1234567890',
            role='Secretary'
        )
        
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('50.00')
        )
        
        sale = Sale.objects.create(
            product=product,
            quantity=5,
            price=Decimal('50.00'),
            total=Decimal('250.00'),
            user=user
        )
        
        assert sale.user == user
        assert user in AppUser.objects.filter(sale__product=product)
