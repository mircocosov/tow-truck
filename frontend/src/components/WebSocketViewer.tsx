import { useEffect, useRef, useState } from "react";
import { useAuth } from "../AuthContext";
import { WS_BASE } from "../api";

type SubscriptionType = "order" | "tow_truck";

export default function WebSocketViewer() {
  const { accessToken } = useAuth();
  const [subscriptionType, setSubscriptionType] = useState<SubscriptionType>("order");
  const [identifier, setIdentifier] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [status, setStatus] = useState("Закрыто");
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, []);

  const connect = () => {
    if (!identifier.trim()) {
      setStatus("Укажите идентификатор заказа или эвакуатора.");
      return;
    }
    if (!accessToken) {
      setStatus("Нужен access token (авторизуйтесь или подставьте вручную).");
      return;
    }

    const path =
      subscriptionType === "order"
        ? `ws/orders/${identifier}/location/`
        : `ws/tow-trucks/${identifier}/location/`;
    const url = `${WS_BASE}${path}?token=${encodeURIComponent(accessToken)}`;

    socketRef.current?.close();
    const socket = new WebSocket(url);
    socketRef.current = socket;
    setMessages([]);
    setStatus("Подключение...");

    socket.onopen = () => setStatus("Подключено");
    socket.onclose = () => setStatus("Закрыто");
    socket.onerror = () => setStatus("Ошибка соединения");
    socket.onmessage = (event) => {
      setMessages((prev) => [
        `${new Date().toLocaleTimeString()}: ${event.data}`,
        ...prev,
      ]);
    };
  };

  const disconnect = () => {
    socketRef.current?.close();
    socketRef.current = null;
    setStatus("Закрыто");
  };

  return (
    <div className="card">
      <h3>WebSocket-подписка</h3>
      <div className="form-grid">
        <label>
          Тип подписки
          <select
            value={subscriptionType}
            onChange={(event) =>
              setSubscriptionType(event.target.value as SubscriptionType)
            }
          >
            <option value="order">По заказу (order ID)</option>
            <option value="tow_truck">По эвакуатору (tow_truck ID)</option>
          </select>
        </label>
        <label>
          ID
          <input
            type="text"
            placeholder="UUID"
            value={identifier}
            onChange={(event) => setIdentifier(event.target.value)}
          />
        </label>
      </div>
      <div className="button-row">
        <button onClick={connect}>Connect</button>
        <button onClick={disconnect}>Disconnect</button>
        <span className="ws-status">{status}</span>
      </div>
      <div className="response-block" style={{ maxHeight: 220 }}>
        {messages.length === 0
          ? "Сообщения появятся после подключения."
          : messages.map((item, index) => <div key={index}>{item}</div>)}
      </div>
    </div>
  );
}
