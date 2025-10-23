import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import LoginForm from "./LoginForm";
import RegistrationForm from "./RegistrationForm";
import PasswordResetForm from "./PasswordResetForm";

type AuthMode = "login" | "register" | "reset";

export default function AuthPage() {
  const navigate = useNavigate();
  const { accessToken } = useAuth();
  const [mode, setMode] = useState<AuthMode>("login");

  useEffect(() => {
    if (accessToken) {
      navigate("/", { replace: true });
    }
  }, [accessToken, navigate]);

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1>
          {mode === "login"
            ? "Вход в сервис эвакуации"
            : mode === "register"
            ? "Регистрация клиента"
            : "Сброс пароля"}
        </h1>

        {mode === "login" && <LoginForm />}
        {mode === "register" && <RegistrationForm />}
        {mode === "reset" && <PasswordResetForm />}

        <div className="auth-links">
          {mode !== "login" && (
            <button type="button" onClick={() => setMode("login")}>
              Уже зарегистрированы?
            </button>
          )}
          {mode !== "register" && (
            <button type="button" onClick={() => setMode("register")}>
              Создать аккаунт
            </button>
          )}
          {mode !== "reset" && (
            <button type="button" onClick={() => setMode("reset")}>
              Забыл пароль
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
