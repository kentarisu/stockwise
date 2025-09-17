from django.contrib import admin
from .models import Product, StockAddition, AppUser, Sale, SMS, ReportProductSummary


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "name", "size", "status", "price", "cost", "date_added", "stock")
    list_filter = ("status",)
    search_fields = ("name", "size")
    ordering = ("product_id",)

@admin.register(StockAddition)
class StockAdditionAdmin(admin.ModelAdmin):
    list_display = ("addition_id", "product", "quantity", "remaining_quantity", "cost", "batch_id", "date_added", "created_at")
    search_fields = ("product__name", "batch_id")
    list_filter = ("date_added", "product")


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "username", "role", "phone_number")
    list_filter = ("role",)
    search_fields = ("username", "phone_number")
    ordering = ("user_id",)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("sale_id", "product", "quantity", "price", "total", "status", "user", "recorded_at")
    list_filter = ("status", "recorded_at", "product")
    search_fields = ("or_number", "user__username", "product__name")
    date_hierarchy = "recorded_at"

@admin.register(SMS)
class SMSAdmin(admin.ModelAdmin):
    list_display = ("sms_id", "product", "user", "message_type", "demand_level", "sent_at")
    list_filter = ("message_type", "demand_level", "sent_at")
    search_fields = ("product__name", "user__username")


@admin.register(ReportProductSummary)
class ReportProductSummaryAdmin(admin.ModelAdmin):
    list_display = ("report_id", "product", "period_start", "period_end", "granularity", "revenue", "cogs", "gross_profit")
    list_filter = ("granularity", "period_start", "period_end")
    search_fields = ("product__name",)
