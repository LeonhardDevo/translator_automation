import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FiGlobe, FiCheck } from 'react-icons/fi';
import apiClient from '../api/axiosInstance';

const languages = [
  { code: 'tk', name: 'Türkmen', flag: '🇹🇲' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' }
];

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[1];

  const changeLanguage = async (lng: string) => {
    setIsLoading(true);
    try {
      // Save language preference to backend
      await apiClient.put('/user/language', null, {
        params: { language: lng }
      });
      i18n.changeLanguage(lng);
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to save language preference:', error);
      // Still change language locally even if backend save fails
      i18n.changeLanguage(lng);
      setIsOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: 'var(--color-bg-subtle)',
          border: '1px solid var(--color-border)',
          borderRadius: '8px',
          cursor: isLoading ? 'wait' : 'pointer',
          color: 'var(--color-text-primary)',
          fontSize: '14px',
          transition: 'all 0.2s ease',
          opacity: isLoading ? 0.7 : 1
        }}
        onMouseOver={(e) => {
          if (!isLoading) {
            e.currentTarget.style.background = 'var(--color-bg-medium)';
          }
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = 'var(--color-bg-subtle)';
        }}
      >
        <FiGlobe size={16} />
        <span>{currentLanguage.flag}</span>
        <span style={{ fontWeight: 500 }}>{currentLanguage.name}</span>
        {isLoading && <span style={{ fontSize: '12px' }}>...</span>}
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: '4px',
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            boxShadow: 'var(--shadow-card)',
            zIndex: 10000,
            minWidth: '160px',
            overflow: 'hidden'
          }}
        >
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              disabled={isLoading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                width: '100%',
                padding: '10px 14px',
                background: i18n.language === lang.code 
                  ? 'var(--gradient-primary)' 
                  : 'transparent',
                border: 'none',
                cursor: isLoading ? 'wait' : 'pointer',
                color: i18n.language === lang.code 
                  ? 'white' 
                  : 'var(--color-text-primary)',
                fontSize: '14px',
                textAlign: 'left',
                transition: 'all 0.15s ease',
                opacity: isLoading ? 0.7 : 1
              }}
              onMouseOver={(e) => {
                if (i18n.language !== lang.code && !isLoading) {
                  e.currentTarget.style.background = 'var(--color-bg-subtle)';
                }
              }}
              onMouseOut={(e) => {
                if (i18n.language !== lang.code) {
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <span style={{ fontSize: '18px' }}>{lang.flag}</span>
              <span style={{ flex: 1 }}>{lang.name}</span>
              {i18n.language === lang.code && <FiCheck size={16} />}
            </button>
          ))}
        </div>
      )}
      
      {/* Overlay to close dropdown when clicking outside */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 9999
          }}
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default LanguageSwitcher;
