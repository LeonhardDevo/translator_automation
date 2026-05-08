import React from 'react';
import { FiSun, FiMoon } from 'react-icons/fi';
import { useTranslation } from 'react-i18next';
import apiClient from '../api/axiosInstance';

interface ThemeToggleProps {
  currentTheme: 'dark' | 'light';
  onThemeChange: (theme: 'dark' | 'light') => void;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ currentTheme, onThemeChange }) => {
  const { t } = useTranslation();

  const handleToggle = async () => {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    try {
      await apiClient.put(`/user/theme?theme=${newTheme}`);
      onThemeChange(newTheme);
    } catch (error) {
      console.error('Failed to update theme preference:', error);
    }
  };

  return (
    <button
      onClick={handleToggle}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '0.5rem 1rem',
        borderRadius: '8px',
        border: '1px solid var(--color-border)',
        background: 'var(--color-bg-medium)',
        color: 'var(--color-text-primary)',
        cursor: 'pointer',
        fontWeight: 600,
        fontSize: '0.9rem',
        transition: 'all 0.3s ease',
      }}
      title={currentTheme === 'dark' ? t('theme.switch_to_light') : t('theme.switch_to_dark')}
    >
      {currentTheme === 'dark' ? (
        <>
          <FiSun size={18} style={{ color: '#F59E0B' }} />
          <span>{t('theme.light')}</span>
        </>
      ) : (
        <>
          <FiMoon size={18} style={{ color: '#6366F1' }} />
          <span>{t('theme.dark')}</span>
        </>
      )}
    </button>
  );
};

export default ThemeToggle;
