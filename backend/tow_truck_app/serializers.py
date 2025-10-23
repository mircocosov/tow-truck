"""
REST framework serializers for the tow truck backend.
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

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


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Handles client/driver self-registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    username = serializers.CharField(read_only=True)
    user_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=UserType.objects.filter(code__in=["CLIENT", "DRIVER"]),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "phone",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "user_type",
        )
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        username = self._generate_username(validated_data)
        user = User.objects.create_user(username=username, password=password, **validated_data)
        return user

    def _generate_username(self, data: dict) -> str:
        source = data.get("phone") or data.get("email") or uuid.uuid4().hex[:8]
        base = re.sub(r"\W+", "", source).lower() or uuid.uuid4().hex[:8]
        candidate = base
        counter = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base}{counter}"
            counter += 1
        return candidate


class UserSerializer(serializers.ModelSerializer):
    """Basic user representation."""

    user_type = serializers.CharField(source="user_type_id", read_only=True)
    user_type_label = serializers.CharField(source="user_type.name", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "user_type",
            "user_type_label",
            "avatar",
            "is_verified",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined", "is_verified")


class UserLoginSerializer(serializers.Serializer):
    """Authenticate user by phone and password."""

    phone = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")

        if not phone or not password:
            raise serializers.ValidationError("Номер телефона и пароль обязательны.")

        try:
            user_obj = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Неверный телефон или пароль.")

        user = authenticate(username=user_obj.username, password=password)
        if not user or not user.is_active:
            raise serializers.ValidationError("Неверный телефон или пароль.")

        attrs["user"] = user
        return attrs


class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = ("code", "name", "description")


class VehicleTypeSerializer(serializers.ModelSerializer):
    """Serializer for tow truck types."""

    class Meta:
        model = VehicleType
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class TowTruckSerializer(serializers.ModelSerializer):
    """Serializer for tow trucks."""

    vehicle_types = VehicleTypeSerializer(many=True, read_only=True)
    driver = UserSerializer(read_only=True)

    class Meta:
        model = TowTruck
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "last_location_update")


class ClientVehicleSerializer(serializers.ModelSerializer):
    """Serializer for client vehicles."""

    owner = UserSerializer(read_only=True)

    class Meta:
        model = ClientVehicle
        fields = "__all__"
        read_only_fields = ("id", "owner", "created_at", "updated_at")


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Order status transitions."""

    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for order payments."""

    payment_method = serializers.SlugRelatedField(
        slug_field="code",
        queryset=PaymentMethod.objects.all(),
    )
    status = serializers.SlugRelatedField(
        slug_field="code",
        queryset=PaymentStatus.objects.all(),
    )

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "paid_at")


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for customer ratings."""

    class Meta:
        model = Rating
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer used when creating orders."""

    vehicle = serializers.PrimaryKeyRelatedField(queryset=ClientVehicle.objects.all())

    class Meta:
        model = Order
        exclude = ("id", "client", "tow_truck", "status", "created_at", "updated_at", "completed_at")

    def validate_vehicle(self, value: ClientVehicle):
        request = self.context.get("request")
        if request and value.owner_id != request.user.id:
            raise serializers.ValidationError("Можно выбрать только собственное ТС.")
        return value

    def create(self, validated_data):
        validated_data["client"] = self.context["request"].user
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """Detailed order serializer with nested relations."""

    client = UserSerializer(read_only=True)
    tow_truck = TowTruckSerializer(read_only=True)
    vehicle = ClientVehicleSerializer(read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    rating = RatingSerializer(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "completed_at")


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Update subset of order fields."""

    class Meta:
        model = Order
        fields = ("status", "final_price", "scheduled_time", "completed_at", "tow_truck")


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    notification_type = serializers.SlugRelatedField(
        slug_field="code",
        queryset=NotificationType.objects.all(),
    )

    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class SupportMessageSerializer(serializers.ModelSerializer):
    """Support message view."""

    author = UserSerializer(read_only=True)

    class Meta:
        model = SupportMessage
        fields = ("id", "author", "body", "is_internal", "created_at")
        read_only_fields = ("id", "author", "created_at", "updated_at")


