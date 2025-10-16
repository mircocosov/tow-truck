"""
Админ-панель Django для системы эвакуатора.

Настройка административного интерфейса для управления всеми моделями системы.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, VehicleType, TowTruck, Order, OrderStatusHistory,
    Payment, Rating, Notification
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Админ-панель для пользователей с расширенными полями.
    """
    
    list_display = ('username', 'email', 'phone', 'user_type', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'phone', 'avatar', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'phone', 'avatar', 'is_verified')
        }),
    )


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    """
    Админ-панель для типов транспортных средств.
    """
    
    list_display = ('name', 'max_weight', 'base_price')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(TowTruck)
class TowTruckAdmin(admin.ModelAdmin):
    """
    Админ-панель для эвакуаторов.
    """
    
    list_display = ('license_plate', 'model', 'driver', 'status', 'capacity')
    list_filter = ('status', 'vehicle_types')
    search_fields = ('license_plate', 'model', 'driver__username')
    filter_horizontal = ('vehicle_types',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('driver')


class OrderStatusHistoryInline(admin.TabularInline):
    """
    Инлайн для истории статусов заказа.
    """
    
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('timestamp',)
    fields = ('old_status', 'new_status', 'changed_by', 'comment', 'timestamp')


class PaymentInline(admin.TabularInline):
    """
    Инлайн для платежей заказа.
    """
    
    model = Payment
    extra = 0
    readonly_fields = ('created_at', 'paid_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Админ-панель для заказов эвакуации.
    """
    
    list_display = (
        'id', 'client', 'vehicle_make', 'vehicle_model', 'license_plate',
        'status', 'priority', 'estimated_price', 'created_at'
    )
    list_filter = ('status', 'priority', 'vehicle_type', 'created_at')
    search_fields = (
        'id', 'client__username', 'vehicle_make', 'vehicle_model',
        'license_plate', 'pickup_address', 'delivery_address'
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'id', 'client', 'vehicle_type', 'tow_truck', 'status', 'priority'
            )
        }),
        ('Информация о транспортном средстве', {
            'fields': (
                'vehicle_make', 'vehicle_model', 'vehicle_year',
                'vehicle_color', 'license_plate'
            )
        }),
        ('Местоположение', {
            'fields': (
                'pickup_address', 'pickup_latitude', 'pickup_longitude',
                'delivery_address', 'delivery_latitude', 'delivery_longitude'
            )
        }),
        ('Детали заказа', {
            'fields': ('description', 'scheduled_time')
        }),
        ('Ценообразование', {
            'fields': ('estimated_price', 'final_price')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderStatusHistoryInline, PaymentInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'client', 'vehicle_type', 'tow_truck', 'tow_truck__driver'
        )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """
    Админ-панель для истории статусов заказов.
    """
    
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'timestamp')
    list_filter = ('new_status', 'timestamp')
    search_fields = ('order__id', 'changed_by__username', 'comment')
    readonly_fields = ('timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'changed_by')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Админ-панель для платежей.
    """
    
    list_display = ('id', 'order', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'order__id', 'transaction_id')
    readonly_fields = ('created_at', 'paid_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """
    Админ-панель для рейтингов.
    """
    
    list_display = ('order', 'driver_rating', 'service_rating', 'created_at')
    list_filter = ('driver_rating', 'service_rating', 'created_at')
    search_fields = ('order__id', 'comment')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Админ-панель для уведомлений.
    """
    
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'related_order')


# Настройка заголовков админ-панели
admin.site.site_header = "Администрирование системы эвакуатора"
admin.site.site_title = "Система эвакуатора"
admin.site.index_title = "Панель управления"
