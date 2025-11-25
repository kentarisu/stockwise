import os
from django.conf import settings
from django.test import SimpleTestCase


class TermReplacementTests(SimpleTestCase):
    def _read(self, rel_path: str) -> str:
        full = os.path.join(settings.BASE_DIR, rel_path)
        with open(full, 'r', encoding='utf-8') as f:
            return f.read()

    def test_inventory_filter_id_renamed(self):
        html = self._read('templates/products_inventory_full.html')
        self.assertIn('id="productFilter"', html)
        self.assertNotIn('id="fruitFilter"', html)

    def test_sales_filter_id_renamed(self):
        html = self._read('templates/sales_full.html')
        self.assertIn('id="productFilter"', html)
        self.assertNotIn('id="fruitFilter"', html)

    def test_reports_filter_id_renamed(self):
        html = self._read('templates/reports_full.html')
        self.assertIn('id="productFilter"', html)
        self.assertNotIn('id="fruitFilter"', html)

    def test_select_product_text_present(self):
        inv = self._read('templates/products_inventory_full.html')
        add_stock = self._read('templates/add_stock.html')
        record_sale = self._read('templates/record_sale.html')
        self.assertIn('Select a product', inv)
        self.assertIn('Select a product', add_stock)
        self.assertIn('Select a product', record_sale)

    def test_no_select_fruit_text(self):
        files = [
            'templates/products_inventory_full.html',
            'templates/sales_full.html',
            'templates/reports_full.html',
            'templates/add_product.html',
            'templates/print_stickers.html',
            'templates/record_sale.html',
            'templates/add_stock.html',
        ]
        for rel in files:
            html = self._read(rel).lower()
            self.assertNotIn('select a fruit', html)

    def test_brand_name_kept(self):
        sales = self._read('templates/sales_full.html')
        views_py = self._read('core/views.py')
        thermal = self._read('core/thermal_printer.py')
        self.assertIn('FruitMaster Marketing', sales)
        self.assertIn('FruitMaster Marketing Sales Report', views_py)
        self.assertIn('FruitMaster Marketing', thermal)

    def test_form_and_inputs_ids_updated(self):
        add_product = self._read('templates/add_product.html')
        self.assertIn('id="addProductForm"', add_product)
        self.assertNotIn('id="addFruitForm"', add_product)

        print_stickers = self._read('templates/print_stickers.html')
        self.assertIn('id="stickerProductSelect"', print_stickers)
        self.assertNotIn('id="stickerFruitSelect"', print_stickers)

    def test_product_param_used_in_frontend(self):
        sales = self._read('templates/sales_full.html')
        self.assertIn('product: fruitFilter', sales)
        self.assertNotIn('fruit: fruitFilter', sales)
        reports = self._read('templates/reports_full.html')
        self.assertIn('product: fruitFilter', reports)
        inventory = self._read('templates/products_inventory_full.html')
        self.assertIn('product: fruitFilter', inventory)

    def test_product_param_accepted_in_backend(self):
        views_py = self._read('core/views.py')
        # Ensure major views accept the product param
        self.assertIn("request.GET.get('product'", views_py)
        self.assertIn("getp('product'", views_py)

    def test_min_price_hint_present(self):
        add_product = self._read('templates/add_product.html')
        self.assertIn('id="minPriceHint"', add_product)
        self.assertIn('Minimum price:', add_product)