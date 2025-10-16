# Настройка базы данных PostgreSQL

## Требования

Для работы проекта необходима установленная PostgreSQL версии 12 или выше.

## Установка PostgreSQL

### Windows
1. Скачайте PostgreSQL с официального сайта: https://www.postgresql.org/download/windows/
2. Установите с настройками по умолчанию
3. Запомните пароль для пользователя `postgres`

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### macOS
```bash
brew install postgresql
brew services start postgresql
```

## Создание базы данных

1. Подключитесь к PostgreSQL:
```bash
psql -U postgres
```

2. Создайте базу данных:
```sql
CREATE DATABASE "towTruck";
```

3. (Опционально) Создайте отдельного пользователя:
```sql
CREATE USER towtruck_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE "towTruck" TO towtruck_user;
```

## Настройка переменных окружения

1. Скопируйте файл `env.example` в `.env`:
```bash
cp env.example .env
```

2. Отредактируйте `.env` файл с вашими настройками:
```env
# База данных PostgreSQL
DB_NAME=towTruck
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

## Запуск миграций

После настройки базы данных выполните:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py create_sample_data
```

## Проверка подключения

Для проверки подключения к базе данных:

```bash
python manage.py dbshell
```

Если подключение успешно, вы увидите приглашение PostgreSQL.
