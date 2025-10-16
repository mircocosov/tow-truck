"""
Команда Django для создания тестовых данных.

Создает базовые данные для тестирования системы эвакуатора.
"""

from django.core.management.base import BaseCommand
from tow_truck_app.models import User, VehicleType, TowTruck, Order


class Command(BaseCommand):
    help = 'Создает тестовые данные для системы эвакуатора'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Создаем типы транспортных средств
        vehicle_types_data = [
            {
                'name': 'Легковой автомобиль',
                'description': 'Автомобили массой до 3.5 тонн',
                'max_weight': 3.5,
                'base_price': 2500.00
            },
            {
                'name': 'Внедорожник/Кроссовер',
                'description': 'SUV и кроссоверы массой до 4.5 тонн',
                'max_weight': 4.5,
                'base_price': 3000.00
            },
            {
                'name': 'Микроавтобус',
                'description': 'Микроавтобусы массой до 6 тонн',
                'max_weight': 6.0,
                'base_price': 4000.00
            },
            {
                'name': 'Грузовой автомобиль',
                'description': 'Грузовые автомобили массой до 10 тонн',
                'max_weight': 10.0,
                'base_price': 6000.00
            }
        ]

        for vt_data in vehicle_types_data:
            vehicle_type, created = VehicleType.objects.get_or_create(
                name=vt_data['name'],
                defaults=vt_data
            )
            if created:
                self.stdout.write(f'Создан тип ТС: {vehicle_type.name}')

        # Создаем тестовых пользователей
        users_data = [
            {
                'username': 'client1',
                'email': 'client1@example.com',
                'phone': '+79001234567',
                'user_type': 'CLIENT',
                'first_name': 'Иван',
                'last_name': 'Петров'
            },
            {
                'username': 'driver1',
                'email': 'driver1@example.com',
                'phone': '+79001234568',
                'user_type': 'DRIVER',
                'first_name': 'Сергей',
                'last_name': 'Иванов'
            },
            {
                'username': 'operator1',
                'email': 'operator1@example.com',
                'phone': '+79001234569',
                'user_type': 'OPERATOR',
                'first_name': 'Анна',
                'last_name': 'Сидорова'
            }
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Создан пользователь: {user.username}')

        # Создаем эвакуаторы
        driver = User.objects.get(username='driver1')
        light_vehicle_type = VehicleType.objects.get(name='Легковой автомобиль')
        suv_vehicle_type = VehicleType.objects.get(name='Внедорожник/Кроссовер')

        tow_trucks_data = [
            {
                'license_plate': 'А123БВ777',
                'model': 'КАМАЗ-5320',
                'capacity': 5.0,
                'driver': driver,
                'status': 'AVAILABLE'
            }
        ]

        for tt_data in tow_trucks_data:
            tow_truck, created = TowTruck.objects.get_or_create(
                license_plate=tt_data['license_plate'],
                defaults=tt_data
            )
            if created:
                tow_truck.vehicle_types.add(light_vehicle_type, suv_vehicle_type)
                self.stdout.write(f'Создан эвакуатор: {tow_truck.license_plate}')

        self.stdout.write(
            self.style.SUCCESS('Тестовые данные успешно созданы!')
        )
        self.stdout.write('\nТестовые учетные записи:')
        self.stdout.write('Клиент: client1 / password123')
        self.stdout.write('Водитель: driver1 / password123')
        self.stdout.write('Оператор: operator1 / password123')
