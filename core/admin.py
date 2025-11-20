from django.contrib import admin
from .models import Product, StockAddition, AppUser, Sale, SMS, ReportProductSummary, ActionLog, Backup, SMSNotificationSettings


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "name", "quantity_unit", "status", "price", "cost", "date_added", "stock")
    list_filter = ("status",)
    search_fields = ("name", "quantity_unit")
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


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "role", "action", "ip_address")
    list_filter = ("role", "created_at")
    search_fields = ("action", "details", "user__username", "ip_address")


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ("backup_id", "filename", "file_size", "backup_type", "created_at", "created_by", "is_verified")
    list_filter = ("backup_type", "created_at", "is_verified")
    search_fields = ("filename", "created_by")
    readonly_fields = ("backup_id", "created_at")
    ordering = ("-created_at",)


@admin.register(SMSNotificationSettings)
class SMSNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ("setting_id", "sales_enabled", "sales_time", "stock_enabled", "stock_threshold", "pricing_enabled", "pricing_sensitivity", "updated_at")
    readonly_fields = ("setting_id", "created_at", "updated_at")
    fieldsets = (
        ('Sales Notifications', {
            'fields': ('sales_enabled', 'sales_time')
        }),
        ('Stock Alerts', {
            'fields': ('stock_enabled', 'stock_threshold')
        }),
        ('Pricing Recommendations', {
            'fields': ('pricing_enabled', 'pricing_sensitivity')
        }),
        ('Metadata', {
            'fields': ('setting_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
