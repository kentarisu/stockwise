from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .password_change_view import change_password

urlpatterns = [
	path('', views.redirect_to_login, name='root'),
	path('login/', views.login_view, name='login'),
	path('login/verify/', views.two_factor_verify, name='two_factor_verify'),
	path('accounts/google/login/', views.google_login_start, name='google_login_start'),
	path('accounts/google/login/callback/', views.google_login_callback, name='google_login_callback'),
	path('logout/', views.logout_view, name='logout'),
	path('dashboard/', views.dashboard_view, name='dashboard'),
	path('products_inventory/', views.products_inventory, name='products_inventory'),
	path('stock_details/', views.stock_details_view, name='stock_details'),
path('products/add/', views.add_product_page, name='add_product_page'),
path('sales/record/', views.record_sale_page, name='record_sale'),
path('sales/record/main/', views.record_sale_main, name='record_sale_main'),
path('stock/add/', views.add_stock_page, name='add_stock_page'),
path('stickers/print/', views.print_stickers_page, name='print_stickers'),
	path('products_inventory/post/', views.handle_product_post, name='handle_product_post'),
    path('profile/', views.profile_view, name='profile'),
    path('api/profile/email/start-change/', views.start_email_change, name='start_email_change'),
    path('api/profile/email/verify/', views.verify_email_change, name='verify_email_change'),
    path('api/admin/secretary/email/start-change/', views.admin_start_secretary_email_change, name='admin_start_secretary_email_change'),
    path('api/admin/secretary/email/verify/', views.admin_verify_secretary_email_change, name='admin_verify_secretary_email_change'),
	path('logs/', views.action_logs_view, name='action_logs'),
	path('api/user/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
	path('api/user/update-secretary/', views.update_secretary_account, name='update_secretary_account'),
	path('change-password/', change_password, name='change_password'),  # TC-035

	# Password assistance
	path('password/forgot/', views.forgot_password, name='forgot_password'),
	path('password/reset/', views.password_reset_verify, name='password_reset_verify'),
	
	# Product API endpoints
	path('api/products/add/', views.product_add, name='product_add'),
	path('api/products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
path('api/products/<int:product_id>/delete/', views.product_delete, name='delete_product'),
	path('api/products/<int:product_id>/stock/add/', views.stock_add, name='stock_add'),
	path('api/products/list/', views.fetch_products, name='fetch_products'),
	path('api/products/<int:product_id>/details/', views.get_product_details, name='get_product_details'),
	path('api/products/active/', views.get_active_products, name='get_active_products'),
	path('api/products/get_id/', views.get_product_id, name='get_product_id'),
	# Stock details API for modal (FIFO batches)
	path('api/products/<int:product_id>/stock/', views.stock_details, name='stock_details_api'),
	path('api/products/<int:product_id>/stock/decrease/', views.stock_decrease, name='stock_decrease'),
	# Alternate simple stock details endpoint (used by modal for stability)
	path('api/products/<int:product_id>/stock_details/', views.fetch_stock_details, name='fetch_stock_details'),
	path('api/products/<int:product_id>/fifo-pricing/', views.calculate_fifo_pricing_api, name='calculate_fifo_pricing'),
	path('api/products/built-in/', views.fetch_built_in_products, name='fetch_built_in_products'),
	
	# Sales URLs
	path('sales/', views.sales_view, name='sales'),
	path('api/sales/fetch/', views.fetch_sales, name='fetch_sales'),
	path('api/sales/<int:sale_id>/void/', views.void_sale, name='void_sale'),
	path('api/sales/<int:sale_id>/complete/', views.complete_sale, name='complete_sale'),
	path('api/sales/<int:sale_id>/details/', views.get_sale_details, name='get_sale_details'),
	path('api/sales/<int:sale_id>/check_print_limit/', views.check_print_limit, name='check_print_limit'),
	path('api/sales/<int:sale_id>/record_print/', views.record_print, name='record_print'),
    path('api/printer/receipt/<int:sale_id>/', views.print_thermal_receipt, name='print_thermal_receipt'),
    path('api/printer/test/', views.test_thermal_printer, name='test_thermal_printer'),
    path('api/printer/ports/', views.get_printer_ports, name='get_printer_ports'),
	path('reports/', views.reports_view, name='reports'),
	path('charts/', views.charts_view, name='charts'),
	path('api/reports/fetch/', views.fetch_reports, name='fetch_reports'),
	path('api/reports/export/', views.export_report, name='export_report'),
	path('reports/print/', views.export_report, name='reports_print'),
	    path('api/fruit_master/search/', views.fruit_master_search, name='fruit_master_search'),
    path('api/fruit_master/sizes/', views.fruit_master_sizes, name='fruit_master_sizes'),
    path('api/fruit_master/variants/', views.fruit_master_variants, name='fruit_master_variants'),
path('api/sales/record/', views.record_sale, name='record_sale_api'),
path('api/stock/add/', views.add_stock, name='add_stock_api'),
    # Removed duplicate routes: canonical paths are defined above
    path('api/stock/qr/create/', views.stock_qr_create, name='stock_qr_create'),
    path('api/stock/qr/apply/', views.stock_qr_apply, name='stock_qr_apply'),
    path('api/stock/qr/decode/', views.stock_qr_decode, name='stock_qr_decode'),
    path('qr/next-batch-sequence/<int:product_id>/', views.qr_next_batch_sequence, name='qr_next_batch_sequence'),
    path('qr/stock-details/<int:product_id>/', views.stock_details, name='stock_details'),
    
    # API for fetching individual transaction details
    path('api/transaction_details/<int:sale_id>/', views.transaction_details, name='transaction_details'),
    
    # SMS Notification URLs
    path('sms-settings/', views.sms_settings_view, name='sms_settings'),
    path('api/sms/test/', views.send_test_sms, name='send_test_sms'),
    path('api/sms/test-type/', views.test_notification_type, name='test_notification_type'),
    path('api/sms/settings/', views.update_notification_settings, name='update_notification_settings'),
    path('api/sms/stats/', views.get_notification_stats, name='get_notification_stats'),
    path('api/sms/send-all/', views.send_all_notifications_now, name='send_all_notifications_now'),
    path('api/sms/status/', views.check_sms_status, name='check_sms_status'),
    path('api/sms/credits/', views.check_sms_credits, name='check_sms_credits'),
    path('api/scheduler/health/', views.get_scheduler_health, name='get_scheduler_health'),
    
    # Pricing AI URLs
    path('api/pricing/recommendations/', views.get_pricing_recommendations, name='get_pricing_recommendations'),
    path('api/pricing/apply/', views.apply_pricing_recommendation, name='apply_pricing_recommendation'),
    path('api/pricing/reject/', views.reject_pricing_recommendation, name='reject_pricing_recommendation'),
    path('api/pricing/send/', views.send_pricing_notification, name='send_pricing_notification'),
    
    # Pricing Analysis URLs
    path('pricing-analysis/', views.pricing_analysis_view, name='pricing_analysis'),
    path('api/pricing-analysis/data/', views.get_pricing_analysis_data, name='get_pricing_analysis_data'),
    path('api/pricing-analysis/record-change/', views.record_price_change, name='record_price_change'),
    
    # Inventory Reports URLs
    path('api/inventory/reports/stock/', views.inventory_stock_report, name='inventory_stock_report'),
    path('api/inventory/reports/movement/', views.inventory_movement_report, name='inventory_movement_report'),
    path('api/inventory/reports/batches/', views.inventory_batch_report, name='inventory_batch_report'),
    path('api/inventory/reports/turnover/', views.inventory_turnover_report, name='inventory_turnover_report'),
    path('api/inventory/reports/suppliers/', views.inventory_supplier_report, name='inventory_supplier_report'),
    path('api/inventory/reports/pdf/', views.generate_inventory_pdf_report, name='generate_inventory_pdf_report'),
    
    # Backup management URLs
    path('backups/', views.backup_management_view, name='backup_management'),
    path('api/backups/create/', views.create_backup, name='create_backup'),
    path('api/backups/upload-restore/', views.upload_and_restore_backup, name='upload_and_restore_backup'),
    path('api/backups/<int:backup_id>/download/', views.download_backup, name='download_backup'),
    path('api/backups/<int:backup_id>/restore/', views.restore_backup, name='restore_backup'),
    path('api/backups/<int:backup_id>/delete/', views.delete_backup, name='delete_backup'),
]
