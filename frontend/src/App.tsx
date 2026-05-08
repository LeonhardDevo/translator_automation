// src/App.tsx
import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import ClientDashboard from './pages/ClientDashboard';
import Workspace from './pages/Workspace';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => (
  <Routes>
    <Route path="/" element={<Navigate to="/login" replace />} />
    <Route path="/login" element={<Login />} />
    <Route
      path="/admin"
      element={
        <ProtectedRoute requiredRole="admin">
          <AdminDashboard />
        </ProtectedRoute>
      }
    />
    <Route
      path="/client"
      element={
        <ProtectedRoute>
          <ClientDashboard />
        </ProtectedRoute>
      }
    />
    <Route
      path="/workspace"
      element={
        <ProtectedRoute>
          <Workspace />
        </ProtectedRoute>
      }
    />
    {/* Default route to login */}
    <Route path="*" element={<Navigate to="/login" replace />} />
  </Routes>
);

export default App;
