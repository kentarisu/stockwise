from django.urls import path
from . import views

urlpatterns = [
    path('inventory/', views.inventory_list, name='qr-inventory'),
    path('generate/<int:product_id>/', views.qr_generate, name='qr-generate'),
    path('sticker/<int:product_id>/', views.qr_sticker, name='qr-sticker'),
    path('confirm/<str:token>/', views.confirm_view, name='qr-confirm'),
    path('add-stock/<str:token>/', views.qr_add_stock_view, name='qr-add-stock'),
    path('record-sale/<str:token>/', views.qr_record_sale_view, name='qr-record-sale'),
    path('stock-details/<int:product_id>/', views.stock_details, name='qr-stock-details'),
    path('next-batch-sequence/<int:product_id>/', views.get_next_batch_sequence, name='next-batch-sequence'),
    path('decode-token/', views.decode_token, name='qr-decode-token'),
]


