"""
API Views для системы эвакуатора.

Представления для обработки HTTP-запросов от мобильного приложения.
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db.models import Q, F
from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import (
    User, VehicleType, TowTruck, Order, OrderStatusHistory,
    Payment, Rating, Notification
)
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserLoginSerializer,
    VehicleTypeSerializer, TowTruckSerializer, OrderCreateSerializer,
    OrderSerializer, OrderUpdateSerializer, PaymentSerializer,
    RatingSerializer, NotificationSerializer, LocationUpdateSerializer
)
from .jwt_serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint для регистрации новых пользователей.
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Создаем JWT токены для пользователя
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_description="Аутентификация пользователя в системе с JWT токенами",
    request_body=UserLoginSerializer,
    responses={
        200: openapi.Response(
            description="Успешная аутентификация",
            examples={
                "application/json": {
                    "user": {
                        "id": 1,
                        "username": "client1",
                        "email": "client1@example.com",
                        "user_type": "CLIENT"
                    },
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                }
            }
        ),
        400: openapi.Response(description="Неверные учетные данные")
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    API endpoint для аутентификации пользователей с JWT токенами.
    """
    
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Создаем JWT токены
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint для получения и обновления профиля пользователя.
    """
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class VehicleTypeListView(generics.ListAPIView):
    """
    API endpoint для получения списка типов транспортных средств.
    """
    
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [AllowAny]


class TowTruckListView(generics.ListAPIView):
    """
    API endpoint для получения списка доступных эвакуаторов.
    """
    
    serializer_class = TowTruckSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = TowTruck.objects.filter(status='AVAILABLE').select_related('driver')
        
        # Фильтрация по типу транспортного средства
        vehicle_type_id = self.request.query_params.get('vehicle_type')
        if vehicle_type_id:
            queryset = queryset.filter(vehicle_types__id=vehicle_type_id)
        
        return queryset


class OrderCreateView(generics.CreateAPIView):
    """
    API endpoint для создания новых заказов.
    """
    
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
        
        # Создаем уведомление для операторов
        Notification.objects.create(
            user=self.request.user,
            notification_type='ORDER_CREATED',
            title='Заказ создан',
            message=f'Ваш заказ на эвакуацию создан и ожидает подтверждения.',
            related_order=serializer.instance
        )


class OrderListView(generics.ListAPIView):
    """
    API endpoint для получения списка заказов пользователя.
    """
    
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Проверка для Swagger генерации схемы
        if not user.is_authenticated:
            return Order.objects.none()
        
        if user.user_type == 'CLIENT':
            return Order.objects.filter(client=user).select_related(
                'client', 'vehicle_type', 'tow_truck', 'tow_truck__driver'
            )
        elif user.user_type == 'DRIVER':
            return Order.objects.filter(tow_truck__driver=user).select_related(
                'client', 'vehicle_type', 'tow_truck', 'tow_truck__driver'
            )
        elif user.user_type == 'OPERATOR':
            return Order.objects.all().select_related(
                'client', 'vehicle_type', 'tow_truck', 'tow_truck__driver'
            )
        
        return Order.objects.none()


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint для получения детальной информации о заказе и его обновления.
    """
    
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'CLIENT':
            return Order.objects.filter(client=user)
        elif user.user_type == 'DRIVER':
            return Order.objects.filter(tow_truck__driver=user)
        elif user.user_type == 'OPERATOR':
            return Order.objects.all()
        
        return Order.objects.none()


