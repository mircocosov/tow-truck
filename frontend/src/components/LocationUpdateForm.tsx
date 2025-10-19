import { useState } from "react";
import { useAuth } from "../AuthContext";
import { parseResponse } from "../api";

export default function LocationUpdateForm() {
  const { apiFetch } = useAuth();
  const [latitude, setLatitude] = useState(55.7558);
  const [longitude, setLongitude] = useState(37.6173);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const response = await apiFetch("location/update/", {
        method: "POST",
        body: JSON.stringify({ latitude, longitude }),
      });
      const payload = await parseResponse(response);
      if (response.ok) {
        setMessage(
          typeof payload === "string"
            ? payload
            : JSON.stringify(payload, null, 2),
        );
      } else {
        setMessage(
          typeof payload === "string"
            ? payload
            : JSON.stringify(payload, null, 2),
        );
      }
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Неизвестная ошибка при обновлении координат.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Driver: отправить координаты</h3>
      <p>
        Авторизуйтесь под водителем, укажите точку и отправьте — WebSocket
        подписчики увидят обновление.
      </p>
      <form onSubmit={handleSubmit} className="form-grid">
        <label>
          Latitude
          <input
            type="number"
            step="0.0001"
            value={latitude}
            onChange={(event) => setLatitude(Number(event.target.value))}
          />
        </label>
        <label>
          Longitude
          <input
            type="number"
            step="0.0001"
            value={longitude}
            onChange={(event) => setLongitude(Number(event.target.value))}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Отправляем..." : "Send location"}
        </button>
      </form>
      {message && (
        <pre className="response-block" style={{ maxHeight: 220 }}>
          {message}
        </pre>
      )}
    </div>
  );
}
