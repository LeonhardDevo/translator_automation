import React from 'react';
import UsageAnalyticsChart from '../UsageAnalyticsChart';

interface DashboardAnalyticsProps {
    usageAnalytics: any;
    theme?: 'dark' | 'light';
}

const DashboardAnalytics: React.FC<DashboardAnalyticsProps> = ({ usageAnalytics, theme = 'dark' }) => {
    return (
        <>
            <div className="upload-section" style={{ width: '100%' }}>
                <h2 style={{ color: 'var(--color-text-heading)', marginBottom: '15px' }}>Usage Analytics</h2>
                <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>Track daily, weekly, and monthly usage patterns across the platform.</p>
                <UsageAnalyticsChart usageData={usageAnalytics || {}} theme={theme} />
            </div>

            <div className="upload-section" style={{ width: '100%' }}>
                <h2 style={{ color: 'var(--color-text-heading)', marginBottom: '15px' }}>Usage Statistics & Diagrams</h2>
                <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>Detailed breakdown of daily, weekly, and monthly usage across the platform.</p>

                <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '20px', marginTop: '20px' }}>
                    <div className="stat-card" style={{ minWidth: '250px', flex: '1', textAlign: 'center', padding: '25px' }}>
                        <div className="stat-number">{usageAnalytics?.daily_usage?.length || 0}</div>
                        <div className="stat-label">Daily Usage Points</div>
                        <p className="stat-sublabel" style={{ color: 'var(--color-text-secondary)', marginTop: '5px' }}>Last 7 days</p>
                    </div>

                    <div className="stat-card" style={{ minWidth: '250px', flex: '1', textAlign: 'center', padding: '25px' }}>
                        <div className="stat-number">{usageAnalytics?.weekly_usage?.length || 0}</div>
                        <div className="stat-label">Weekly Usage Points</div>
                        <p className="stat-sublabel" style={{ color: 'var(--color-text-secondary)', marginTop: '5px' }}>Last 4 weeks</p>
                    </div>

                    <div className="stat-card" style={{ minWidth: '250px', flex: '1', textAlign: 'center', padding: '25px' }}>
                        <div className="stat-number">{usageAnalytics?.monthly_usage?.length || 0}</div>
                        <div className="stat-label">Monthly Usage Points</div>
                        <p className="stat-sublabel" style={{ color: 'var(--color-text-secondary)', marginTop: '5px' }}>Last 6 months</p>
                    </div>
                </div>
            </div>
        </>
    );
};

export default React.memo(DashboardAnalytics);
