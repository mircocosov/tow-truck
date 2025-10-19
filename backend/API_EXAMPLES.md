# Примеры использования API v1

## Базовый URL
```
http://127.0.0.1:8000/api/v1/
```

## Аутентификация с JWT токенами

### 1. Регистрация пользователя
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "phone": "+79001234567",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Иван",
    "last_name": "Петров",
    "user_type": "CLIENT"
  }'
```

**Ответ:**
```json
{
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "phone": "+79001234567",
    "user_type": "CLIENT",
    "is_verified": false
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Логин пользователя
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "client1",
    "password": "password123"
  }'
```

**Ответ:**
```json
{
  "user": {
    "id": 1,
    "username": "client1",
    "email": "client1@example.com",
    "user_type": "CLIENT"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Обновление токена
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Работа с заказами

### 4. Создание заказа (требует аутентификации)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -d '{
    "vehicle_type": 1,
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "vehicle_year": 2020,
    "vehicle_color": "Белый",
    "license_plate": "А123БВ777",
    "pickup_address": "ул. Ленина, 1, Москва",
    "pickup_latitude": 55.7558,
    "pickup_longitude": 37.6176,
    "delivery_address": "ул. Арбат, 10, Москва",
    "delivery_latitude": 55.7522,
    "delivery_longitude": 37.5911,
    "description": "Не заводится двигатель",
    "priority": "NORMAL"
  }'
```

### 5. Получение списка заказов
```bash
curl -X GET http://127.0.0.1:8000/api/v1/orders/list/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 6. Получение деталей заказа
```bash
curl -X GET http://127.0.0.1:8000/api/v1/orders/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Работа с эвакуаторами

### 7. Получение списка доступных эвакуаторов
```bash
curl -X GET http://127.0.0.1:8000/api/v1/tow-trucks/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 8. Фильтрация эвакуаторов по типу ТС
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/tow-trucks/?vehicle_type=1" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Работа с уведомлениями

### 9. Получение уведомлений
```bash
curl -X GET http://127.0.0.1:8000/api/v1/notifications/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 10. Отметка уведомления как прочитанного
```bash
curl -X POST http://127.0.0.1:8000/api/v1/notifications/1/read/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Обновление местоположения (для водителей)

### 11. Обновление местоположения водителя
```bash
curl -X POST http://127.0.0.1:8000/api/v1/location/update/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -d '{
    "latitude": 55.7558,
    "longitude": 37.6176
  }'
```

## JavaScript примеры

### Использование в мобильном приложении
```javascript
// Базовый класс для работы с API
class TowTruckAPI {
  constructor(baseURL = 'http://127.0.0.1:8000/api/v1') {
    this.baseURL = baseURL;
    this.accessToken = null;
    this.refreshToken = null;
  }

  // Логин и сохранение токенов
  async login(username, password) {
    const response = await fetch(`${this.baseURL}/auth/login/`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password})
    });
    
    const data = await response.json();
    this.accessToken = data.access;
    this.refreshToken = data.refresh;
    return data;
  }

  // Обновление токена
  async refreshAccessToken() {
    const response = await fetch(`${this.baseURL}/auth/token/refresh/`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({refresh: this.refreshToken})
    });
    
    const data = await response.json();
    this.accessToken = data.access;
    return data.access;
  }

  // Выполнение запроса с автоматическим обновлением токена
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    let response = await fetch(url, {...options, headers});

    // Если токен истек, обновляем и повторяем запрос
    if (response.status === 401 && this.refreshToken) {
      await this.refreshAccessToken();
      headers['Authorization'] = `Bearer ${this.accessToken}`;
      response = await fetch(url, {...options, headers});
    }

    return response;
  }

  // Создание заказа
  async createOrder(orderData) {
    const response = await this.request('/orders/', {
      method: 'POST',
      body: JSON.stringify(orderData)
    });
    return response.json();
  }

  // Получение списка заказов
  async getOrders() {
    const response = await this.request('/orders/list/');
    return response.json();
  }
}

// Использование
const api = new TowTruckAPI();

// Логин
await api.login('client1', 'password123');

// Создание заказа
const order = await api.createOrder({
  vehicle_type: 1,
  vehicle_make: 'Toyota',
  vehicle_model: 'Camry',
  vehicle_year: 2020,
  vehicle_color: 'Белый',
  license_plate: 'А123БВ777',
  pickup_address: 'ул. Ленина, 1, Москва',
  pickup_latitude: 55.7558,
  pickup_longitude: 37.6176,
  delivery_address: 'ул. Арбат, 10, Москва',
  delivery_latitude: 55.7522,
  delivery_longitude: 37.5911,
  description: 'Не заводится двигатель',
  priority: 'NORMAL'
});

// Получение заказов
const orders = await api.getOrders();
```

## Тестирование через Swagger UI

1. Откройте http://127.0.0.1:8000/swagger/
2. Нажмите "Authorize" и введите: `Bearer <ваш_access_token>`
3. Тестируйте endpoints прямо в браузере

## Коды ошибок

- **400** - Неверные данные запроса
- **401** - Не авторизован (токен истек или неверный)
- **403** - Доступ запрещен
- **404** - Ресурс не найден
- **500** - Внутренняя ошибка сервера


## Real-time Location WebSocket

### JavaScript example

```javascript
const orderId = '550e8400-e29b-41d4-a716-446655440000';
const socket = new WebSocket(`ws://127.0.0.1:8000/ws/orders/${orderId}/location/?token=${accessToken}`);

socket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  console.log('Live location update', payload.location);
};
```

### Sample payload

```json
{
  "type": "update",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "location": {
    "tow_truck_id": "2c9d4f2a-2f1e-4c66-bf4f-06d22aa6ef73",
    "latitude": 55.7558,
    "longitude": 37.6176,
    "updated_at": "2025-10-18T23:51:04.123456+03:00"
  }
}
```

## Support Tickets

### Create a ticket

```bash
curl -X POST http://127.0.0.1:8000/api/v1/support/tickets/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "subject": "Need help with my order",
    "description": "Driver is delayed by 30 minutes",
    "priority": "HIGH"
  }'
```

### Post a message to a ticket

```bash
curl -X POST http://127.0.0.1:8000/api/v1/support/tickets/${TICKET_ID}/messages/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
    "body": "Can you provide an ETA?"
  }'
```
### ����� ������

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+79001234567",
    "new_password": "NewStrongPass123!",
    "new_password_confirm": "NewStrongPass123!"
  }'
```
