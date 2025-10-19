import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { useAuth } from "./AuthContext";
import type { ApiError } from "./api";

interface LoginFormData {
  phone: string;
  password: string;
}

export default function LoginForm() {
  const { login } = useAuth();
  const [formData, setFormData] = useState<LoginFormData>({
    phone: "",
    password: "",
  });
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      await login(formData);
      setMessage("Вход выполнен успешно!");
    } catch (error) {
      if (error instanceof Error) {
        const apiError = error as ApiError;
        setMessage(
          apiError.payload
            ? `Ошибка ${apiError.status ?? ""}: ${JSON.stringify(apiError.payload)}`
            : error.message,
        );
      } else {
        setMessage("Неизвестная ошибка при выполнении входа.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid">
      <label>
        Телефон
        <input
          type="text"
          name="phone"
          placeholder="+79001234567"
          value={formData.phone}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Пароль
        <input
          type="password"
          name="password"
          placeholder="Пароль"
          value={formData.password}
          onChange={handleChange}
          required
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Выполняем вход..." : "Войти"}
      </button>

      {message && <p className="form-message">{message}</p>}
    </form>
  );
}
