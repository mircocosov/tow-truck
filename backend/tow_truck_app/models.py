"""
Модели данных для системы эвакуатора.

Этот модуль содержит все модели данных, необходимые для работы системы эвакуатора:
- Пользователи (клиенты, водители, операторы)
- Транспортные средства
- Заказы на эвакуацию
- Отслеживание местоположения
- Платежи и ценообразование
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Расширенная модель пользователя Django для системы эвакуатора.
    
    Поддерживает три типа пользователей:
    - CLIENT: клиент, заказывающий эвакуацию
    - DRIVER: водитель эвакуатора
    - OPERATOR: оператор диспетчерской
    """
    
    USER_TYPE_CHOICES = [
        ('CLIENT', 'Клиент'),
        ('DRIVER', 'Водитель'),
        ('OPERATOR', 'Оператор'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='CLIENT',
        verbose_name='Тип пользователя'
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        verbose_name='Номер телефона'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Верифицирован'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    # Переопределяем related_name для избежания конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="tow_truck_user_set",
        related_query_name="tow_truck_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="tow_truck_user_set",
        related_query_name="tow_truck_user",
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class VehicleType(models.Model):
    """
    Типы транспортных средств для эвакуации.
    
    Определяет категории автомобилей и соответствующие эвакуаторы.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название типа'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    max_weight = models.FloatField(
        verbose_name='Максимальный вес (тонны)'
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Базовая цена'
    )
    
    class Meta:
        verbose_name = 'Тип транспортного средства'
        verbose_name_plural = 'Типы транспортных средств'
    
    def __str__(self):
        return self.name


class TowTruck(models.Model):
    """
    Модель эвакуатора.
    
    Содержит информацию об эвакуаторах, их характеристиках и статусе.
    """
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Доступен'),
        ('BUSY', 'Занят'),
        ('MAINTENANCE', 'На обслуживании'),
        ('OFFLINE', 'Недоступен'),
    ]
    
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Госномер'
    )
    model = models.CharField(
        max_length=100,
        verbose_name='Модель'
    )
    capacity = models.FloatField(
        verbose_name='Грузоподъемность (тонны)'
    )
    vehicle_types = models.ManyToManyField(
        VehicleType,
        related_name='tow_trucks',
        verbose_name='Поддерживаемые типы ТС'
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'DRIVER'},
        verbose_name='Водитель'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='AVAILABLE',
        verbose_name='Статус'
    )
    current_location_lat = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Широта текущего местоположения'
    )
    current_location_lon = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Долгота текущего местоположения'
    )
    last_location_update = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее обновление местоположения'
    )
    
    class Meta:
        verbose_name = 'Эвакуатор'
        verbose_name_plural = 'Эвакуаторы'
    
    def __str__(self):
        return f"{self.model} ({self.license_plate})"


class Order(models.Model):
    """
    Модель заказа на эвакуацию.
    
    Основная модель для управления заказами эвакуации.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает подтверждения'),
        ('CONFIRMED', 'Подтвержден'),
        ('ASSIGNED', 'Назначен водитель'),
        ('IN_PROGRESS', 'Выполняется'),
        ('COMPLETED', 'Завершен'),
        ('CANCELLED', 'Отменен'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Низкий'),
        ('NORMAL', 'Обычный'),
        ('HIGH', 'Высокий'),
        ('URGENT', 'Срочный'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID заказа'
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'CLIENT'},
        related_name='orders',
        verbose_name='Клиент'
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.CASCADE,
        verbose_name='Тип транспортного средства'
    )
    tow_truck = models.ForeignKey(
        TowTruck,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Эвакуатор'
    )
    
    # Информация о транспортном средстве
    vehicle_make = models.CharField(
        max_length=100,
        verbose_name='Марка автомобиля'
    )
    vehicle_model = models.CharField(
        max_length=100,
        verbose_name='Модель автомобиля'
    )
    vehicle_year = models.PositiveIntegerField(
        verbose_name='Год выпуска'
    )
    vehicle_color = models.CharField(
        max_length=50,
        verbose_name='Цвет автомобиля'
    )
    license_plate = models.CharField(
        max_length=20,
        verbose_name='Госномер автомобиля'
    )
    
    # Местоположение
    pickup_address = models.TextField(
        verbose_name='Адрес забора'
    )
    pickup_latitude = models.FloatField(
        verbose_name='Широта места забора'
    )
    pickup_longitude = models.FloatField(
        verbose_name='Долгота места забора'
    )
    delivery_address = models.TextField(
        verbose_name='Адрес доставки'
    )
    delivery_latitude = models.FloatField(
        verbose_name='Широта места доставки'
    )
    delivery_longitude = models.FloatField(
        verbose_name='Долгота места доставки'
    )
    
    # Детали заказа
    description = models.TextField(
        blank=True,
        verbose_name='Описание проблемы'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL',
        verbose_name='Приоритет'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Статус'
    )
    
    # Ценообразование
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Предварительная цена'
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Финальная цена'
    )
    
    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    scheduled_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Запланированное время'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения'
    )
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ {self.id} - {self.vehicle_make} {self.vehicle_model}"


class OrderStatusHistory(models.Model):
    """
    История изменений статуса заказа.
    
    Отслеживает все изменения статуса заказа для аудита.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Заказ'
    )
    old_status = models.CharField(
        max_length=15,
        choices=Order.STATUS_CHOICES,
        verbose_name='Предыдущий статус'
    )
    new_status = models.CharField(
        max_length=15,
        choices=Order.STATUS_CHOICES,
        verbose_name='Новый статус'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Изменен пользователем'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время изменения'
    )
    
    class Meta:
        verbose_name = 'История статуса заказа'
        verbose_name_plural = 'История статусов заказов'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.order.id}: {self.old_status} → {self.new_status}"


class Payment(models.Model):
    """
    Модель платежей.
    
    Управляет платежами за услуги эвакуации.
    """
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Ожидает оплаты'),
        ('PROCESSING', 'Обрабатывается'),
        ('COMPLETED', 'Оплачен'),
        ('FAILED', 'Ошибка оплаты'),
        ('REFUNDED', 'Возвращен'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Наличные'),
        ('CARD', 'Банковская карта'),
        ('BANK_TRANSFER', 'Банковский перевод'),
        ('MOBILE_PAYMENT', 'Мобильный платеж'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Заказ'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма'
    )
    payment_method = models.CharField(
        max_length=15,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Способ оплаты'
    )
    status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        verbose_name='Статус оплаты'
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID транзакции'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата оплаты'
    )
    
    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
    
    def __str__(self):
        return f"Платеж {self.id} - {self.amount} руб."


class Rating(models.Model):
    """
    Модель рейтингов и отзывов.
    
    Позволяет клиентам оценивать качество услуг.
    """
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='rating',
        verbose_name='Заказ'
    )
    driver_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка водителя'
    )
    service_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка сервиса'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'
    
    def __str__(self):
        return f"Рейтинг для заказа {self.order.id}"


class Notification(models.Model):
    """
    Модель уведомлений.
    
    Система уведомлений для пользователей.
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('ORDER_CREATED', 'Заказ создан'),
        ('ORDER_ASSIGNED', 'Заказ назначен'),
        ('ORDER_IN_PROGRESS', 'Заказ выполняется'),
        ('ORDER_COMPLETED', 'Заказ завершен'),
        ('PAYMENT_RECEIVED', 'Платеж получен'),
        ('DRIVER_ARRIVED', 'Водитель прибыл'),
        ('GENERAL', 'Общее уведомление'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='Тип уведомления'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    message = models.TextField(
        verbose_name='Сообщение'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    related_order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Связанный заказ'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
