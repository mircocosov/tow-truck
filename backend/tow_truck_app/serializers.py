"""
Сериализаторы для API системы эвакуатора.

Сериализаторы для преобразования моделей Django в JSON и обратно
для REST API мобильного приложения.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, VehicleType, TowTruck, Order, OrderStatusHistory,
    Payment, Rating, Notification
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей.
    """
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'phone', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


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
    
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Неверные учетные данные')
            if not user.is_active:
                raise serializers.ValidationError('Аккаунт деактивирован')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Необходимо указать имя пользователя и пароль')


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
