"""
Test cases for Django models in the StockWise application.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from core.models import Product, StockAddition, AppUser, Sale, SMS, ReportProductSummary


class TestProduct:
    """Test cases for the Product model."""
    
    def test_product_creation(self):
        """Test basic product creation."""
        product = Product.objects.create(
            name='Test Apple',
            variant='Red',
            status='active',
            price=Decimal('50.00'),
            cost=Decimal('30.00'),
            size='120',
            stock=100,
            low_stock_threshold=10,
            supplier='Test Supplier'
        )
        
        assert product.name == 'Test Apple'
        assert product.variant == 'Red'
        assert product.status == 'active'
        assert product.price == Decimal('50.00')
        assert product.cost == Decimal('30.00')
        assert product.size == '120'
        assert product.stock == 100
        assert product.low_stock_threshold == 10
        assert product.supplier == 'Test Supplier'
        assert product.is_built_in is False
        assert product.__str__() == 'Test Apple'
    
    def test_product_default_values(self):
        """Test product default values."""
        product = Product.objects.create(name='Test Product')
        
        assert product.status == 'active'
        assert product.price == Decimal('0.00')
        assert product.cost == Decimal('0.00')
        assert product.stock == 0
        assert product.low_stock_threshold == 10
        assert product.is_built_in is False
        assert product.qr_code == b''
    
    def test_product_status_choices(self):
        """Test product status choices validation."""
        # Valid choices
        product1 = Product.objects.create(name='Active Product', status='active')
        product2 = Product.objects.create(name='Discontinued Product', status='discontinued')
        
        assert product1.status == 'active'
        assert product2.status == 'discontinued'
    
    def test_product_str_representation(self):
        """Test product string representation."""
        product = Product.objects.create(name='Test Product Name')
        assert str(product) == 'Test Product Name'


class TestAppUser:
    """Test cases for the AppUser model."""
    
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
        assert user.__str__() == 'testuser'
    
    def test_user_default_role(self):
        """Test user default role."""
        user = AppUser.objects.create(
            username='testuser',
            password='hashedpassword',
            phone_number='1234567890'
        )
        
        assert user.role == 'Secretary'
    
    def test_user_role_choices(self):
        """Test user role choices validation."""
        admin_user = AppUser.objects.create(
            username='admin',
            password='password',
            phone_number='1234567890',
            role='Admin'
        )
        
        secretary_user = AppUser.objects.create(
            username='secretary',
            password='password',
            phone_number='0987654321',
            role='Secretary'
        )
        
        assert admin_user.role == 'Admin'
        assert secretary_user.role == 'Secretary'


class TestStockAddition:
    """Test cases for the StockAddition model."""
    
    def test_stock_addition_creation(self, sample_product):
        """Test basic stock addition creation."""
        stock_addition = StockAddition.objects.create(
            product=sample_product,
            quantity=50,
            cost=Decimal('25.00'),
            batch_id='BATCH001',
            supplier='Test Supplier',
            remaining_quantity=50
        )
        
        assert stock_addition.product == sample_product
        assert stock_addition.quantity == 50
        assert stock_addition.cost == Decimal('25.00')
        assert stock_addition.batch_id == 'BATCH001'
        assert stock_addition.supplier == 'Test Supplier'
        assert stock_addition.remaining_quantity == Decimal('50.00')
    
    def test_stock_addition_default_values(self, sample_product):
        """Test stock addition default values."""
        stock_addition = StockAddition.objects.create(
            product=sample_product,
            batch_id='BATCH002'
        )
        
        assert stock_addition.quantity == 0
        assert stock_addition.cost == Decimal('0.00')
        assert stock_addition.remaining_quantity == Decimal('0.00')
        assert stock_addition.date_added is not None


class TestSale:
    """Test cases for the Sale model."""
    
    def test_sale_creation(self, sample_product, sample_user):
        """Test basic sale creation."""
        sale = Sale.objects.create(
            product=sample_product,
            quantity=5,
            price=Decimal('50.00'),
            total=Decimal('250.00'),
            user=sample_user,
            transaction_number='TXN001',
            or_number='OR001',
            customer_name='John Doe',
            address='123 Main St',
            contact_number=1234567890
        )
        
        assert sale.product == sample_product
        assert sale.quantity == 5
        assert sale.price == Decimal('50.00')
        assert sale.total == Decimal('250.00')
        assert sale.user == sample_user
        assert sale.transaction_number == 'TXN001'
        assert sale.or_number == 'OR001'
        assert sale.customer_name == 'John Doe'
        assert sale.address == '123 Main St'
        assert sale.contact_number == 1234567890
        assert sale.status == 'completed'
        assert sale.stock_restored is False
    
    def test_sale_default_values(self, sample_product, sample_user):
        """Test sale default values."""
        sale = Sale.objects.create(
            product=sample_product,
            user=sample_user
        )
        
        assert sale.quantity == 0
        assert sale.price == Decimal('0.00')
        assert sale.total == Decimal('0.00')
        assert sale.status == 'completed'
        assert sale.stock_restored is False
        assert sale.transaction_number == ''
        assert sale.or_number == ''
        assert sale.customer_name == ''
        assert sale.address == ''
        assert sale.contact_number == 0
    
    def test_sale_status_choices(self, sample_product, sample_user):
        """Test sale status choices."""
        completed_sale = Sale.objects.create(
            product=sample_product,
            user=sample_user,
            status='completed'
        )
        
        voided_sale = Sale.objects.create(
            product=sample_product,
            user=sample_user,
            status='voided'
        )
        
        assert completed_sale.status == 'completed'
        assert voided_sale.status == 'voided'


class TestSMS:
    """Test cases for the SMS model."""
    
    def test_sms_creation(self, sample_product, sample_user):
        """Test basic SMS creation."""
        sms = SMS.objects.create(
            product=sample_product,
            user=sample_user,
            message_type='stock_alert',
            demand_level='high',
            message_content='Low stock alert for Test Apple'
        )
        
        assert sms.product == sample_product
        assert sms.user == sample_user
        assert sms.message_type == 'stock_alert'
        assert sms.demand_level == 'high'
        assert sms.message_content == 'Low stock alert for Test Apple'
        assert sms.__str__() == f'SMS {sms.sms_id}'
    
    def test_sms_message_type_choices(self, sample_product, sample_user):
        """Test SMS message type choices."""
        sms_types = [
            'sales_summary_daily',
            'sales_summary_weekly',
            'stock_alert',
            'pricing_alert'
        ]
        
        # Create different users for each SMS to avoid unique constraint
        for i, msg_type in enumerate(sms_types):
            user = AppUser.objects.create(
                username=f'testuser{i}',
                password='password',
                phone_number=f'123456789{i}',
                role='Secretary'
            )
            sms = SMS.objects.create(
                product=sample_product,
                user=user,
                message_type=msg_type,
                demand_level='mid',
                message_content=f'Test message for {msg_type}'
            )
            assert sms.message_type == msg_type
    
    def test_sms_demand_level_choices(self, sample_product, sample_user):
        """Test SMS demand level choices."""
        demand_levels = ['high', 'mid', 'low']
        
        # Create different users for each SMS to avoid unique constraint
        for i, level in enumerate(demand_levels):
            user = AppUser.objects.create(
                username=f'testuser{i}',
                password='password',
                phone_number=f'123456789{i}',
                role='Secretary'
            )
            sms = SMS.objects.create(
                product=sample_product,
                user=user,
                message_type='stock_alert',
                demand_level=level,
                message_content=f'Test message for {level} demand'
            )
            assert sms.demand_level == level


class TestReportProductSummary:
    """Test cases for the ReportProductSummary model."""
    
    def test_report_creation(self, sample_product, sample_user):
        """Test basic report creation."""
        now = timezone.now()
        report = ReportProductSummary.objects.create(
            product=sample_product,
            period_start=now - timedelta(days=30),
            period_end=now,
            granularity='daily',
            generated_by=sample_user,
            opening_qty=Decimal('100.00'),
            added_qty=Decimal('50.00'),
            sold_qty=Decimal('30.00'),
            closing_qty=Decimal('120.00')
        )
        
        assert report.product == sample_product
        assert report.granularity == 'daily'
        assert report.generated_by == sample_user
        assert report.opening_qty == Decimal('100.00')
        assert report.added_qty == Decimal('50.00')
        assert report.sold_qty == Decimal('30.00')
        assert report.closing_qty == Decimal('120.00')
    
    def test_report_default_values(self, sample_product):
        """Test report default values."""
        now = timezone.now()
        report = ReportProductSummary.objects.create(
            product=sample_product,
            period_start=now - timedelta(days=7),
            period_end=now,
            granularity='weekly'
        )
        
        assert report.opening_qty == Decimal('0.00')
        assert report.added_qty == Decimal('0.00')
        assert report.sold_qty == Decimal('0.00')
        assert report.expired_qty == Decimal('0.00')
        assert report.closing_qty == Decimal('0.00')
        assert report.revenue == Decimal('0.00')
        assert report.cogs == Decimal('0.00')
        assert report.gross_profit == Decimal('0.00')
        assert report.low_stock_flag is False
        assert report.sms_low_stock_count == 0
        assert report.sms_expiry_count == 0
