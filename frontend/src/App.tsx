import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import AuthPage from "./AuthPage";
import Home from "./Home";
import AdminPanel from "./AdminPanel";
import Dashboard from "./Dashboard";

function ProtectedRoute({
  children,
  requireOperator = false,
}: {
  children: ReactNode;
  requireOperator?: boolean;
}) {
  const { accessToken, user } = useAuth();

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  if (requireOperator && user?.user_type !== "OPERATOR") {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireOperator>
                <AdminPanel />
              </ProtectedRoute>
            }
          />
          <Route
            path="/playground"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
