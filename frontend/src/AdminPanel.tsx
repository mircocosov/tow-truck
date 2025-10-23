import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { createApiError, parseResponse } from "./api";

interface VehicleType {
  id: number;
  name: string;
  description: string;
  base_price: string;
  per_km_rate: string;
}

interface EditState {
  base_price: string;
  per_km_rate: string;
}

export default function AdminPanel() {
  const { user, logout, apiFetch } = useAuth();
  const [vehicleTypes, setVehicleTypes] = useState<VehicleType[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [edits, setEdits] = useState<Record<number, EditState>>({});

  const isOperator = user?.user_type === "OPERATOR";

  useEffect(() => {
    const loadTypes = async () => {
      setLoading(true);
      setMessage(null);
      try {
        const response = await apiFetch("vehicle-types/");
        const data = await parseResponse(response);
        if (!response.ok) {
          throw createApiError("Не удалось загрузить список тарифов", response.status, data);
        }
        const list = data as VehicleType[];
        setVehicleTypes(list);
        const next: Record<number, EditState> = {};
        list.forEach((item) => {
          next[item.id] = {
            base_price: item.base_price ?? "0",
            per_km_rate: item.per_km_rate ?? "0",
          };
        });
        setEdits(next);
      } catch (error) {
        if (error instanceof Error) {
          setMessage(error.message);
        } else {
          setMessage("Произошла ошибка при загрузке тарифов");
        }
      } finally {
        setLoading(false);
      }
    };

    loadTypes();
  }, [apiFetch]);

  const handleChange = (id: number, event: ChangeEvent<HTMLInputElement>) => {
    setEdits((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [event.target.name]: event.target.value,
      },
    }));
  };

  const handleSubmit = async (id: number, event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!edits[id]) return;

    setSavingId(id);
    setMessage(null);

    try {
      const response = await apiFetch(`vehicle-types/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(edits[id]),
      });
      const data = await parseResponse(response);
      if (!response.ok) {
        throw createApiError("Не удалось сохранить тариф", response.status, data);
      }
      const updated = data as VehicleType;
      setVehicleTypes((current) =>
        current.map((item) => (item.id === id ? updated : item)),
      );
      setEdits((prev) => ({
        ...prev,
        [id]: {
          base_price: updated.base_price ?? prev[id]?.base_price ?? "0",
          per_km_rate: updated.per_km_rate ?? prev[id]?.per_km_rate ?? "0",
        },
      }));
      setMessage("Изменения сохранены");
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Произошла ошибка при сохранении");
      }
    } finally {
      setSavingId(null);
    }
  };

  if (!isOperator) {
    return (
      <div className="app-shell">
        <header className="top-bar">
          <div className="top-bar__brand">
            <h1>Сервис эвакуации</h1>
            <p>Для управления тарифами необходим аккаунт оператора.</p>
          </div>
          <nav className="top-bar__actions">
            <Link to="/" className="nav-link">
              На главную
            </Link>
            <button onClick={logout} className="nav-button">
              Выйти
            </button>
          </nav>
        </header>
        <main className="admin-body">
          <p>
            Обратитесь к администратору за правами оператора, если хотите менять тарифы через эту панель.
          </p>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="top-bar__brand">
          <h1>Администрирование тарифов</h1>
          <p>Вы вошли как оператор.</p>
        </div>
        <nav className="top-bar__actions">
          <Link to="/" className="nav-link">
            На главную
          </Link>
          <Link to="/playground" className="nav-link">
            Playground
          </Link>
          <button onClick={logout} className="nav-button">
            Выйти
          </button>
        </nav>
      </header>
      <main className="admin-body">
        {loading && <p>Загружаем тарифы...</p>}
        {message && <p className="info-message">{message}</p>}
        <div className="admin-grid">
          {vehicleTypes.map((type) => (
            <form
              key={type.id}
              className="admin-card"
              onSubmit={(event) => handleSubmit(type.id, event)}
            >
              <h2>{type.name}</h2>
              {type.description && <p>{type.description}</p>}
              <label>
                Базовая цена
                <input
                  type="number"
                  step="0.01"
                  name="base_price"
                  value={edits[type.id]?.base_price ?? ""}
                  onChange={(event) => handleChange(type.id, event)}
                />
              </label>
              <label>
                Цена за километр
                <input
                  type="number"
                  step="0.01"
                  name="per_km_rate"
                  value={edits[type.id]?.per_km_rate ?? ""}
                  onChange={(event) => handleChange(type.id, event)}
                />
              </label>
              <button type="submit" disabled={savingId === type.id}>
                {savingId === type.id ? "Сохраняем..." : "Сохранить"}
              </button>
            </form>
          ))}
        </div>
      </main>
    </div>
  );
}
