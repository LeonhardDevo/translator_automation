import React from 'react';

interface SystemStats {
    total_users: number;
    active_users: number;
    total_documents: number;
    completed_documents: number;
    timestamp: string;
}

interface DashboardStatsProps {
    stats: SystemStats | null;
}

const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
    return (
        <div className="admin-stats-grid">
            <div className="stat-card">
                <div className="stat-number">{stats?.total_users || 0}</div>
                <div className="stat-label">Total Users</div>
            </div>

            <div className="stat-card">
                <div className="stat-number">{stats?.active_users || 0}</div>
                <div className="stat-label">Active Users</div>
            </div>

            <div className="stat-card">
                <div className="stat-number">{stats?.total_documents || 0}</div>
                <div className="stat-label">Total Documents</div>
            </div>

            <div className="stat-card">
                <div className="stat-number">{stats?.completed_documents || 0}</div>
                <div className="stat-label">Completed</div>
            </div>

            <div className="stat-card">
                <div className="stat-number">N/A</div>
                <div className="stat-label">Pending</div>
            </div>
        </div>
    );
};

export default React.memo(DashboardStats);
