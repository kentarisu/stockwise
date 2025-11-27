# QR Stock URLs
from django.urls import path
from . import views

urlpatterns = [
    path('sticker/<int:product_id>/', views.qr_sticker_view, name='qr_sticker'),
    path('sticker/print/<int:product_id>/', views.qr_sticker_print, name='qr_sticker_print'),
    path('scan/', views.qr_scan_view, name='qr_scan'),
    path('test/<int:product_id>/', views.qr_test_view, name='qr_test'),
    path('scanner/', views.qr_scanner_view, name='qr_scanner'),
    path('generator/<int:product_id>/', views.qr_generator_view, name='qr_generator'),
    path('generate/<int:product_id>/', views.qr_generate_image, name='qr_generate_image'),
    path('debug/<int:product_id>/', views.qr_debug_view, name='qr_debug'),
    path('confirm/<str:token>/', views.qr_confirm_view, name='qr_confirm'),
]
