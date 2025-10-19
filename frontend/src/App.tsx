import { useState } from "react";
import { AuthProvider, useAuth } from "./AuthContext";
import Dashboard from "./Dashboard";
import LoginForm from "./LoginForm";
import RegistrationForm from "./RegistrationForm";
import PasswordResetForm from "./PasswordResetForm";

type AuthMode = "login" | "register" | "reset";

function AuthGate() {
  const { accessToken } = useAuth();
  const [mode, setMode] = useState<AuthMode>("login");

  if (accessToken) {
    return <Dashboard />;
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1>
          {mode === "login"
            ? "Вход"
            : mode === "register"
              ? "Регистрация"
              : "Сброс пароля"}
        </h1>

        {mode === "login" && <LoginForm />}
        {mode === "register" && <RegistrationForm />}
        {mode === "reset" && <PasswordResetForm />}

        <div className="auth-links">
          {mode !== "login" && (
            <button type="button" onClick={() => setMode("login")}>
              У меня есть аккаунт
            </button>
          )}
          {mode !== "register" && (
            <button type="button" onClick={() => setMode("register")}>
              Регистрация
            </button>
          )}
          {mode !== "reset" && (
            <button type="button" onClick={() => setMode("reset")}>
              Забыли пароль?
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  );
}
