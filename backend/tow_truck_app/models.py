"""
Core data models for the tow truck backend.

This module contains user management entities together with the operational
domain models required by the updated entity-relationship diagram.
"""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TimestampedModel(models.Model):
    """Abstract helper that adds created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name="Updated at")

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class ReferenceModel(TimestampedModel):
    """
    Abstract base for simple dictionary/lookup tables that have a human readable
    name and machine friendly code.
    """

    code = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name="Code",
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Name",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    is_active = models.BooleanField(default=True, verbose_name="Is active")

    class Meta(TimestampedModel.Meta):
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return self.name


class UserType(ReferenceModel):
    """Dictionary with allowed user roles (client, driver, operator)."""

    class Meta(ReferenceModel.Meta):
        verbose_name = "User type"
        verbose_name_plural = "User types"


class PaymentMethod(ReferenceModel):
    """Dictionary for supported payment methods."""

    class Meta(ReferenceModel.Meta):
        verbose_name = "Payment method"
        verbose_name_plural = "Payment methods"


class PaymentStatus(ReferenceModel):
    """Dictionary for payment processing statuses."""

    class Meta(ReferenceModel.Meta):
        verbose_name = "Payment status"
        verbose_name_plural = "Payment statuses"


class NotificationType(ReferenceModel):
    """Dictionary for notification classification."""

    class Meta(ReferenceModel.Meta):
        verbose_name = "Notification type"
        verbose_name_plural = "Notification types"


class TicketStatus(ReferenceModel):
    """Dictionary for support ticket statuses."""

    class Meta(ReferenceModel.Meta):
        verbose_name = "Ticket status"
        verbose_name_plural = "Ticket statuses"


class User(AbstractUser):
    """
    Custom user model that stores the role through the ``UserType`` dictionary.
    """

    user_type = models.ForeignKey(
        UserType,
        to_field="code",
        db_column="user_type",
        related_name="users",
        on_delete=models.PROTECT,
        verbose_name="User type",
    )
    phone = models.CharField(max_length=15, unique=True, verbose_name="Phone")
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Avatar",
    )
    is_verified = models.BooleanField(default=False, verbose_name="Phone verified")

    # Override related names from AbstractUser to avoid clashes inside the project.
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="tow_truck_user_set",
        related_query_name="tow_truck_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="tow_truck_user_set",
        related_query_name="tow_truck_user",
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        type_name = self.user_type.name if self.user_type else "Unknown"
        return f"{self.username} ({type_name})"

    @property
    def user_type_code(self) -> str | None:
        """Backward compatible accessor that returns the user type code."""
        return self.user_type_id

    def has_user_type(self, code: str) -> bool:
        """Convenience helper to compare user type codes."""
        return self.user_type_id == code


class VehicleType(TimestampedModel):
    """Type of tow truck that can handle different categories of vehicles."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Description")
    max_weight = models.FloatField(verbose_name="Max weight (tons)")
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Base price",
    )
    per_km_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Rate per km",
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = "Tow truck type"
        verbose_name_plural = "Tow truck types"
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return self.name


