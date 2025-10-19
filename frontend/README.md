# Tow-Truck Frontend Playground

A small React/Vite app for manually testing every backend endpoint.

## Launch

```bash
cd frontend
npm install
npm run dev
```

By default the app expects API at `http://127.0.0.1:8000/api/v1/` and WebSocket at `ws://127.0.0.1:8000/`. Override them with environment variables if needed:

```
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1/
VITE_WS_BASE_URL=ws://127.0.0.1:8000/
```

## Features

- Login/registration with JWT persistence in localStorage.
- Token editor (useful to impersonate driver/client without logging in again).
- **Live tracking** section:
  - REST form for drivers to send coordinates.
  - WebSocket viewer to follow order/tow truck updates in real time.
- **REST sandbox** with presets for orders, payments, ratings, notifications and support tickets.
- Password reset form (sets a new password by phone number).

## Useful test accounts

- `client1 / password123`
- `driver1 / password123`
- `operator1 / password123`

These accounts are created by the management command `python manage.py create_sample_data` on the backend.
