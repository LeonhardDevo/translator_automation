// src/pages/Login.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/axiosInstance';
import { useTranslation } from 'react-i18next';
import '../App.css';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import Logo from '../components/ui/Logo';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      // Login request
      const response = await apiClient.post('/auth/login', {
        email,
        password,
        remember_me: rememberMe
      });
      const token: string = response.data.access_token;

      // Clear any existing tokens first
      localStorage.removeItem('token');
      sessionStorage.removeItem('token');

      // Store token based on "Remember Me" preference
      if (rememberMe) {
        localStorage.setItem('token', token);
      } else {
        sessionStorage.setItem('token', token);
      }

      // Check if user is admin
      try {
        await apiClient.get('/admin/users');
        navigate('/admin');
      } catch {
        // If not admin, try regular user dashboard - get language preference
        const dashboardResponse = await apiClient.get('/user/dashboard');
        const userLanguage = dashboardResponse.data.user_info.language || 'en';
        i18n.changeLanguage(userLanguage);
        navigate('/client');
      }
    } catch (err) {
      console.error('Login failed', err);
      // Determine error message based on type
      let errorMessage = t('login_failed');
      const error = err as any; // Cast to any to access properties safely
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
      alert(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      {/* Floating bubbles for liquid effect */}
      <div className="bubble" style={{ width: '80px', height: '80px', top: '15%', left: '10%', animationDelay: '0s' }}></div>
      <div className="bubble" style={{ width: '60px', height: '60px', top: '70%', left: '85%', animationDelay: '2s' }}></div>
      <div className="bubble" style={{ width: '40px', height: '40px', top: '40%', left: '80%', animationDelay: '4s' }}></div>
      <div className="bubble" style={{ width: '70px', height: '70px', top: '80%', left: '15%', animationDelay: '1s' }}></div>

      {/* Additional floating elements */}
      <div className="floating-element" style={{ width: '120px', height: '120px', top: '5%', right: '5%', animationDuration: '20s' }}></div>
      <div className="floating-element" style={{ width: '100px', height: '100px', bottom: '10%', left: '5%', animationDuration: '25s', animationDelay: '3s' }}></div>

      <div className="liquid-form">
        {/* Logo at the top */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '-30px', marginTop: '-50px' }}>
          <Logo width={150} height={150} />
        </div>
        
        <h2 className="form-title">{t('Login')}</h2>
        <form onSubmit={handleLogin}>
          <div className="input-group">
            <input
              type="email"
              placeholder={t('email')}
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="form-input"
              required
            />
          </div>

          <div className="input-group password-input-group">
            <input
              type={showPassword ? 'text' : 'password'}
              placeholder={t('password')}
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="form-input"
              required
            />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
            >
              {showPassword ? <FiEyeOff /> : <FiEye />}
            </button>
          </div>

          <div className="input-group checkbox-group" style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
            <input
              type="checkbox"
              id="remember_me"
              checked={rememberMe}
              onChange={e => setRememberMe(e.target.checked)}
              style={{ marginRight: '0.5rem', width: 'auto', accentColor: 'var(--color-accent-dark)' }}
            />
            <label htmlFor="remember_me" style={{ color: 'var(--color-text-secondary)', cursor: 'pointer' }}>{t('remember_me') || 'Remember me'}</label>
          </div>


          <button
            type="submit"
            className="form-button"
            disabled={isLoading}
          >
            {isLoading ? t('logging_in') : t('login')}
          </button>
        </form>

        <div className="form-footer">
          <p>
            Contact administrator to create an account
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
