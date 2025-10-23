import {
  createContext,
  useContext,
  useMemo,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  API_BASE,
  resolveUrl,
  parseResponse,
  createApiError,
  type HttpMethod,
} from "./api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: any | null;
}

interface LoginPayload {
  phone: string;
  password: string;
}

interface RegisterPayload {
  email?: string;
  phone: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  user_type: "CLIENT" | "DRIVER";
}

interface AuthContextValue extends AuthState {
  login(payload: LoginPayload): Promise<void>;
  register(payload: RegisterPayload): Promise<void>;
  resetPassword(args: {
    phone: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void>;
  logout(): void;
  updateTokens(tokens: Partial<AuthState>): void;
  apiFetch(
    pathOrUrl: string,
    init?: RequestInit & { method?: HttpMethod },
  ): Promise<Response>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "tow-truck-auth";

function loadInitialState(): AuthState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as AuthState;
      return parsed;
    }
  } catch {
    /* ignore broken storage */
  }
  return { accessToken: null, refreshToken: null, user: null };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => loadInitialState());

  const persist = useCallback((next: AuthState) => {
    setState(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }, []);

  const login = useCallback(
    async ({ phone, password }: LoginPayload) => {
      const response = await fetch(`${API_BASE}auth/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, password }),
      });
      const data = await parseResponse(response);
      if (!response.ok) {
        throw createApiError(
          "Не удалось выполнить вход",
          response.status,
          data,
        );
      }
      persist({
        accessToken: data.access ?? null,
        refreshToken: data.refresh ?? null,
        user: data.user ?? null,
      });
    },
    [persist],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      const response = await fetch(`${API_BASE}auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await parseResponse(response);
      if (!response.ok) {
        throw createApiError(
          "Регистрация не удалась",
          response.status,
          data,
        );
      }
      persist({
        accessToken: data.access ?? null,
        refreshToken: data.refresh ?? null,
        user: data.user ?? null,
      });
    },
    [persist],
  );

  const resetPassword = useCallback(
    async ({
      phone,
      new_password,
      new_password_confirm,
    }: {
      phone: string;
      new_password: string;
      new_password_confirm: string;
    }) => {
      const response = await fetch(`${API_BASE}auth/password/reset/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, new_password, new_password_confirm }),
      });
      const data = await parseResponse(response);
      if (!response.ok) {
        throw createApiError(
          "Не удалось сменить пароль",
          response.status,
          data,
        );
      }
    },
    [],
  );

  const logout = useCallback(() => {
    persist({ accessToken: null, refreshToken: null, user: null });
  }, [persist]);

  const updateTokens = useCallback(
    (tokens: Partial<AuthState>) => {
      persist({
        accessToken: tokens.accessToken ?? state.accessToken,
        refreshToken: tokens.refreshToken ?? state.refreshToken,
        user: tokens.user ?? state.user,
      });
    },
    [persist, state.accessToken, state.refreshToken, state.user],
  );

  const apiFetch = useCallback(
    async (pathOrUrl: string, init: RequestInit = {}) => {
      const url = resolveUrl(pathOrUrl);
      const headers = new Headers(init.headers);

      if (
        state.accessToken &&
        !headers.has("Authorization") &&
        !headers.has("authorization")
      ) {
        headers.set("Authorization", `Bearer ${state.accessToken}`);
      }

      if (
        init.body &&
        !(init.body instanceof FormData) &&
        !headers.has("Content-Type")
      ) {
        headers.set("Content-Type", "application/json");
      }

      const response = await fetch(url, { ...init, headers });

      if (!response.ok && response.status === 401) {
        logout();
      }

      return response;
    },
    [logout, state.accessToken],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      register,
      resetPassword,
      logout,
      updateTokens,
      apiFetch,
    }),
    [state, login, register, resetPassword, logout, updateTokens, apiFetch],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
