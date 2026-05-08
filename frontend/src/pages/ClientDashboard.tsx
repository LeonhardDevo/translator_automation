// src/pages/ClientDashboard.tsx
import React, { useState, useEffect, useMemo, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FiMenu, FiX } from 'react-icons/fi';
import apiClient from '../api/axiosInstance';
import UploadForm from '../components/UploadForm';
import LanguageSwitcher from '../components/LanguageSwitcher';
import ThemeToggle from '../components/ThemeToggle';
import Logo from '../components/ui/Logo';
import '../App.css';

// Lazy load PricingCards
const PricingCards = React.lazy(() => import('../components/Client/PricingCards'));

interface UserStats {
  user_info: {
    id: number;
    email: string;
    full_name: string;
    daily_usage: number;
    daily_limit: number;
    total_usage: number;
    total_translated_images: number;
    plan_name: string;
    plan_total_limit: number;
    account_expires: string | null;
    language: string;
    theme: string;
  };
  stats: {
    submitted: number;
    translated: number;
  };
}

const ClientDashboard: React.FC = () => {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  // Load user language and theme preference on mount
  useEffect(() => {
    const loadUserPreferences = async () => {
      try {
        const response = await apiClient.get('/user/dashboard');
        const userLanguage = response.data.user_info?.language;
        const userTheme = response.data.user_info?.theme || 'dark';
        
        if (userLanguage) {
          i18n.changeLanguage(userLanguage);
        }
        
        // Apply theme
        setTheme(userTheme as 'dark' | 'light');
        applyTheme(userTheme);
      } catch (error) {
        console.error('Failed to load user preferences:', error);
      }
    };
    loadUserPreferences();
  }, []);

  // Apply theme class to document
  const applyTheme = (themeName: string) => {
    if (themeName === 'light') {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
  };

  // Handle theme change
  const handleThemeChange = (newTheme: 'dark' | 'light') => {
    setTheme(newTheme);
    applyTheme(newTheme);
  };

  const fetchStats = async () => {
    try {
      const response = await apiClient.get('/user/dashboard');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch user stats:', error);
      // 401 handled by axios interceptor
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    navigate('/login');
  };

  const dailyPercent = useMemo(() => {
    if (!stats) return 0;
    return stats.user_info.daily_limit > 0
      ? Math.round((stats.user_info.daily_usage / stats.user_info.daily_limit) * 100)
      : 0;
  }, [stats]);

  const totalPercent = useMemo(() => {
    if (!stats) return 0;
    return stats.user_info.plan_total_limit > 0
      ? Math.round((stats.user_info.total_usage / stats.user_info.plan_total_limit) * 100)
      : 0;
  }, [stats]);

  const { t, i18n } = useTranslation();

  if (loading) {
    return <div className="dashboard-container">{t('common.loading')}</div>;
  }

  if (!stats) {
    return <div className="dashboard-container">{t('common.error')}</div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <Logo width={45} height={45} />
          <h1 className="dashboard-title" style={{ margin: 0, fontSize: 'clamp(1rem, 3vw, 1.5rem)' }}>{t('dashboard.client_dashboard')}</h1>
        </div>
        
        {/* Desktop menu */}
        <div className="desktop-header-actions">
          <ThemeToggle currentTheme={theme} onThemeChange={handleThemeChange} />
          <LanguageSwitcher />
          <button style={{ background: 'var(--gradient-primary)', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap' }} onClick={() => navigate('/workspace')}>{t('workspace.title')} (Beta)</button>
          <button className="logout-btn" onClick={handleLogout}>{t('auth.logout')}</button>
        </div>

        {/* Mobile hamburger button */}
        <button 
          className="mobile-menu-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>

        {/* Mobile dropdown menu */}
        {mobileMenuOpen && (
          <div className="mobile-menu-dropdown">
            <ThemeToggle currentTheme={theme} onThemeChange={handleThemeChange} />
            <LanguageSwitcher />
            <button 
              style={{ background: 'var(--gradient-primary)', color: 'white', padding: '0.75rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 600, width: '100%', marginTop: '10px' }} 
              onClick={() => { navigate('/workspace'); setMobileMenuOpen(false); }}
            >
              {t('workspace.title')} (Beta)
            </button>
            <button 
              className="logout-btn" 
              onClick={handleLogout}
              style={{ width: '100%', marginTop: '10px' }}
            >
              {t('auth.logout')}
            </button>
          </div>
        )}
      </div>

      <div className="admin-stats-grid">
        <div className="stat-card">
          <div className="stat-number">{stats.user_info.daily_usage}</div>
          <div className="stat-label">{t('dashboard.todays_translations')}</div>
          <div className="stat-sublabel">{t('dashboard.daily_limit', { limit: stats.user_info.daily_limit })}</div>
          <div style={{ marginTop: '8px', background: 'var(--color-border)', borderRadius: '8px', height: '8px', overflow: 'hidden' }}>
            <div style={{
              width: `${Math.min(dailyPercent, 100)}%`,
              height: '100%',
              background: dailyPercent >= 90 ? 'var(--color-danger)' : dailyPercent >= 70 ? 'var(--color-warning)' : 'var(--color-success)',
              borderRadius: '8px',
              transition: 'width 0.5s ease'
            }}></div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-number">{stats.user_info.total_usage}</div>
          <div className="stat-label">{t('dashboard.total_used')}</div>
          <div className="stat-sublabel">
            {stats.user_info.plan_total_limit > 0
              ? t('dashboard.plan_limit', { limit: stats.user_info.plan_total_limit })
              : t('dashboard.no_active_plan')}
          </div>
            {stats.user_info.plan_total_limit > 0 && (
            <div style={{ marginTop: '8px', background: 'var(--color-border)', borderRadius: '8px', height: '8px', overflow: 'hidden' }}>
              <div style={{
                width: `${Math.min(totalPercent, 100)}%`,
                height: '100%',
                background: totalPercent >= 90 ? 'var(--color-danger)' : totalPercent >= 70 ? 'var(--color-warning)' : 'var(--color-success)',
                borderRadius: '8px',
                transition: 'width 0.5s ease'
              }}></div>
            </div>
          )}
        </div>

        <div className="stat-card">
          <div className="stat-number">{stats.user_info.plan_name}</div>
          <div className="stat-label">{t('dashboard.current_plan')}</div>
          {stats.user_info.plan_total_limit > 0 && (
            <div className="stat-sublabel">
              {t('dashboard.translations_remaining', { count: stats.user_info.plan_total_limit - stats.user_info.total_usage })}
            </div>
          )}
        </div>

        <div className="stat-card">
          <div className="stat-number">{stats.stats.translated}</div>
          <div className="stat-label">{t('dashboard.total_translated_images')}</div>
          <div className="stat-sublabel">{t('dashboard.all_time_never_resets')}</div>
        </div>

        <div className="stat-card">
          <div className="stat-number">{stats.stats.submitted}</div>
          <div className="stat-label">{t('dashboard.total_submitted')}</div>
          <div className="stat-sublabel">{t('dashboard.all_documents_submitted')}</div>
        </div>
      </div>

      <div className="upload-section">
        <h2>{t('translate.translate_document')}</h2>
        <UploadForm onUploadSuccess={fetchStats} />
      </div>

      <div className="upload-section" style={{ marginTop: '40px' }}>
        <h2>{t('pricing.available_pricing_plans')}</h2>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '30px', textAlign: 'center' }}>
          {t('pricing.choose_plan')}
        </p>
        <Suspense fallback={<div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>Loading pricing plans...</div>}>
          <PricingCards />
        </Suspense>
      </div>
    </div>
  );
};

export default ClientDashboard;
