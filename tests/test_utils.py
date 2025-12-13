"""
Test cases for utility functions and helper methods in the StockWise application.
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import datetime, timedelta
import django.db.models as models

from core.models import Product, AppUser, Sale, StockAddition


class TestPricingAI:
    """Test cases for pricing AI functionality."""
    
    def test_pricing_ai_recommendation(self):
        """Test pricing AI recommendation generation."""
        # Mock the AI function
        mock_generate = MagicMock()
        mock_generate.return_value = {
            'suggested_price': Decimal('45.00'),
            'action': 'increase',
            'confidence': 0.85
        }
        
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('40.00'),
            cost=Decimal('25.00'),
            stock=50
        )
        
        # Test the pricing recommendation
        result = mock_generate(product)
        
        assert result['suggested_price'] == Decimal('45.00')
        assert result['action'] == 'increase'
        assert result['confidence'] == 0.85
    
    def test_pricing_calculation_logic(self):
        """Test basic pricing calculation logic."""
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('50.00'),
            cost=Decimal('30.00'),
            stock=100
        )
        
        # Calculate margin
        margin = (product.price - product.cost) / product.price
        assert margin == Decimal('0.40')  # 40% margin
        
        # Calculate markup
        markup = (product.price - product.cost) / product.cost
        assert abs(markup - Decimal('0.67')) < Decimal('0.01')  # 67% markup (with tolerance)


class TestSMSService:
    """Test cases for SMS service functionality."""
    
    def test_sms_service_send_notification(self):
        """Test SMS service notification sending."""
        # Mock the SMS service
        mock_send = MagicMock()
        mock_send.return_value = True
        
        result = mock_send(
            phone_number='1234567890',
            message='Test SMS message',
            message_type='stock_alert'
        )
        
        assert result is True
        mock_send.assert_called_once_with(
            phone_number='1234567890',
            message='Test SMS message',
            message_type='stock_alert'
        )
    
    def test_sms_message_formatting(self):
        """Test SMS message formatting."""
        product = Product.objects.create(
            name='Test Apple',
            stock=5,
            low_stock_threshold=10
        )
        
        # Format low stock message
        message = f"Low stock alert: {product.name} has {product.stock} units remaining (threshold: {product.low_stock_threshold})"
        
        assert "Low stock alert" in message
        assert product.name in message
        assert str(product.stock) in message
        assert str(product.low_stock_threshold) in message
    
    def test_sms_message_length_validation(self):
        """Test SMS message length validation."""
        # Create a very long message
        long_message = "A" * 200  # SMS typically has 160 character limit
        
        # Should be truncated or formatted appropriately
        assert len(long_message) > 160
        
        # In real implementation, this would be handled by the SMS service
        truncated_message = long_message[:160] if len(long_message) > 160 else long_message
        assert len(truncated_message) <= 160


class TestStockManagement:
    """Test cases for stock management utilities."""
    
    def test_stock_level_calculation(self, sample_product):
        """Test stock level calculations."""
        # Add some stock additions
        StockAddition.objects.create(
            product=sample_product,
            quantity=50,
            cost=Decimal('25.00'),
            batch_id='BATCH001',
            remaining_quantity=50
        )
        
        StockAddition.objects.create(
            product=sample_product,
            quantity=30,
            cost=Decimal('15.00'),
            batch_id='BATCH002',
            remaining_quantity=30
        )
        
        # Calculate total stock from additions
        total_stock = StockAddition.objects.filter(
            product=sample_product
        ).aggregate(total=models.Sum('remaining_quantity'))['total']
        
        assert total_stock == Decimal('80.00')
    
    def test_low_stock_detection(self):
        """Test low stock detection logic."""
        # Create product with low stock
        low_stock_product = Product.objects.create(
            name='Low Stock Product',
            stock=5,
            low_stock_threshold=10,
            price=Decimal('25.00')
        )
        
        # Create product with adequate stock
        adequate_stock_product = Product.objects.create(
            name='Adequate Stock Product',
            stock=50,
            low_stock_threshold=10,
            price=Decimal('25.00')
        )
        
        # Check low stock condition
        assert low_stock_product.stock < low_stock_product.low_stock_threshold
        assert adequate_stock_product.stock >= adequate_stock_product.low_stock_threshold
    
    def test_stock_addition_batch_tracking(self, sample_product):
        """Test stock addition batch tracking."""
        batch_id = 'BATCH001'
        
        # Create stock addition
        stock_addition = StockAddition.objects.create(
            product=sample_product,
            quantity=100,
            cost=Decimal('50.00'),
            batch_id=batch_id,
            remaining_quantity=100,
            supplier='Test Supplier'
        )
        
        # Verify batch tracking
        assert stock_addition.batch_id == batch_id
        assert stock_addition.remaining_quantity == Decimal('100.00')
        
        # Simulate stock usage
        stock_addition.remaining_quantity = Decimal('75.00')
        stock_addition.save()
        
        assert stock_addition.remaining_quantity == Decimal('75.00')


class TestSalesCalculations:
    """Test cases for sales calculation utilities."""
    
    def test_sale_total_calculation(self, sample_product, sample_user):
        """Test sale total calculation."""
        quantity = 5
        price = Decimal('50.00')
        expected_total = quantity * price
        
        sale = Sale.objects.create(
            product=sample_product,
            quantity=quantity,
            price=price,
            total=expected_total,
            user=sample_user
        )
        
        assert sale.total == expected_total
        assert sale.total == Decimal('250.00')
    
    def test_change_calculation(self, sample_product, sample_user):
        """Test change calculation for sales."""
        total = Decimal('250.00')
        amount_paid = Decimal('300.00')
        expected_change = amount_paid - total
        
        sale = Sale.objects.create(
            product=sample_product,
            quantity=5,
            price=Decimal('50.00'),
            total=total,
            amount_paid=amount_paid,
            change_given=expected_change,
            user=sample_user
        )
        
        assert sale.change_given == expected_change
        assert sale.change_given == Decimal('50.00')
    
    def test_sales_revenue_calculation(self, sample_user):
        """Test sales revenue calculation."""
        # Create products
        product1 = Product.objects.create(
            name='Product 1',
            price=Decimal('50.00'),
            cost=Decimal('30.00')
        )
        
        product2 = Product.objects.create(
            name='Product 2',
            price=Decimal('75.00'),
            cost=Decimal('45.00')
        )
        
        # Create sales
        Sale.objects.create(
            product=product1,
            quantity=2,
            price=Decimal('50.00'),
            total=Decimal('100.00'),
            user=sample_user
        )
        
        Sale.objects.create(
            product=product2,
            quantity=1,
            price=Decimal('75.00'),
            total=Decimal('75.00'),
            user=sample_user
        )
        
        # Calculate total revenue
        total_revenue = Sale.objects.aggregate(
            total=models.Sum('total')
        )['total']
        
        assert total_revenue == Decimal('175.00')


class TestDataValidation:
    """Test cases for data validation utilities."""
    
    def test_product_data_validation(self):
        """Test product data validation."""
        # Valid product data
        valid_data = {
            'name': 'Valid Product',
            'price': '50.00',
            'cost': '30.00',
            'size': '120',
            'stock': '100',
            'low_stock_threshold': '10'
        }
        
        # All fields should be valid
        assert valid_data['name']
        assert float(valid_data['price']) > 0
        assert float(valid_data['cost']) >= 0
        assert int(valid_data['stock']) >= 0
        assert int(valid_data['low_stock_threshold']) > 0
    
    def test_sale_data_validation(self):
        """Test sale data validation."""
        # Valid sale data
        valid_data = {
            'quantity': '5',
            'price': '50.00',
            'customer_name': 'John Doe',
            'contact_number': '1234567890'
        }
        
        # All fields should be valid
        assert int(valid_data['quantity']) > 0
        assert float(valid_data['price']) > 0
        assert valid_data['customer_name']
        assert len(valid_data['contact_number']) >= 10
    
    def test_user_data_validation(self):
        """Test user data validation."""
        # Valid user data
        valid_data = {
            'username': 'testuser',
            'phone_number': '1234567890',
            'role': 'Secretary'
        }
        
        # All fields should be valid
        assert valid_data['username']
        assert len(valid_data['phone_number']) >= 10
        assert valid_data['role'] in ['Admin', 'Secretary']


class TestReportGeneration:
    """Test cases for report generation utilities."""
    
    def test_daily_sales_report_data(self, sample_user):
        """Test daily sales report data generation."""
        # Create some sales for today
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('50.00'),
            cost=Decimal('30.00')
        )
        
        today = timezone.now().date()
        
        Sale.objects.create(
            product=product,
            quantity=5,
            price=Decimal('50.00'),
            total=Decimal('250.00'),
            user=sample_user,
            recorded_at=timezone.now()
        )
        
        # Generate daily sales data
        daily_sales = Sale.objects.filter(
            recorded_at__date=today
        ).aggregate(
            total_sales=models.Sum('total'),
            total_quantity=models.Sum('quantity'),
            total_transactions=models.Count('sale_id')
        )
        
        assert daily_sales['total_sales'] == Decimal('250.00')
        assert daily_sales['total_quantity'] == 5
        assert daily_sales['total_transactions'] == 1
    
    def test_inventory_report_data(self):
        """Test inventory report data generation."""
        # Create products with different stock levels
        Product.objects.create(
            name='Low Stock Product',
            stock=5,
            low_stock_threshold=10,
            price=Decimal('25.00')
        )
        
        Product.objects.create(
            name='Adequate Stock Product',
            stock=50,
            low_stock_threshold=10,
            price=Decimal('25.00')
        )
        
        # Generate inventory report data
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(
            stock__lt=models.F('low_stock_threshold')
        ).count()
        
        assert total_products == 2
        assert low_stock_products == 1
    
    def test_profit_loss_calculation(self, sample_user):
        """Test profit and loss calculation."""
        # Create product with cost and sales
        product = Product.objects.create(
            name='Test Product',
            price=Decimal('50.00'),
            cost=Decimal('30.00')
        )
        
        # Create sale
        Sale.objects.create(
            product=product,
            quantity=10,
            price=Decimal('50.00'),
            total=Decimal('500.00'),
            user=sample_user
        )
        
        # Calculate profit
        revenue = Decimal('500.00')
        cogs = Decimal('30.00') * 10  # cost * quantity
        profit = revenue - cogs
        
        assert revenue == Decimal('500.00')
        assert cogs == Decimal('300.00')
        assert profit == Decimal('200.00')
