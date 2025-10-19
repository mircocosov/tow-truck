import { useState } from "react";
import { API_BASE, parseResponse } from "./api";

interface ResetFormData {
  phone: string;
  new_password: string;
  new_password_confirm: string;
}

export default function PasswordResetForm() {
  const [formData, setFormData] = useState<ResetFormData>({
    phone: "",
    new_password: "",
    new_password_confirm: "",
  });
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (formData.new_password !== formData.new_password_confirm) {
      setMessage("Пароли должны совпадать.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}auth/password/reset/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const payload = await parseResponse(response);

      if (response.ok) {
        setMessage(
          typeof payload === "string"
            ? payload
            : JSON.stringify(payload),
        );
        setFormData({ phone: "", new_password: "", new_password_confirm: "" });
      } else {
        setMessage(
          typeof payload === "string"
            ? payload
            : JSON.stringify(payload),
        );
      }
    } catch (error) {
      if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("Неизвестная ошибка при сбросе пароля.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form-grid">
      <label>
        Телефон*
        <input
          type="text"
          name="phone"
          placeholder="Phone*"
          value={formData.phone}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Новый пароль*
        <input
          type="password"
          name="new_password"
          placeholder="Новый пароль"
          value={formData.new_password}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Повторите пароль*
        <input
          type="password"
          name="new_password_confirm"
          placeholder="Подтвердите пароль"
          value={formData.new_password_confirm}
          onChange={handleChange}
          required
        />
      </label>
      <button type="submit" disabled={loading}>
        {loading ? "Обновляем..." : "Сбросить пароль"}
      </button>
      {message && <p className="form-message">{message}</p>}
    </form>
  );
}
