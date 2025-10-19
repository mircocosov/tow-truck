import { useState } from "react";
import { useAuth } from "../AuthContext";
import { parseResponse } from "../api";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface Preset {
  name: string;
  method: HttpMethod;
  path: string;
  body?: object | string;
  description?: string;
}

const presets: Preset[] = [
  {
    name: "Password reset (POST)",
    method: "POST",
    path: "auth/password/reset/",
    body: {
      phone: "+79001234567",
      new_password: "NewStrongPass123!",
      new_password_confirm: "NewStrongPass123!",
    },
    description: "Номер телефона должен существовать в системе.",
  },
  {
    name: "Vehicle types (GET)",
    method: "GET",
    path: "vehicle-types/",
  },
  {
    name: "Tow trucks (GET)",
    method: "GET",
    path: "tow-trucks/",
  },
  {
    name: "Orders list (GET)",
    method: "GET",
    path: "orders/list/",
  },
  {
    name: "Order detail (GET)",
    method: "GET",
    path: "orders/<order_id>/",
    description: "Замените <order_id> на настоящий UUID.",
  },
  {
    name: "Create order (POST, CLIENT)",
    method: "POST",
    path: "orders/",
    body: {
      vehicle_type: 1,
      vehicle_make: "Toyota",
      vehicle_model: "Camry",
      vehicle_year: 2020,
      vehicle_color: "Черный",
      license_plate: "А123ВС777",
      pickup_address: "Москва, Красная площадь, 1",
      pickup_latitude: 55.7539,
      pickup_longitude: 37.6208,
      delivery_address: "Москва, Проспект Мира, 10",
      delivery_latitude: 55.7814,
      delivery_longitude: 37.6339,
      description: "Тестовый заказ",
      priority: "NORMAL",
    },
  },
  {
    name: "Update order status (PATCH, OPERATOR/DRIVER)",
    method: "PATCH",
    path: "orders/<order_id>/update-status/",
    body: { status: "IN_PROGRESS" },
  },
  {
    name: "Dashboard stats (GET)",
    method: "GET",
    path: "dashboard/stats/",
  },
  {
    name: "Create payment (POST)",
    method: "POST",
    path: "orders/<order_id>/payments/",
    body: {
      amount: "3500.00",
      payment_method: "CARD",
      status: "COMPLETED",
      transaction_id: "TEST-123",
    },
  },
  {
    name: "Create rating (POST, CLIENT)",
    method: "POST",
    path: "orders/<order_id>/rating/",
    body: {
      driver_rating: 5,
      service_rating: 5,
      comment: "Отлично! Спасибо.",
    },
  },
  {
    name: "Notifications (GET)",
    method: "GET",
    path: "notifications/",
  },
  {
    name: "Support tickets (GET)",
    method: "GET",
    path: "support/tickets/",
  },
  {
    name: "Create support ticket (POST)",
    method: "POST",
    path: "support/tickets/",
    body: {
      subject: "Нужна помощь",
      description: "Машина не заводится после эвакуации",
      priority: "NORMAL",
    },
  },
  {
    name: "Add support message (POST)",
    method: "POST",
    path: "support/tickets/<ticket_id>/messages/",
    body: {
      body: "Есть новости?",
      is_internal: false,
    },
  },
];

function pretty(value: unknown) {
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return value;
    }
  }
  if (value === undefined) return "";
  return JSON.stringify(value, null, 2);
}

export default function RequestRunner() {
  const { apiFetch } = useAuth();
  const [selectedPreset, setSelectedPreset] = useState<string>("");
  const [method, setMethod] = useState<HttpMethod>("GET");
  const [path, setPath] = useState("vehicle-types/");
  const [body, setBody] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const applyPreset = (name: string) => {
    setSelectedPreset(name);
    const preset = presets.find((item) => item.name === name);
    if (!preset) return;
    setMethod(preset.method);
    setPath(preset.path);
    setBody(
      preset.body
        ? typeof preset.body === "string"
          ? preset.body
          : JSON.stringify(preset.body, null, 2)
        : "",
    );
    setStatus(preset.description ?? "");
    setResponse("");
  };

  const sendRequest = async () => {
    setLoading(true);
    setStatus("Отправляем запрос...");
    setResponse("");

    try {
      if (!path.trim()) {
        setStatus("Укажите путь до эндпоинта.");
        return;
      }

      const init: RequestInit = { method };
      if (!["GET", "DELETE"].includes(method) && body.trim()) {
        init.body = body;
      }

      const response = await apiFetch(path.trim(), init);
      const payload = await parseResponse(response);
      setStatus(`HTTP ${response.status}`);
      setResponse(pretty(payload));
    } catch (error) {
      if (error instanceof Error) {
        setStatus("Ошибка выполнения запроса");
        setResponse(error.message);
      } else {
        setStatus("Неизвестная ошибка");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="request-runner">
      <div className="request-runner__left">
        <label>
          Preset
          <select
            value={selectedPreset}
            onChange={(event) => applyPreset(event.target.value)}
          >
            <option value="" disabled>
              Выберите пресет…
            </option>
            {presets.map((preset) => (
              <option key={preset.name} value={preset.name}>
                {preset.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Method
          <select
            value={method}
            onChange={(event) => setMethod(event.target.value as HttpMethod)}
          >
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="PATCH">PATCH</option>
            <option value="DELETE">DELETE</option>
          </select>
        </label>

        <label>
          Path / URL
          <input
            type="text"
            value={path}
            onChange={(event) => setPath(event.target.value)}
            placeholder="orders/list/"
          />
        </label>

        <label>
          Body (JSON)
          <textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            rows={10}
            placeholder='{"key": "value"}'
          />
        </label>

        <button onClick={sendRequest} disabled={loading}>
          {loading ? "Отправляем..." : "Send request"}
        </button>
        {status && <p className="request-status">{status}</p>}
      </div>

      <div className="request-runner__right">
        <h4>Response</h4>
        <pre className="response-block">
          {response || "Ответ появится после отправки запроса."}
        </pre>
      </div>
    </div>
  );
}
