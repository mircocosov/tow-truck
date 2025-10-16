-- Создание базы данных для системы эвакуатора
-- Выполните этот скрипт в PostgreSQL для создания базы данных

-- Создание базы данных
CREATE DATABASE "towTruck" 
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'ru_RU.UTF-8'
    LC_CTYPE = 'ru_RU.UTF-8'
    TEMPLATE = template0;

-- Комментарий к базе данных
COMMENT ON DATABASE "towTruck" IS 'База данных для системы эвакуатора';

-- Подключение к созданной базе данных
\c "towTruck";

-- Создание расширений (если необходимо)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Информация о создании
SELECT 'База данных towTruck успешно создана!' as status;