class OrderUpdateStatusView(generics.UpdateAPIView):
    """
    API endpoint для обновления статуса заказа.
    """
    
    serializer_class = OrderUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'DRIVER':
            return Order.objects.filter(tow_truck__driver=user)
        elif user.user_type == 'OPERATOR':
            return Order.objects.all()
        
        return Order.objects.none()
    
    def perform_update(self, serializer):
        order = self.get_object()
        old_status = order.status
        
        serializer.save()
        
        # Создаем запись в истории статусов
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=order.status,
            changed_by=self.request.user
        )
        
        # Создаем уведомления
        self.create_status_notification(order, old_status)
    
    def create_status_notification(self, order, old_status):
        """
        Создает уведомления при изменении статуса заказа.
        """
        
        notification_messages = {
            'CONFIRMED': {
                'title': 'Заказ подтвержден',
                'message': f'Ваш заказ {order.id} подтвержден и ожидает назначения водителя.'
            },
            'ASSIGNED': {
                'title': 'Водитель назначен',
                'message': f'К вашему заказу {order.id} назначен водитель.'
            },
            'IN_PROGRESS': {
                'title': 'Эвакуация началась',
                'message': f'Водитель выехал к месту забора для заказа {order.id}.'
            },
            'COMPLETED': {
                'title': 'Заказ завершен',
                'message': f'Ваш заказ {order.id} успешно завершен.'
            },
            'CANCELLED': {
                'title': 'Заказ отменен',
                'message': f'Ваш заказ {order.id} был отменен.'
            }
        }
        
        if order.status in notification_messages:
            Notification.objects.create(
                user=order.client,
                notification_type=f'ORDER_{order.status}',
                title=notification_messages[order.status]['title'],
                message=notification_messages[order.status]['message'],
                related_order=order
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location(request):
    """
    API endpoint для обновления местоположения водителя.
    """
    
    if request.user.user_type != 'DRIVER':
        return Response(
            {'error': 'Только водители могут обновлять местоположение'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = LocationUpdateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            tow_truck = TowTruck.objects.get(driver=request.user)
            tow_truck.current_location_lat = serializer.validated_data['latitude']
            tow_truck.current_location_lon = serializer.validated_data['longitude']
            tow_truck.save()
            
            return Response({'message': 'Местоположение обновлено'})
        except TowTruck.DoesNotExist:
            return Response(
                {'error': 'Эвакуатор не найден для данного водителя'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentCreateView(generics.CreateAPIView):
    """
    API endpoint для создания платежей.
    """
    
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, client=self.request.user)
        serializer.save(order=order)


class RatingCreateView(generics.CreateAPIView):
    """
    API endpoint для создания рейтингов.
    """
    
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id, client=self.request.user, status='COMPLETED')
        serializer.save(order=order)


class NotificationListView(generics.ListAPIView):
    """
    API endpoint для получения уведомлений пользователя.
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    API endpoint для отметки уведомления как прочитанного.
    """
    
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.is_read = True
    notification.save()
    
    return Response({'message': 'Уведомление отмечено как прочитанное'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    API endpoint для получения статистики для дашборда.
    """
    
    user = request.user
    
    if user.user_type == 'CLIENT':
        stats = {
            'total_orders': Order.objects.filter(client=user).count(),
            'active_orders': Order.objects.filter(
                client=user,
                status__in=['PENDING', 'CONFIRMED', 'ASSIGNED', 'IN_PROGRESS']
            ).count(),
            'completed_orders': Order.objects.filter(
                client=user,
                status='COMPLETED'
            ).count(),
            'unread_notifications': Notification.objects.filter(
                user=user,
                is_read=False
            ).count()
        }
    
    elif user.user_type == 'DRIVER':
        driver_orders = Order.objects.filter(tow_truck__driver=user)
        stats = {
            'total_orders': driver_orders.count(),
            'active_orders': driver_orders.filter(
                status__in=['ASSIGNED', 'IN_PROGRESS']
            ).count(),
            'completed_orders': driver_orders.filter(
                status='COMPLETED'
            ).count(),
            'avg_rating': driver_orders.filter(
                rating__isnull=False
            ).aggregate(
                avg_rating=models.Avg('rating__driver_rating')
            )['avg_rating'] or 0,
            'unread_notifications': Notification.objects.filter(
                user=user,
                is_read=False
            ).count()
        }
    
    elif user.user_type == 'OPERATOR':
        stats = {
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(status='PENDING').count(),
            'active_orders': Order.objects.filter(
                status__in=['CONFIRMED', 'ASSIGNED', 'IN_PROGRESS']
            ).count(),
            'available_trucks': TowTruck.objects.filter(status='AVAILABLE').count(),
            'unread_notifications': Notification.objects.filter(
                user=user,
                is_read=False
            ).count()
        }
    
    return Response(stats)
