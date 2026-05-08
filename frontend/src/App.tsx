// src/App.tsx
import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import ClientDashboard from './pages/ClientDashboard';
import Workspace from './pages/Workspace';

const App: React.FC = () => (
  <Routes>
    <Route path="/" element={<Navigate to="/login" />} />
    <Route path="/login" element={<Login />} />
    <Route path="/admin" element={<AdminDashboard />} />
    <Route path="/client" element={<ClientDashboard />} />
    <Route path="/workspace" element={<Workspace />} />
    {/* Default route to login */}
    <Route path="*" element={<Navigate to="/login" />} />
  </Routes>
);

export default App;
