"""
URL configuration for tow truck backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI конфигурация
schema_view = get_schema_view(
    openapi.Info(
        title="Система эвакуатора API",
        default_version='v1',
        description="""
        ## API v1 для системы эвакуатора

        Полнофункциональное REST API для управления заказами на эвакуацию транспортных средств.

        ### Поддерживаемые типы пользователей:
        - **Клиенты** - заказывают услуги эвакуации
        - **Водители** - выполняют заказы на эвакуацию  
        - **Операторы** - управляют заказами и назначают водителей

        ### Основные функции:
        - Регистрация и аутентификация пользователей с JWT токенами
        - Создание и управление заказами
        - Отслеживание местоположения эвакуаторов
        - Система платежей и рейтингов
        - Уведомления в реальном времени

        ### Аутентификация:
        Для доступа к защищенным endpoints используйте JWT токены.
        Получите токены через `/api/v1/auth/login/` и передавайте access токен в заголовке:
        ```
        Authorization: Bearer <access_token>
        ```

        ### Структура API:
        - **Base URL**: `/api/v1/`
        - **Access токен**: действует 60 минут
        - **Refresh токен**: действует 7 дней
        - **Обновление токена**: `/api/v1/auth/token/refresh/`
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="admin@towtruck.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Административная панель
    path('admin/', admin.site.urls),
    
    # API endpoints v1
    path('api/v1/', include('tow_truck_app.urls')),
    
    # Swagger UI
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # ReDoc
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)