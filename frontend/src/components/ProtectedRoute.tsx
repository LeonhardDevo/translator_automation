import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

type Role = 'user' | 'admin';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: Role;
}

const getToken = (): string | null =>
  localStorage.getItem('token') || sessionStorage.getItem('token');

interface JwtPayload {
  sub?: string;
  role?: string;
  exp?: number;
}

const decodeJwt = (token: string): JwtPayload | null => {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
    return JSON.parse(atob(padded)) as JwtPayload;
  } catch {
    return null;
  }
};

const clearToken = () => {
  localStorage.removeItem('token');
  sessionStorage.removeItem('token');
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const location = useLocation();
  const token = getToken();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const payload = decodeJwt(token);
  if (!payload || (payload.exp && payload.exp * 1000 < Date.now())) {
    clearToken();
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (requiredRole && payload.role !== requiredRole) {
    return <Navigate to="/client" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
