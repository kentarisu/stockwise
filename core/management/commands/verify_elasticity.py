"""
Django management command to verify elasticity calculation for a specific product.
This script replicates the exact calculation from pricing_ai.py and shows step-by-step results.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import Product, Sale
from core.pricing_ai import DemandPricingAI, PolicyConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz


class Command(BaseCommand):
    help = 'Verify elasticity calculation for a specific product'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-name',
            type=str,
            default='Apple',
            help='Product name (e.g., "Apple")'
        )
        parser.add_argument(
            '--variant',
            type=str,
            default='Fuji',
            help='Product variant (e.g., "Fuji")'
        )
        parser.add_argument(
            '--quantity-unit',
            type=str,
            default='50',
            help='Quantity unit (e.g., "50")'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days of historical data to use'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed step-by-step calculations'
        )

    def handle(self, *args, **options):
        product_name = options['product_name']
        variant = options['variant']
        quantity_unit = options['quantity_unit']
        days = options['days']
        verbose = options['verbose']

        self.stdout.write(self.style.SUCCESS(f'\n=== Elasticity Verification ==='))
        self.stdout.write(f'Product: {product_name} ({variant}) ({quantity_unit})')
        self.stdout.write(f'Historical Period: {days} days\n')

        # Find the product
        try:
            product = Product.objects.get(
                name=product_name,
                variant=variant,
                quantity_unit=quantity_unit,
                status='active'
            )
            self.stdout.write(self.style.SUCCESS(f'[OK] Found product: ID={product.product_id}'))
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'[ERROR] Product not found'))
            return
        except Product.MultipleObjectsReturned:
            products = Product.objects.filter(
                name=product_name,
                variant=variant,
                quantity_unit=quantity_unit,
                status='active'
            )
            product = products.first()
            self.stdout.write(self.style.WARNING(f'[WARNING] Multiple products found, using first: ID={product.product_id}'))

        # Get sales data
        manila_tz = pytz.timezone('Asia/Manila')
        end_date = datetime.now(manila_tz)
        start_date = end_date - timedelta(days=days)

        sales = Sale.objects.filter(
            product=product,
            recorded_at__gte=start_date,
            recorded_at__lte=end_date,
            status='completed'
        ).order_by('recorded_at')

        self.stdout.write(f'\nSales Records: {sales.count()} transactions')
        
        if sales.count() == 0:
            self.stdout.write(self.style.ERROR('[ERROR] No sales data found'))
            return

        # Prepare data exactly as pricing_ai.py does
        sales_data = sales.values('recorded_at', 'quantity', 'price')
        sales_df = pd.DataFrame(list(sales_data))
        
        if sales_df.empty:
            self.stdout.write(self.style.ERROR('[ERROR] Empty sales dataframe'))
            return

        sales_df.columns = ['date', 'units_sold', 'price']
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        sales_df['product_id'] = product.product_id
        sales_df['units_sold'] = sales_df['units_sold'].astype(float)
        sales_df['price'] = sales_df['price'].astype(float)

        self.stdout.write(f'\n=== Data Preparation (matching pricing_ai.py) ===')
        self.stdout.write(f'Initial records: {len(sales_df)}')
        
        if verbose:
            self.stdout.write(f'\nFirst 5 records:')
            self.stdout.write(str(sales_df.head()))

        # Step 1: Aggregate by date and product (exact match to pricing_ai.py line 86-89)
        sales_df['date_only'] = sales_df['date'].dt.date
        sales_aggregated = sales_df.groupby(['product_id', 'date_only']).agg({
            'units_sold': 'sum',
            'price': 'mean'
        }).reset_index()
        sales_aggregated['date'] = pd.to_datetime(sales_aggregated['date_only'])
        sales_aggregated = sales_aggregated.drop('date_only', axis=1)

        self.stdout.write(f'\nAfter daily aggregation: {len(sales_aggregated)} days')
        
        if verbose:
            self.stdout.write(f'\nFirst 5 aggregated days:')
            self.stdout.write(str(sales_aggregated.head()))

        # Step 2: Apply log transformations (exact match to pricing_ai.py line 92-93)
        sales_aggregated['ln_p'] = np.log(sales_aggregated['price'].clip(lower=1e-6))
        sales_aggregated['ln_q'] = np.log((sales_aggregated['units_sold'] + 1e-6))

        # Step 3: Add weekday (exact match to pricing_ai.py line 95)
        sales_aggregated['wday'] = sales_aggregated['date'].dt.weekday  # 0=Mon

        self.stdout.write(f'\n=== Log Transformations ===')
        if verbose:
            self.stdout.write(f'\nSample log values:')
            sample = sales_aggregated[['date', 'price', 'units_sold', 'ln_p', 'ln_q', 'wday']].head(10)
            self.stdout.write(str(sample))
        
        self.stdout.write(f'Price range: {sales_aggregated["price"].min():.2f} - {sales_aggregated["price"].max():.2f}')
        self.stdout.write(f'Quantity range: {sales_aggregated["units_sold"].min():.2f} - {sales_aggregated["units_sold"].max():.2f}')
        self.stdout.write(f'ln(Price) range: {sales_aggregated["ln_p"].min():.4f} - {sales_aggregated["ln_p"].max():.4f}')
        self.stdout.write(f'ln(Quantity) range: {sales_aggregated["ln_q"].min():.4f} - {sales_aggregated["ln_q"].max():.4f}')

        # Step 4: Build design matrix (exact match to pricing_ai.py line 107-112)
        g = sales_aggregated.sort_values('date')
        
        if len(g) < 15:  # min_obs_per_product default
            self.stdout.write(self.style.WARNING(f'\n[WARNING] Only {len(g)} observations (minimum 15 recommended)'))
        else:
            self.stdout.write(f'\n[OK] Sufficient observations: {len(g)}')

        # Build X matrix
        X_base = np.c_[np.ones(len(g)), g['ln_p'].values]
        
        # Weekday dummies
        wday_dummies = pd.get_dummies(g['wday'], prefix='d', drop_first=True)
        X = np.c_[X_base, wday_dummies.values]
        y = g['ln_q'].values.reshape(-1, 1)

        self.stdout.write(f'\n=== Design Matrix ===')
        self.stdout.write(f'X shape: {X.shape} (rows={X.shape[0]}, cols={X.shape[1]})')
        self.stdout.write(f'y shape: {y.shape}')
        self.stdout.write(f'Columns: [intercept, ln_price, weekday_dummies...]')
        
        if verbose:
            self.stdout.write(f'\nFirst 5 rows of X:')
            self.stdout.write(str(X[:5]))
            self.stdout.write(f'\nFirst 5 values of y:')
            self.stdout.write(str(y[:5]))

        # Step 5: Solve OLS (exact match to pricing_ai.py line 115-119)
        lam = 1e-6
        XtX = X.T @ X + lam * np.eye(X.shape[1])
        Xty = X.T @ y
        beta = np.linalg.solve(XtX, Xty)

        self.stdout.write(f'\n=== OLS Regression Results ===')
        self.stdout.write(f'Regularization lambda: {lam}')
        self.stdout.write(f'Beta coefficients shape: {beta.shape}')
        
        # Extract elasticity (exact match to pricing_ai.py line 122)
        elasticity = float(beta[1, 0])
        
        self.stdout.write(f'\nBeta coefficients:')
        self.stdout.write(f'  beta_0 (intercept): {beta[0, 0]:.6f}')
        self.stdout.write(f'  beta_1 (elasticity): {beta[1, 0]:.6f}')
        if len(beta) > 2:
            for i in range(2, len(beta)):
                self.stdout.write(f'  beta_{i} (weekday {i-1}): {beta[i, 0]:.6f}')

        # Step 6: Calculate R² (exact match to pricing_ai.py line 124-128)
        y_hat = X @ beta
        ss_res = float(((y - y_hat) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        self.stdout.write(f'\n=== Model Quality ===')
        self.stdout.write(f'Sum of Squared Residuals (SS_res): {ss_res:.6f}')
        self.stdout.write(f'Total Sum of Squares (SS_tot): {ss_tot:.6f}')
        self.stdout.write(f'R^2 = 1 - (SS_res / SS_tot) = {r2:.6f}')

        # Final result
        self.stdout.write(f'\n=== FINAL RESULT ===')
        self.stdout.write(self.style.SUCCESS(f'Elasticity: {elasticity:.6f}'))
        self.stdout.write(f'R^2: {r2:.6f}')
        self.stdout.write(f'Observations: {len(g)}')
        
        # Compare to expected
        expected_elasticity = 1.010
        diff = abs(elasticity - expected_elasticity)
        tolerance = 0.001
        
        self.stdout.write(f'\n=== VERIFICATION ===')
        self.stdout.write(f'Expected elasticity: {expected_elasticity:.6f}')
        self.stdout.write(f'Calculated elasticity: {elasticity:.6f}')
        self.stdout.write(f'Difference: {diff:.6f}')
        
        if diff < tolerance:
            self.stdout.write(self.style.SUCCESS(f'[MATCH] Within tolerance {tolerance}'))
        else:
            self.stdout.write(self.style.WARNING(f'[MISMATCH] Difference > {tolerance}'))
        
        # Additional diagnostics
        self.stdout.write(f'\n=== DIAGNOSTICS ===')
        if elasticity > 0:
            self.stdout.write(self.style.WARNING('[WARNING] Positive elasticity (unusual for normal goods)'))
        if r2 < 0.3:
            self.stdout.write(self.style.WARNING(f'[WARNING] Low R^2 ({r2:.3f}) - model fit is poor'))
        if len(g) < 15:
            self.stdout.write(self.style.WARNING(f'[WARNING] Few observations ({len(g)})'))
        
        # Correlation check
        correlation = np.corrcoef(g['ln_p'], g['ln_q'])[0, 1]
        self.stdout.write(f'Correlation between ln(price) and ln(quantity): {correlation:.6f}')
        
        # Verify using the actual DemandPricingAI class
        self.stdout.write(f'\n=== Verification using DemandPricingAI class ===')
        cfg = PolicyConfig(
            min_obs_per_product=15,
            default_elasticity=-1.0
        )
        ai = DemandPricingAI(cfg)
        
        # Prepare data in the exact format expected by fit()
        ai_sales_df = pd.DataFrame({
            'date': sales_df['date'],
            'product_id': sales_df['product_id'],
            'units_sold': sales_df['units_sold'],
            'price': sales_df['price']
        })
        
        ai.fit(ai_sales_df)
        ai_model = ai.models.get(product.product_id, {})
        ai_elasticity = float(ai_model.get('elasticity', cfg.default_elasticity))
        ai_r2 = float(ai_model.get('r2', 0.0))
        ai_n = int(ai_model.get('n', 0))
        
        self.stdout.write(f'DemandPricingAI result:')
        self.stdout.write(f'  Elasticity: {ai_elasticity:.6f}')
        self.stdout.write(f'  R^2: {ai_r2:.6f}')
        self.stdout.write(f'  n: {ai_n}')
        
        if abs(elasticity - ai_elasticity) < 0.0001:
            self.stdout.write(self.style.SUCCESS('[OK] Manual calculation matches DemandPricingAI class'))
        else:
            self.stdout.write(self.style.ERROR('[ERROR] Manual calculation does NOT match DemandPricingAI class'))
            self.stdout.write(f'  Difference: {abs(elasticity - ai_elasticity):.6f}')
