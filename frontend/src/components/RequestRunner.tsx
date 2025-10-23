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
    description: "Смена пароля по номеру телефона",
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
    description: "<order_id> необходимо заменить на реальный UUID заказа",
  },
  {
    name: "Create order (POST, CLIENT)",
    method: "POST",
    path: "orders/",
    body: {
      vehicle: 1,
      vehicle_type: 1,
      pickup_address: "Москва, Тверская, 1",
      pickup_latitude: 55.7539,
      pickup_longitude: 37.6208,
      delivery_address: "Москва, Варшавское шоссе, 170",
      delivery_latitude: 55.6364,
      delivery_longitude: 37.6567,
      description: "Блокировка колес",
      priority: "NORMAL",
    },
  },
  {
    name: "Update order status (PATCH)",
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
      comment: "Быстро и аккуратно",
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
      subject: "Не работает отслеживание",
      description: "После обновления клиентской версии не видно эвакуатор на карте",
      priority: "NORMAL",
    },
  },
];

function pretty(data: unknown) {
  if (typeof data === "string") {
    return data;
  }
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
}

export default function RequestRunner() {
  const { apiFetch } = useAuth();
  const [selectedPreset, setSelectedPreset] = useState<string>("");
  const [method, setMethod] = useState<HttpMethod>("GET");
  const [path, setPath] = useState("vehicle-types/");
  const [body, setBody] = useState<string>("");
  const [responseText, setResponseText] = useState<string>("");
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
    setResponseText("");
  };

  const sendRequest = async () => {
    if (!path.trim()) {
      setStatus("Укажите путь или URL запроса");
      return;
    }

    setLoading(true);
    setStatus("Выполняем запрос...");
    setResponseText("");

    try {
      const init: RequestInit & { method?: HttpMethod } = { method };
      if (!["GET", "DELETE"].includes(method) && body.trim()) {
        init.body = body;
      }

      const response = await apiFetch(path.trim(), init);
      const payload = await parseResponse(response);
      setStatus(`HTTP ${response.status}`);
      setResponseText(pretty(payload));
    } catch (error) {
      if (error instanceof Error) {
        setStatus("Ошибка выполнения запроса");
        setResponseText(error.message);
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
              Выберите пример запроса
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
          {loading ? "Выполняем..." : "Send request"}
        </button>
        {status && <p className="request-status">{status}</p>}
      </div>

      <div className="request-runner__right">
        <h4>Response</h4>
        <pre className="response-block">
          {responseText || "Ответ сервера появится здесь."}
        </pre>
      </div>
    </div>
  );
}
