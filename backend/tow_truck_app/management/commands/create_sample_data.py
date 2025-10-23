"""
Management command that seeds the database with demo data.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from tow_truck_app.models import (
    ClientVehicle,
    NotificationType,
    Order,
    PaymentMethod,
    PaymentStatus,
    TicketStatus,
    TowTruck,
    User,
    UserType,
    VehicleType,
)


class Command(BaseCommand):
    help = "Populate the database with a minimal set of reference data and demo accounts."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Creating reference data…")

        user_types = [
            ("CLIENT", "Клиент"),
            ("DRIVER", "Водитель"),
            ("OPERATOR", "Оператор"),
        ]
        for code, name in user_types:
            UserType.objects.update_or_create(code=code, defaults={"name": name})

        payment_methods = [
            ("CASH", "Наличные"),
            ("CARD", "Банковская карта"),
            ("BANK_TRANSFER", "Банковский перевод"),
            ("MOBILE_PAYMENT", "Мобильный платёж"),
        ]
        for code, name in payment_methods:
            PaymentMethod.objects.update_or_create(code=code, defaults={"name": name})

        payment_statuses = [
            ("PENDING", "Ожидает обработки"),
            ("PROCESSING", "В обработке"),
            ("COMPLETED", "Завершён"),
            ("FAILED", "Не удалось"),
            ("REFUNDED", "Возвращён"),
        ]
        for code, name in payment_statuses:
            PaymentStatus.objects.update_or_create(code=code, defaults={"name": name})

        notification_types = [
            ("ORDER_CREATED", "Заказ создан"),
            ("ORDER_CONFIRMED", "Заказ подтверждён"),
            ("ORDER_ASSIGNED", "Назначен эвакуатор"),
            ("ORDER_IN_PROGRESS", "Заказ в работе"),
            ("ORDER_COMPLETED", "Заказ выполнен"),
            ("ORDER_CANCELLED", "Заказ отменён"),
            ("PAYMENT_RECEIVED", "Платёж получен"),
            ("DRIVER_ARRIVED", "Водитель прибыл"),
            ("GENERAL", "Общее уведомление"),
        ]
        for code, name in notification_types:
            NotificationType.objects.update_or_create(code=code, defaults={"name": name})

        ticket_statuses = [
            ("OPEN", "Открыт"),
            ("IN_PROGRESS", "В работе"),
            ("RESOLVED", "Решён"),
            ("CLOSED", "Закрыт"),
        ]
        for code, name in ticket_statuses:
            TicketStatus.objects.update_or_create(code=code, defaults={"name": name})

        self.stdout.write("Creating vehicle types…")
        vehicle_types = [
            {
                "name": "Легковой автомобиль",
                "description": "Городские автомобили до 3.5 тонн.",
                "max_weight": 3.5,
                "base_price": 2500.00,
                "per_km_rate": 120.00,
            },
            {
                "name": "Внедорожник/Кроссовер",
                "description": "Повышенная проходимость, до 4.5 тонн.",
                "max_weight": 4.5,
                "base_price": 3000.00,
                "per_km_rate": 150.00,
            },
            {
                "name": "Лёгкий грузовик",
                "description": "Коммерческий транспорт до 6 тонн.",
                "max_weight": 6.0,
                "base_price": 4000.00,
                "per_km_rate": 180.00,
            },
        ]
        created_vehicle_types = []
        for payload in vehicle_types:
            vt, _ = VehicleType.objects.update_or_create(name=payload["name"], defaults=payload)
            created_vehicle_types.append(vt)

        self.stdout.write("Creating demo users…")
        demo_users = [
            {
                "username": "client1",
                "email": "client1@example.com",
                "phone": "+79001234567",
                "first_name": "Ирина",
                "last_name": "Клиентова",
                "user_type_id": "CLIENT",
            },
            {
                "username": "driver1",
                "email": "driver1@example.com",
                "phone": "+79001234568",
                "first_name": "Владимир",
                "last_name": "Водитель",
                "user_type_id": "DRIVER",
            },
            {
                "username": "operator1",
                "email": "operator1@example.com",
                "phone": "+79001234569",
                "first_name": "Ольга",
                "last_name": "Операторова",
                "user_type_id": "OPERATOR",
            },
        ]

        for payload in demo_users:
            user, created = User.objects.update_or_create(
                username=payload["username"],
                defaults={k: v for k, v in payload.items() if k != "user_type_id"},
            )
            if created:
                user.user_type_id = payload["user_type_id"]
                user.set_password("password123")
                user.save()

        client = User.objects.get(username="client1")
        driver = User.objects.get(username="driver1")

        self.stdout.write("Creating client vehicle and tow truck…")
        client_vehicle, _ = ClientVehicle.objects.update_or_create(
            license_plate="А123ВС777",
            defaults={
                "owner": client,
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "color": "Белый",
            },
        )

        tow_truck, _ = TowTruck.objects.update_or_create(
            license_plate="Э001КХ199",
            defaults={
                "model": "КАМАЗ-Эвакуатор",
                "capacity": 5.0,
                "driver": driver,
                "status": "AVAILABLE",
            },
        )
        tow_truck.vehicle_types.set(created_vehicle_types)

        if not Order.objects.filter(client=client).exists():
            order = Order.objects.create(
                client=client,
                vehicle=client_vehicle,
                vehicle_type=created_vehicle_types[0],
                pickup_address="Москва, ул. Ленина, 1",
                pickup_latitude=55.7522,
                pickup_longitude=37.6156,
                delivery_address="Москва, ул. Тверская, 7",
                delivery_latitude=55.7652,
                delivery_longitude=37.6051,
                description="Не заводится двигатель",
                estimated_price=5500,
            )
            self.stdout.write(f"Создан демонстрационный заказ {order.id}")

        self.stdout.write(self.style.SUCCESS("Демо-данные успешно загружены."))
        self.stdout.write("Аккаунты:\n - client1 / password123\n - driver1 / password123\n - operator1 / password123")
