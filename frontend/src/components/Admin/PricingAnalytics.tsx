import React, { useState, useEffect } from 'react';
import apiClient from '../../api/axiosInstance';
import '../../App.css';

interface AnalyticsData {
  total_users: number;
  active_users: number;
  total_translations?: number;
  plan_breakdown: Array<{
    plan_name: string;
    subscribers: number;
  }>;
}

const PricingAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await apiClient.get('/pricing/admin/pricing-analytics');
        setAnalytics(response.data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) return <div className="loading-spinner">Loading analytics...</div>;
  if (!analytics) return (
    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>
      No analytics data available
    </div>
  );

  return (
    <div>
      <h2 style={{ color: 'var(--color-text-heading)', marginBottom: '20px' }}>Pricing Analytics</h2>
      <div className="admin-stats-grid">
        <div className="stat-card">
          <div className="stat-number">{analytics.total_users}</div>
          <div className="stat-label">Total Users</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-number">{analytics.active_users}</div>
          <div className="stat-label">Active Users</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-number">{analytics.total_translations || 0}</div>
          <div className="stat-label">Total Translations</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-number">Plans: {analytics.plan_breakdown.length}</div>
          <div className="stat-label">Plan Distribution</div>
          <div className="stat-sublabel">
            {analytics.plan_breakdown.map((plan, index) => (
              <div key={index} style={{ color: 'var(--color-accent-dark)' }}>{plan.plan_name}: {plan.subscribers}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingAnalytics;
