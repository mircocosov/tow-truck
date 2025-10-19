import type { ChangeEvent, FormEvent } from "react";
import { useState } from "react";
import { useAuth } from "./AuthContext";
import type { ApiError } from "./api";

interface RegistrationFormData {
  email: string;
  phone: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  user_type: "CLIENT" | "DRIVER";
}

export default function RegistrationForm() {
  const { register } = useAuth();
  const [formData, setFormData] = useState<RegistrationFormData>({
    email: "",
    phone: "",
    password: "",
    password_confirm: "",
    first_name: "",
    last_name: "",
    user_type: "CLIENT",
  });

  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleChange = (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (formData.password !== formData.password_confirm) {
      setMessage("Пароли должны совпадать.");
      return;
    }

    if (!/^\+?[0-9]{7,15}$/.test(formData.phone)) {
      setMessage(
        "Укажите корректный номер телефона в международном формате.",
      );
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await register(formData);
      setMessage("Регистрация успешно выполнена!");
      setFormData({
        email: "",
        phone: "",
        password: "",
        password_confirm: "",
        first_name: "",
        last_name: "",
        user_type: "CLIENT",
      });
    } catch (error) {
      if (error instanceof Error) {
        const apiError = error as ApiError;
        setMessage(
          apiError.payload
            ? `Ошибка ${apiError.status ?? ""}: ${JSON.stringify(apiError.payload)}`
            : error.message,
        );
      } else {
        setMessage("Неизвестная ошибка при регистрации.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid">
      <label>
        Email
        <input
          type="email"
          name="email"
          placeholder="email@example.com"
          value={formData.email}
          onChange={handleChange}
        />
      </label>

      <label>
        Телефон*
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
        Пароль*
        <input
          type="password"
          name="password"
          placeholder="Пароль"
          value={formData.password}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Повторите пароль*
        <input
          type="password"
          name="password_confirm"
          placeholder="Подтвердите пароль"
          value={formData.password_confirm}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Имя
        <input
          type="text"
          name="first_name"
          value={formData.first_name}
          onChange={handleChange}
          maxLength={150}
        />
      </label>

      <label>
        Фамилия
        <input
          type="text"
          name="last_name"
          value={formData.last_name}
          onChange={handleChange}
          maxLength={150}
        />
      </label>

      <label>
        Тип пользователя
        <select
          name="user_type"
          value={formData.user_type}
          onChange={handleChange}
        >
          <option value="CLIENT">Client</option>
          <option value="DRIVER">Driver</option>
        </select>
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Регистрируем..." : "Зарегистрироваться"}
      </button>

      {message && <p className="form-message">{message}</p>}
    </form>
  );
}
