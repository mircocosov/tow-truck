"""
URL-маршруты для API системы эвакуатора.

Определяет все endpoints для мобильного приложения.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .jwt_serializers import CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer

# Создаем роутер для ViewSets (если понадобятся в будущем)
router = DefaultRouter()

app_name = 'tow_truck_app'

urlpatterns = [
    # Аутентификация
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', views.login_view, name='user-login'),
    path('auth/password/reset/', views.password_reset, name='password-reset'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Типы транспортных средств
    path('vehicle-types/', views.VehicleTypeListView.as_view(), name='vehicle-types'),
    path('vehicle-types/<int:pk>/', views.VehicleTypeDetailView.as_view(), name='vehicle-types-detail'),
    
    # Эвакуаторы
    path('tow-trucks/', views.TowTruckListView.as_view(), name='tow-trucks'),

    # Стоимость эвакуатора
    path('pricing/estimate/', views.PriceEstimateView.as_view(), name='price-estimate'),
    path('weather/', views.WeatherLookupView.as_view(), name='weather-lookup'),

    # Заказы
    path('orders/', views.OrderCreateView.as_view(), name='order-create'),
    path('orders/list/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:pk>/update-status/', views.OrderUpdateStatusView.as_view(), name='order-update-status'),
    
    # Платежи
    path('orders/<uuid:order_id>/payments/', views.PaymentCreateView.as_view(), name='payment-create'),
    
    # Рейтинги
    path('orders/<uuid:order_id>/rating/', views.RatingCreateView.as_view(), name='rating-create'),
    
    # Уведомления
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='notification-read'),
    # Support tickets
    path('support/tickets/', views.SupportTicketListCreateView.as_view(), name='support-ticket-list-create'),
    path('support/tickets/<uuid:pk>/', views.SupportTicketDetailView.as_view(), name='support-ticket-detail'),
    path('support/tickets/<uuid:ticket_id>/messages/', views.SupportMessageListCreateView.as_view(), name='support-ticket-messages'),

    
    # Местоположение
    path('location/update/', views.update_location, name='location-update'),
    
    # Статистика
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
]

# Добавляем маршруты из роутера
urlpatterns += router.urls


