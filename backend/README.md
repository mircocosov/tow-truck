# Система эвакуатора - Backend

Backend API для мобильного приложения системы эвакуатора, разработанный на Django REST Framework.

## Описание

Система эвакуатора предоставляет API для управления заказами на эвакуацию транспортных средств. Поддерживает три типа пользователей:
- **Клиенты** - заказывают услуги эвакуации
- **Водители** - выполняют заказы на эвакуацию
- **Операторы** - управляют заказами и назначают водителей

## Основные функции

- Регистрация и аутентификация пользователей
- Управление заказами на эвакуацию
- Отслеживание местоположения эвакуаторов
- Система платежей
- Рейтинги и отзывы
- Уведомления в реальном времени
- Административная панель

## Технологии

- **Django 4.2** - веб-фреймворк
- **Django REST Framework** - API
- **SQLite** - база данных (по умолчанию)
- **PostgreSQL** - для продакшена (опционально)
- **Token Authentication** - аутентификация
- **CORS** - для работы с мобильными приложениями

## Установка и запуск

### 1. Клонирование и настройка окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка базы данных

**PostgreSQL (рекомендуется):**

1. Установите PostgreSQL и создайте базу данных:
```sql
CREATE DATABASE "towTruck";
```

2. Скопируйте файл настроек:
```bash
cp env.example .env
```

3. Отредактируйте `.env` файл с настройками вашей базы данных:
```env
DB_NAME=towTruck
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

4. Выполните миграции:
```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Создание тестовых данных (опционально)
python manage.py create_sample_data
```

**Альтернативно SQLite (для разработки):**
Если хотите использовать SQLite, измените в `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 3. Запуск сервера

```bash
python manage.py runserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000/

## API Endpoints

### Аутентификация
- `POST /api/v1/auth/register/` - регистрация пользователя
- `POST /api/v1/auth/login/` - вход в систему
- `POST /api/v1/auth/token/refresh/` - обновление токена
- `GET /api/v1/auth/profile/` - профиль пользователя

### Заказы
- `POST /api/v1/orders/` - создание заказа
- `GET /api/v1/orders/list/` - список заказов
- `GET /api/v1/orders/{id}/` - детали заказа
- `PATCH /api/v1/orders/{id}/update-status/` - обновление статуса

### Эвакуаторы
- `GET /api/v1/tow-trucks/` - список доступных эвакуаторов

### Уведомления
- `GET /api/v1/notifications/` - список уведомлений
- `POST /api/v1/notifications/{id}/read/` - отметить как прочитанное

### Местоположение
- `POST /api/v1/location/update/` - обновление местоположения водителя

## Структура проекта

```
backend/
├── backend/                 # Основные настройки Django
│   ├── settings.py         # Настройки проекта
│   ├── urls.py            # Главные URL-маршруты
│   └── wsgi.py            # WSGI конфигурация
├── tow_truck_app/         # Основное приложение
│   ├── models.py          # Модели данных
│   ├── views.py           # API представления
│   ├── serializers.py     # Сериализаторы
│   ├── urls.py           # URL-маршруты приложения
│   ├── admin.py          # Административная панель
│   └── management/       # Пользовательские команды
├── logs/                 # Папка для логов
├── media/               # Медиа файлы
├── static/              # Статические файлы
├── requirements.txt     # Зависимости Python
└── manage.py           # Управление Django
```

## Модели данных

### User
Расширенная модель пользователя Django с поддержкой типов (клиент, водитель, оператор).

### Order
Основная модель заказа на эвакуацию с полной информацией о транспортном средстве, местоположении и статусе.

### TowTruck
Модель эвакуатора с информацией о водителе, грузоподъемности и текущем местоположении.

### VehicleType
Типы транспортных средств с базовыми ценами.

### Payment
Система платежей за услуги эвакуации.

### Rating
Рейтинги и отзывы клиентов.

### Notification
Система уведомлений для пользователей.

## Административная панель

Доступна по адресу: http://127.0.0.1:8000/admin/

Включает полное управление всеми моделями системы с удобным интерфейсом для операторов.

## Тестовые данные

Для создания тестовых данных используйте команду:
```bash
python manage.py create_sample_data
```

Создаются:
- Типы транспортных средств
- Тестовые пользователи (клиент, водитель, оператор)
- Эвакуаторы
- Примеры заказов

## Безопасность

- Token-based аутентификация
- CORS настройки для мобильных приложений
- Валидация данных на уровне сериализаторов
- Права доступа на основе типа пользователя

## Развертывание

### Переменные окружения

Скопируйте файл `env.example` в `.env` и настройте переменные:

```env
# Django настройки
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# База данных PostgreSQL
DB_NAME=towTruck
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Email настройки
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Redis (для Celery)
REDIS_URL=redis://localhost:6379/0

# CORS настройки
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://your-frontend-domain.com
```

### Продакшен настройки

Для продакшена рекомендуется:
1. Использовать PostgreSQL вместо SQLite
2. Настроить статические файлы
3. Использовать Redis для кэширования
4. Настроить логирование
5. Использовать HTTPS

## Разработка

### Добавление новых функций

1. Создайте модели в `models.py`
2. Создайте миграции: `python manage.py makemigrations`
3. Примените миграции: `python manage.py migrate`
4. Добавьте сериализаторы в `serializers.py`
5. Создайте представления в `views.py`
6. Добавьте URL-маршруты в `urls.py`
7. Настройте админ-панель в `admin.py`

### Тестирование

```bash
# Запуск тестов
python manage.py test

# Создание покрытия тестами
coverage run --source='.' manage.py test
coverage report
```

## Поддержка

Для вопросов и предложений создавайте issues в репозитории проекта.


## Real-time Tracking

- WebSocket endpoint for orders: `ws://<host>/ws/orders/<order_id>/location/`
- WebSocket endpoint for tow trucks: `ws://<host>/ws/tow-trucks/<tow_truck_id>/location/`
- Authenticate with an access token: append `?token=<JWT_ACCESS_TOKEN>` to the URL or open the socket from an authenticated session.
- Messages are JSON payloads with the `location`, `order_id` or `tow_truck_id`, and an `updated_at` timestamp.
- Drivers must regularly call `POST /api/v1/location/update/` to publish fresh coordinates.

## Support Tickets API

- List or create tickets: `GET|POST /api/v1/support/tickets/`
- Ticket details / updates: `GET|PATCH /api/v1/support/tickets/<ticket_id>/`
- Conversation messages: `GET|POST /api/v1/support/tickets/<ticket_id>/messages/`
- Initial ticket creation automatically records the first message using the description body.
- Operators can assign tickets, add internal notes, and change status to `IN_PROGRESS`, `RESOLVED`, or `CLOSED`.


### Аутентификация

- Вход выполняется по номеру телефона и паролю (например, `client1` → `+79001234567`).
- Для восстановления пароля используйте POST `/api/v1/auth/password/reset/` c номером телефона и новым паролем.