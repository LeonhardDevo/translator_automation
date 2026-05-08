// frontend/src/pages/AdminDashboard.tsx
import React, { useState, useEffect, Suspense, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/axiosInstance';
import DashboardStats from '../components/Admin/DashboardStats';
import DashboardAnalytics from '../components/Admin/DashboardAnalytics';
import Logo from '../components/ui/Logo';
import ThemeToggle from '../components/ThemeToggle';
import '../App.css';
import { FaUserMinus, FaCogs, FaMoneyBill } from 'react-icons/fa';

// Lazy load components
const UserManagement = React.lazy(() => import('../components/Admin/UserManagement'));
const SystemManagement = React.lazy(() => import('../components/SystemManagement'));
const PurchaseRequests = React.lazy(() => import('../components/Admin/PurchaseRequests'));
const PricingAnalytics = React.lazy(() => import('../components/Admin/PricingAnalytics'));
const ManagePricingPlans = React.lazy(() => import('../components/Admin/ManagePricingPlans'));

interface SystemStats {
  total_users: number;
  active_users: number;
  total_documents: number;
  completed_documents: number;
  timestamp: string;
}

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [usageAnalytics, setUsageAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'system' | 'pricing'>(() => {
    const savedTab = localStorage.getItem('admin-active-tab');
    return savedTab as 'dashboard' | 'system' | 'pricing' || 'dashboard';
  });
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      // We only fetch stats and analytics here. User list is fetched by UserManagement.
      const statsResponse = await apiClient.get('/admin/stats');
      const analyticsResponse = await apiClient.get('/admin/usage-analytics');

      setStats(statsResponse.data);
      setUsageAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      // 401 handled by axios interceptor
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Load user theme preference on mount
  useEffect(() => {
    const loadUserTheme = async () => {
      try {
        const response = await apiClient.get('/user/dashboard');
        const userTheme = response.data.user_info?.theme || 'dark';
        
        // Apply theme
        setTheme(userTheme as 'dark' | 'light');
        applyTheme(userTheme);
      } catch (error) {
        console.error('Failed to load theme preference:', error);
      }
    };
    loadUserTheme();
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

  const handleLogout = () => {
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    navigate('/login');
  };

  const handleTabChange = (tab: 'dashboard' | 'system' | 'pricing') => {
    setActiveTab(tab);
    localStorage.setItem('admin-active-tab', tab);
  };

  const LoadingFallback = () => (
    <div className="dashboard-container">
      <div className="loading-spinner">Loading component...</div>
    </div>
  );

  if (loading && !stats) {
    return (
      <div className="dashboard-container">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  // Custom tab button styles
  const tabButtonStyle = (isActive: boolean): React.CSSProperties => ({
    padding: '10px 20px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.3s ease',
    background: isActive ? 'var(--gradient-primary)' : 'var(--color-bg-medium)',
    color: isActive ? 'white' : 'var(--color-text-primary)',
    boxShadow: isActive ? 'var(--shadow-primary)' : 'none'
  });

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <Logo width={45} height={45} />
          <h1 className="dashboard-title">Admin Dashboard</h1>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              style={tabButtonStyle(activeTab === 'dashboard')}
              onClick={() => handleTabChange('dashboard')}
            >
              <FaUserMinus /> Dashboard
            </button>
            <button
              style={tabButtonStyle(activeTab === 'system')}
              onClick={() => handleTabChange('system')}
            >
              <FaCogs /> System Management
            </button>
            <button
              style={tabButtonStyle(activeTab === 'pricing')}
              onClick={() => handleTabChange('pricing')}
            >
              <FaMoneyBill /> Pricing Management
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <ThemeToggle currentTheme={theme} onThemeChange={handleThemeChange} />
          <button 
            className="logout-btn" 
            onClick={handleLogout}
            style={{
              background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
              color: 'white',
              border: 'none',
              padding: '12px 25px',
              borderRadius: '12px',
              cursor: 'pointer',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.3s ease'
            }}
          >
            Logout
          </button>
        </div>
      </div>

      <Suspense fallback={<LoadingFallback />}>
        {activeTab === 'dashboard' && (
          <div>
            <DashboardStats stats={stats} />
            <DashboardAnalytics usageAnalytics={usageAnalytics} theme={theme} />

            <div style={{ marginTop: '40px' }}>
              <UserManagement onUserChange={fetchData} />
            </div>
          </div>
        )}

        {activeTab === 'system' && (
          <div style={{ marginTop: '20px' }}>
            <SystemManagement />
          </div>
        )}

        {activeTab === 'pricing' && (
          <div style={{ marginTop: '20px' }}>
            <div className="documents-list">
              <PricingAnalytics />
            </div>
            <div className="documents-list" style={{ marginTop: '20px' }}>
              <PurchaseRequests />
            </div>
            <div className="documents-list" style={{ marginTop: '20px' }}>
              <ManagePricingPlans />
            </div>
          </div>
        )}
      </Suspense>
    </div>
  );
};

export default AdminDashboard;
