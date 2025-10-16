# Инструкция по настройке проекта

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных PostgreSQL

**Вариант A: Создание через psql**
```bash
psql -U postgres
CREATE DATABASE "towTruck";
\q
```

**Вариант B: Использование SQL-скрипта**
```bash
psql -U postgres -f create_db.sql
```

### 3. Настройка переменных окружения
```bash
# Скопируйте файл-шаблон
cp env.example .env

# Отредактируйте .env файл с вашими настройками
# Особенно важно указать правильный пароль для PostgreSQL
```

### 4. Применение миграций
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py create_sample_data
```

### 5. Запуск сервера
```bash
python manage.py runserver
```

## Доступные URL после запуска:

- **Swagger UI**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/
- **Django Admin**: http://127.0.0.1:8000/admin/
- **API v1**: http://127.0.0.1:8000/api/v1/

## Тестовые учетные записи:
- **Клиент**: `client1` / `password123`
- **Водитель**: `driver1` / `password123`
- **Оператор**: `operator1` / `password123`

## Важные файлы:

- `.env` - настройки окружения (НЕ коммитится в git)
- `env.example` - шаблон настроек (коммитится в git)
- `.gitignore` - файлы, исключенные из git
- `DATABASE_SETUP.md` - подробная инструкция по настройке БД
- `create_db.sql` - SQL-скрипт для создания БД

## Безопасность:

⚠️ **ВАЖНО**: Никогда не коммитьте файл `.env` в git! Он содержит секретные данные.

✅ **Правильно**: Используйте `env.example` как шаблон для других разработчиков.
