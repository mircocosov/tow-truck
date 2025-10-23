"""
Django admin configuration for the tow truck backend.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    ClientVehicle,
    Notification,
    NotificationType,
    Order,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Rating,
    SupportMessage,
    SupportTicket,
    TicketStatus,
    TowTruck,
    User,
    UserType,
    VehicleType,
)


class ReferenceAdmin(admin.ModelAdmin):
    """Shared configuration for dictionary tables."""

    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


admin.site.register(UserType, ReferenceAdmin)
admin.site.register(PaymentMethod, ReferenceAdmin)
admin.site.register(PaymentStatus, ReferenceAdmin)
admin.site.register(NotificationType, ReferenceAdmin)
admin.site.register(TicketStatus, ReferenceAdmin)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin options for user accounts."""

    list_display = ("username", "email", "phone", "user_type", "is_verified", "is_active", "date_joined")
    list_filter = ("user_type", "is_verified", "is_active", "is_staff", "date_joined")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Дополнительные данные", {"fields": ("user_type", "phone", "avatar", "is_verified")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Дополнительные данные", {"fields": ("user_type", "phone", "avatar", "is_verified")}),
    )


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    """Supported tow truck categories."""

    list_display = ("name", "max_weight", "base_price", "per_km_rate", "updated_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)


@admin.register(TowTruck)
class TowTruckAdmin(admin.ModelAdmin):
    """Tow truck inventory."""

    list_display = ("license_plate", "model", "driver", "status", "capacity", "updated_at")
    list_filter = ("status", "vehicle_types")
    search_fields = ("license_plate", "model", "driver__username")
    filter_horizontal = ("vehicle_types",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("driver")


@admin.register(ClientVehicle)
class ClientVehicleAdmin(admin.ModelAdmin):
    """Client vehicles (ТС)."""

    list_display = ("license_plate", "owner", "make", "model", "year", "updated_at")
    search_fields = ("license_plate", "owner__username", "make", "model")
    list_filter = ("year",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("owner",)


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline history of status changes inside the order screen."""

    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("old_status", "new_status", "changed_by", "comment", "created_at")


class PaymentInline(admin.TabularInline):
    """Inline list of payments for an order."""

    model = Payment
    extra = 0
    readonly_fields = ("created_at", "updated_at", "paid_at")
    autocomplete_fields = ("payment_method", "status")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Service orders."""

    list_display = ("id", "client", "vehicle", "status", "priority", "estimated_price", "created_at")
    list_filter = ("status", "priority", "vehicle_type", "created_at")
    search_fields = (
        "id",
        "client__username",
        "vehicle__license_plate",
        "vehicle__make",
        "vehicle__model",
        "pickup_address",
        "delivery_address",
    )
    readonly_fields = ("id", "created_at", "updated_at", "completed_at")
    autocomplete_fields = ("client", "vehicle", "vehicle_type", "tow_truck")
    inlines = [OrderStatusHistoryInline, PaymentInline]

    fieldsets = (
        ("Основные сведения", {"fields": ("id", "client", "vehicle", "vehicle_type", "tow_truck", "status", "priority")}),
        (
            "Маршрут",
            {
                "fields": (
                    "pickup_address",
                    "pickup_latitude",
                    "pickup_longitude",
                    "delivery_address",
                    "delivery_latitude",
                    "delivery_longitude",
                )
            },
        ),
        ("Описание и план", {"fields": ("description", "scheduled_time")}),
        ("Стоимость", {"fields": ("estimated_price", "final_price")}),
        ("Служебные поля", {"fields": ("created_at", "updated_at", "completed_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "client", "vehicle", "vehicle_type", "tow_truck", "tow_truck__driver"
        )


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Dedicated page for order status changes."""

    list_display = ("order", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("new_status", "created_at")
    search_fields = ("order__id", "changed_by__username", "comment")
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "changed_by")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payments attached to orders."""

    list_display = ("id", "order", "amount", "payment_method", "status", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("id", "order__id", "transaction_id")
    readonly_fields = ("created_at", "updated_at", "paid_at")
    autocomplete_fields = ("order", "payment_method", "status")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "payment_method", "status")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Ratings left by clients."""

    list_display = ("order", "driver_rating", "service_rating", "created_at")
    list_filter = ("driver_rating", "service_rating", "created_at")
    search_fields = ("order__id", "comment")
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """User notifications."""

    list_display = ("user", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("user__username", "title", "message")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user", "notification_type", "related_order")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "notification_type", "related_order")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """Support tickets and escalation."""

    list_display = ("id", "subject", "author", "status", "priority", "assigned_to", "created_at")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("id", "subject", "author__username", "assigned_to__username")
    readonly_fields = ("id", "created_at", "updated_at", "closed_at", "last_message_at")
    autocomplete_fields = ("author", "assigned_to", "related_order", "status")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author", "assigned_to", "related_order", "status")


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    """Messages inside support tickets."""

    list_display = ("id", "ticket", "author", "is_internal", "created_at")
    list_filter = ("is_internal", "created_at")
    search_fields = ("ticket__id", "ticket__subject", "author__username", "body")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("ticket", "author")
    ordering = ("-created_at",)


admin.site.site_header = "Система эвакуации — администрирование"
admin.site.site_title = "Панель управления сервисом эвакуации"
admin.site.index_title = "Добро пожаловать в административный раздел"