class SupportMessageCreateSerializer(serializers.ModelSerializer):
    """Create support message with optional internal flag."""

    is_internal = serializers.BooleanField(default=False)

    class Meta:
        model = SupportMessage
        fields = ("body", "is_internal")

    def validate_is_internal(self, value):
        request = self.context.get("request")
        if (
            value
            and request
            and not request.user.is_staff
            and not request.user.has_user_type("OPERATOR")
        ):
            raise serializers.ValidationError("Внутренние заметки доступны только операторам.")
        return value


class SupportTicketSerializer(serializers.ModelSerializer):
    """Detailed support ticket representation."""

    author = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    messages = SupportMessageSerializer(many=True, read_only=True)
    related_order_uuid = serializers.UUIDField(source="related_order_id", read_only=True)
    status = serializers.CharField(source="status_id", read_only=True)
    status_label = serializers.CharField(source="status.name", read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "author",
            "subject",
            "description",
            "status",
            "status_label",
            "priority",
            "related_order",
            "related_order_uuid",
            "assigned_to",
            "closed_at",
            "last_message_at",
            "created_at",
            "updated_at",
            "messages",
        )
        read_only_fields = (
            "id",
            "author",
            "status",
            "status_label",
            "related_order",
            "related_order_uuid",
            "assigned_to",
            "closed_at",
            "last_message_at",
            "created_at",
            "updated_at",
            "messages",
        )


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Create support ticket from client/operator."""

    related_order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SupportTicket
        fields = ("subject", "description", "priority", "related_order")


class SupportTicketUpdateSerializer(serializers.ModelSerializer):
    """Update support ticket status, priority and assignment."""

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    status = serializers.SlugRelatedField(
        slug_field="code",
        queryset=TicketStatus.objects.all(),
    )

    class Meta:
        model = SupportTicket
        fields = ("status", "priority", "assigned_to", "related_order")

    def validate_assigned_to(self, value: User | None):
        if value and not (value.is_staff or value.has_user_type("OPERATOR")):
            raise serializers.ValidationError("Назначать можно только операторов.")
        return value

    def update(self, instance, validated_data):
        previous_status = instance.status_id
        instance = super().update(instance, validated_data)

        closed_codes = {"RESOLVED", "CLOSED"}
        reopened_codes = {"OPEN", "IN_PROGRESS"}

        if instance.status_id in closed_codes and instance.closed_at is None:
            instance.closed_at = timezone.now()
            instance.save(update_fields=["closed_at"])
        elif previous_status in closed_codes and instance.status_id in reopened_codes and instance.closed_at:
            instance.closed_at = None
            instance.save(update_fields=["closed_at"])

        return instance


class PriceEstimateRequestSerializer(serializers.Serializer):
    """Input payload for calculating tow truck price."""

    vehicle_type = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all())
    distance_km = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=Decimal("0.01"))
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class PriceEstimateResponseSerializer(serializers.Serializer):
    """Serializer used for documenting the response payload."""

    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    breakdown = serializers.DictField()


class WeatherRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class WeatherResponseSerializer(serializers.Serializer):
    provider = serializers.CharField(allow_null=True, required=False)
    condition = serializers.CharField(allow_null=True)
    temperature = serializers.FloatField(allow_null=True)
    feels_like = serializers.FloatField(allow_null=True)
    wind_speed = serializers.FloatField(allow_null=True)
    pressure_mm = serializers.FloatField(allow_null=True)
    raw = serializers.DictField()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer to reset password via phone."""

    phone = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Пароли не совпадают.")
        try:
            user = User.objects.get(phone=attrs["phone"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"phone": "Пользователь с таким номером не найден."})
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class LocationUpdateSerializer(serializers.Serializer):
    """Serializer to update tow truck coordinates."""

    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Широта должна быть в диапазоне от -90 до 90.")
        return value

    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Долгота должна быть в диапазоне от -180 до 180.")
        return value
