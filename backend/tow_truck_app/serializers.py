"""
Сериализаторы для API системы эвакуатора.

Сериализаторы для преобразования моделей Django в JSON и обратно
для REST API мобильного приложения.
"""

import re
import uuid

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import (
    User, VehicleType, TowTruck, Order, OrderStatusHistory,
    Payment, Rating, Notification, SupportTicket, SupportMessage
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей.
    """
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    username = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'phone', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
            'email': {'required': False, 'allow_blank': True},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
        }
    
    def validate_user_type(self, value):
        allowed_roles = {'CLIENT', 'DRIVER'}
        if value not in allowed_roles:
            raise serializers.ValidationError(
                "Регистрация доступна только для ролей CLIENT или DRIVER."
            )
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        username = self._generate_username(validated_data)
        user = User.objects.create_user(
            username=username,
            password=password,
            **validated_data
        )
        return user
    
    def _generate_username(self, data):
        base_source = data.get('phone') or data.get('email') or uuid.uuid4().hex[:8]
        base = re.sub(r'\W+', '', base_source).lower()
        if not base:
            base = uuid.uuid4().hex[:8]
        unique = base
        counter = 1
        while User.objects.filter(username=unique).exists():
            unique = f"{base}{counter}"
            counter += 1
        return unique


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователей.
    """
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'user_type', 'avatar', 'is_verified', 'date_joined'
        )
        read_only_fields = ('id', 'date_joined', 'is_verified')


class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации пользователей.
    """
    
    phone = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        
        if not phone or not password:
            raise serializers.ValidationError('Необходимо указать телефон и пароль')

        try:
            user_obj = User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError('Неверные учетные данные')

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise serializers.ValidationError('Неверные учетные данные')
        if not user.is_active:
            raise serializers.ValidationError('Аккаунт деактивирован')
        attrs['user'] = user
        return attrs


class VehicleTypeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для типов транспортных средств.
    """
    
    class Meta:
        model = VehicleType
        fields = '__all__'


class TowTruckSerializer(serializers.ModelSerializer):
    """
    Сериализатор для эвакуаторов.
    """
    
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    vehicle_types = VehicleTypeSerializer(many=True, read_only=True)
    
    class Meta:
        model = TowTruck
        fields = (
            'id', 'license_plate', 'model', 'capacity', 'vehicle_types',
            'driver', 'driver_name', 'status', 'current_location_lat',
            'current_location_lon', 'last_location_update'
        )


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для истории статусов заказа.
    """
    
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для платежей.
    """
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('created_at', 'paid_at')


class RatingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рейтингов.
    """
    
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ('created_at',)


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания заказов.
    """
    
    class Meta:
        model = Order
        exclude = ('id', 'client', 'tow_truck', 'status', 'created_at', 'updated_at', 'completed_at')
    
    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для заказов.
    """
    
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    driver_name = serializers.CharField(source='tow_truck.driver.get_full_name', read_only=True)
    tow_truck_info = TowTruckSerializer(source='tow_truck', read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    rating = RatingSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'completed_at')


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления заказов.
    """
    
    class Meta:
        model = Order
        fields = ('status', 'final_price', 'scheduled_time', 'completed_at')


class NotificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уведомлений.
    """
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('created_at',)
class SupportMessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = SupportMessage
        fields = ('id', 'author', 'body', 'is_internal', 'created_at')
        read_only_fields = ('id', 'author', 'created_at')


class SupportMessageCreateSerializer(serializers.ModelSerializer):
    is_internal = serializers.BooleanField(default=False)

    class Meta:
        model = SupportMessage
        fields = ('body', 'is_internal')

    def validate_is_internal(self, value):
        request = self.context.get('request')
        if value and request and getattr(request.user, 'user_type', None) != 'OPERATOR' and not request.user.is_staff:
            raise serializers.ValidationError("Internal notes are available only for operators.")
        return value


class SupportTicketSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    messages = SupportMessageSerializer(many=True, read_only=True)
    related_order_uuid = serializers.UUIDField(source='related_order_id', read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'author', 'subject', 'description', 'status', 'priority',
            'related_order', 'related_order_uuid', 'assigned_to', 'closed_at',
            'last_message_at', 'created_at', 'updated_at', 'messages'
        )
        read_only_fields = (
            'id', 'author', 'status', 'related_order', 'related_order_uuid', 'assigned_to', 'closed_at',
            'last_message_at', 'created_at', 'updated_at', 'messages',
        )


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    related_order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = SupportTicket
        fields = ('subject', 'description', 'priority', 'related_order')


class SupportTicketUpdateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='OPERATOR'),
        required=False,
        allow_null=True
    )

    class Meta:
        model = SupportTicket
        fields = ('status', 'priority', 'assigned_to', 'related_order')

    def validate_assigned_to(self, value):
        if value and getattr(value, 'user_type', None) != 'OPERATOR' and not value.is_staff:
            raise serializers.ValidationError("Assigned user must be an operator.")
        return value

    def update(self, instance, validated_data):
        status_before = instance.status
        instance = super().update(instance, validated_data)

        if instance.status in ('RESOLVED', 'CLOSED') and instance.closed_at is None:
            instance.closed_at = timezone.now()
            instance.save(update_fields=['closed_at'])
        elif status_before in ('RESOLVED', 'CLOSED') and instance.status in ('OPEN', 'IN_PROGRESS') and instance.closed_at:
            instance.closed_at = None
            instance.save(update_fields=['closed_at'])

        return instance
class PasswordResetSerializer(serializers.Serializer):
    phone = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Пароли должны совпадать.")
        try:
            user = User.objects.get(phone=attrs['phone'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'phone': 'Пользователь с таким номером не найден.'})
        attrs['user'] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user

class LocationUpdateSerializer(serializers.Serializer):
    """
    Сериализатор для обновления местоположения.
    """
    
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    
    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Широта должна быть между -90 и 90")
        return value
    
    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Долгота должна быть между -180 и 180")
        return value
