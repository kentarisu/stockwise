from django.urls import path
from . import views

urlpatterns = [
    path('inventory/', views.inventory_list, name='qr-inventory'),
    path('generate/<int:product_id>/', views.qr_generate, name='qr-generate'),
    path('sticker/<int:product_id>/', views.qr_sticker, name='qr-sticker'),
    path('confirm/<str:token>/', views.confirm_view, name='qr-confirm'),
    path('stock-details/<int:product_id>/', views.stock_details, name='qr-stock-details'),
]