class ClientVehicle(TimestampedModel):
    """Client owned vehicle (ТС) that can be linked to orders."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Vehicle ID",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="vehicles",
        limit_choices_to={"user_type__code": "CLIENT"},
        verbose_name="Owner",
    )
    nickname = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Nickname",
    )
    make = models.CharField(max_length=100, verbose_name="Make")
    model = models.CharField(max_length=100, verbose_name="Model")
    year = models.PositiveIntegerField(verbose_name="Year")
    color = models.CharField(max_length=50, blank=True, verbose_name="Color")
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="License plate",
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta(TimestampedModel.Meta):
        verbose_name = "Client vehicle"
        verbose_name_plural = "Client vehicles"
        ordering = ["make", "model", "license_plate"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"{self.make} {self.model} ({self.license_plate})"


class TowTruck(TimestampedModel):
    """Tow truck that can serve orders."""

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("BUSY", "Busy"),
        ("MAINTENANCE", "Maintenance"),
        ("OFFLINE", "Offline"),
    ]

    license_plate = models.CharField(max_length=20, unique=True, verbose_name="Plate")
    model = models.CharField(max_length=100, verbose_name="Model")
    capacity = models.FloatField(verbose_name="Capacity (tons)")
    vehicle_types = models.ManyToManyField(
        VehicleType,
        related_name="tow_trucks",
        verbose_name="Supported vehicle types",
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"user_type__code": "DRIVER"},
        verbose_name="Driver",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="AVAILABLE",
        verbose_name="Status",
    )
    current_location_lat = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Current latitude",
    )
    current_location_lon = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Current longitude",
    )
    last_location_update = models.DateTimeField(
        auto_now=True,
        verbose_name="Last location update",
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = "Tow truck"
        verbose_name_plural = "Tow trucks"
        ordering = ["license_plate"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"{self.model} ({self.license_plate})"


class Order(TimestampedModel):
    """Tow service order created by clients."""

    STATUS_CHOICES = [
        ("PENDING", "Pending approval"),
        ("CONFIRMED", "Confirmed"),
        ("ASSIGNED", "Driver assigned"),
        ("IN_PROGRESS", "In progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("NORMAL", "Normal"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Order ID",
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type__code": "CLIENT"},
        related_name="orders",
        verbose_name="Client",
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.CASCADE,
        verbose_name="Required tow truck type",
    )
    tow_truck = models.ForeignKey(
        TowTruck,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Assigned tow truck",
    )
    vehicle = models.ForeignKey(
        ClientVehicle,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Client vehicle",
        null=True,
        blank=True,
    )
    pickup_address = models.TextField(verbose_name="Pickup address")
    pickup_latitude = models.FloatField(verbose_name="Pickup latitude")
    pickup_longitude = models.FloatField(verbose_name="Pickup longitude")
    delivery_address = models.TextField(verbose_name="Delivery address")
    delivery_latitude = models.FloatField(verbose_name="Delivery latitude")
    delivery_longitude = models.FloatField(verbose_name="Delivery longitude")
    description = models.TextField(blank=True, verbose_name="Description")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="NORMAL",
        verbose_name="Priority",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name="Status",
    )
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Estimated price",
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Final price",
    )
    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Scheduled time",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed at",
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"Order {self.id} - {self.vehicle.make} {self.vehicle.model}"


class OrderStatusHistory(TimestampedModel):
    """History of status transitions for orders."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Order",
    )
    old_status = models.CharField(
        max_length=15,
        choices=Order.STATUS_CHOICES,
        verbose_name="Old status",
    )
    new_status = models.CharField(
        max_length=15,
        choices=Order.STATUS_CHOICES,
        verbose_name="New status",
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Changed by",
    )
    comment = models.TextField(blank=True, verbose_name="Comment")

    class Meta(TimestampedModel.Meta):
        verbose_name = "Order status history"
        verbose_name_plural = "Order status history"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"{self.order.id}: {self.old_status} → {self.new_status}"


class Payment(TimestampedModel):
    """Payment tied to an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Order",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Amount",
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        to_field="code",
        db_column="payment_method",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Payment method",
    )
    status = models.ForeignKey(
        PaymentStatus,
        to_field="code",
        db_column="status",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Payment status",
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Transaction ID",
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Paid at",
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"Payment {self.id} - {self.amount}"


class Rating(TimestampedModel):
    """Rating submitted by a client after the order is completed."""

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="rating",
        verbose_name="Order",
    )
    driver_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Driver rating",
    )
    service_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Service rating",
    )
    comment = models.TextField(blank=True, verbose_name="Comment")

    class Meta(TimestampedModel.Meta):
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"Rating for order {self.order.id}"


class Notification(TimestampedModel):
    """Notification delivered to a user."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="User",
    )
    notification_type = models.ForeignKey(
        NotificationType,
        to_field="code",
        db_column="notification_type",
        on_delete=models.PROTECT,
        related_name="notifications",
        verbose_name="Notification type",
    )
    title = models.CharField(max_length=200, verbose_name="Title")
    message = models.TextField(verbose_name="Message")
    is_read = models.BooleanField(default=False, verbose_name="Is read")
    related_order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Related order",
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"{self.title} - {self.user.username}"


class SupportTicket(TimestampedModel):
    """Support ticket created by a user."""

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("NORMAL", "Normal"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Ticket ID",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name="Author",
    )
    subject = models.CharField(max_length=255, verbose_name="Subject")
    description = models.TextField(verbose_name="Initial description")
    status = models.ForeignKey(
        TicketStatus,
        to_field="code",
        db_column="status",
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Status",
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="NORMAL",
        verbose_name="Priority",
    )
    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related order",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_support_tickets",
        limit_choices_to={"user_type__code": "OPERATOR"},
        verbose_name="Assigned operator",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Closed at",
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last message at",
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = "Support ticket"
        verbose_name_plural = "Support tickets"

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        return f"{self.subject} ({self.status_id})"


class SupportMessage(TimestampedModel):
    """Single message in a support ticket conversation."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="Message ID",
    )
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Ticket",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="support_messages",
        verbose_name="Author",
    )
    body = models.TextField(verbose_name="Body")
    is_internal = models.BooleanField(default=False, verbose_name="Internal note")

    class Meta(TimestampedModel.Meta):
        verbose_name = "Support message"
        verbose_name_plural = "Support messages"
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple display hook
        ts = self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "?"
        return f"Message by {self.author} at {ts}"
