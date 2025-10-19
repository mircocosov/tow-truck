import { useEffect, useMemo, useState } from "react";
import { useAuth } from "./AuthContext";
import RequestRunner from "./components/RequestRunner";
import WebSocketViewer from "./components/WebSocketViewer";
import LocationUpdateForm from "./components/LocationUpdateForm";

export default function Dashboard() {
  const { user, logout, accessToken, refreshToken, updateTokens } = useAuth();
  const [showTokens, setShowTokens] = useState(false);
  const [accessDraft, setAccessDraft] = useState(accessToken ?? "");
  const [refreshDraft, setRefreshDraft] = useState(refreshToken ?? "");

  useEffect(() => {
    setAccessDraft(accessToken ?? "");
  }, [accessToken]);

  useEffect(() => {
    setRefreshDraft(refreshToken ?? "");
  }, [refreshToken]);

  const userInfo = useMemo(() => {
    if (!user) return "гость";
    const role = user.user_type ?? "unknown";
    const name = user.first_name || user.last_name
      ? `${user.first_name ?? ""} ${user.last_name ?? ""}`.trim()
      : user.phone ?? user.email ?? "user";
    return `${name} (${role})`;
  }, [user]);

  const applyTokens = () => {
    updateTokens({
      accessToken: accessDraft || null,
      refreshToken: refreshDraft || null,
    });
  };

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1>Tow-Truck Playground</h1>
          <p>Текущий пользователь: {userInfo}</p>
        </div>
        <button onClick={logout}>Выйти</button>
      </header>

      <section className="dashboard__section">
        <h2>JWT токены</h2>
        <p>
          После логина токены сохраняются в localStorage. Можно вручную подставить
          значения (например, чтобы посмотреть систему глазами оператора).
        </p>
        <button onClick={() => setShowTokens((prev) => !prev)}>
          {showTokens ? "Скрыть токены" : "Показать/изменить токены"}
        </button>
        {showTokens && (
          <div className="token-editor">
            <label>
              Access token
              <textarea
                value={accessDraft}
                onChange={(event) => setAccessDraft(event.target.value)}
              />
            </label>
            <label>
              Refresh token
              <textarea
                value={refreshDraft}
                onChange={(event) => setRefreshDraft(event.target.value)}
              />
            </label>
            <button onClick={applyTokens}>Применить</button>
          </div>
        )}
        <details style={{ marginTop: "12px" }}>
          <summary>Подсказки</summary>
          <ul>
            <li>client1 / password123 → +79001234567</li>
            <li>driver1 / password123 → +79001234568</li>
            <li>operator1 / password123 → +79001234569 (для тестов через токен)</li>
          </ul>
        </details>
      </section>

      <section className="dashboard__section">
        <h2>Live-трекинг</h2>
        <p>
          Выполните вход под водителем, отправьте координаты — и подписка
          по WebSocket получит обновление.
        </p>
        <div className="dashboard__grid">
          <LocationUpdateForm />
          <WebSocketViewer />
        </div>
      </section>

      <section className="dashboard__section">
        <h2>REST-песочница</h2>
        <p>
          Пресеты покрывают основные эндпоинты (заказы, статусы, платежи, тикеты, сброс пароля и т.п.).
          Можно менять URL/тело и отправлять запросы.
        </p>
        <RequestRunner />
      </section>
    </div>
  );
}
