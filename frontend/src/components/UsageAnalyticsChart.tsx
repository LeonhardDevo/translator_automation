// frontend/src/components/UsageAnalyticsChart.tsx
import React from 'react';
import { BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface UsagePoint {
  date?: string;
  week?: string;
  month?: string;
  count: number;
}

interface UsageAnalyticsData {
  daily_usage?: UsagePoint[];
  weekly_usage?: UsagePoint[];
  monthly_usage?: UsagePoint[];
}

interface UsageAnalyticsChartProps {
  usageData: UsageAnalyticsData;
  theme?: 'dark' | 'light';
}

// Define theme colors
const getThemeColors = (theme: 'dark' | 'light') => ({
  background: theme === 'dark' ? '#1E293B' : '#F8FAFC',
  text: theme === 'dark' ? '#E2E8F0' : '#1E293B',
  textSecondary: theme === 'dark' ? '#94A3B8' : '#64748B',
  grid: theme === 'dark' ? '#334155' : '#E2E8F0',
  accent: theme === 'dark' ? '#22D3EE' : '#0EA5E9',
  accentSecondary: theme === 'dark' ? '#3B82F6' : '#0284C7',
  border: theme === 'dark' ? '#334155' : '#CBD5E1',
  tooltipBg: theme === 'dark' ? '#1E293B' : '#FFFFFF',
  tooltipBorder: theme === 'dark' ? '#22D3EE' : '#0EA5E9',
  tooltipText: theme === 'dark' ? '#E2E8F0' : '#1E293B',
});

const UsageAnalyticsChart: React.FC<UsageAnalyticsChartProps> = ({ usageData, theme = 'dark' }) => {
  const colors = getThemeColors(theme);

  // Format daily usage data for chart
  const dailyChartData = usageData.daily_usage?.map(item => ({
    date: item.date ? new Date(item.date).toLocaleDateString() : 'N/A',
    count: item.count
  })) || [];

  // Format weekly usage data for chart
  const weeklyChartData = usageData.weekly_usage?.map(item => ({
    week: item.week ? `Week of ${new Date(item.week).toLocaleDateString()}` : 'N/A',
    count: item.count
  })) || [];

  // Format monthly usage data for chart
  const monthlyChartData = usageData.monthly_usage?.map(item => ({
    month: item.month ? new Date(item.month).toLocaleDateString('en-US', { year: 'numeric', month: 'short' }) : 'N/A',
    count: item.count
  })) || [];

  // Custom tooltip based on theme
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ 
          backgroundColor: colors.tooltipBg, 
          border: `1px solid ${colors.tooltipBorder}`, 
          borderRadius: '8px', 
          padding: '10px',
          boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)'
        }}>
          <p style={{ color: colors.tooltipText, margin: '0 0 5px 0', fontWeight: 600 }}>{label}</p>
          <p style={{ color: colors.accent, margin: 0 }}>{`Usage: ${payload[0]?.value || 0}`}</p>
        </div>
      );
    }
    return null;
  };

  const chartContainerStyle = {
    backgroundColor: colors.background,
    padding: '20px',
    borderRadius: '15px',
    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
    minWidth: '300px' as const,
    minHeight: '350px' as const,
    border: `1px solid ${colors.border}`
  };

  return (
    <div className="usage-analytics-charts">
      <h3 style={{ color: colors.text, marginBottom: '20px' }}>Usage Analytics Charts</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
        {/* Daily Usage Chart */}
        <div className="chart-container" style={chartContainerStyle}>
          <h4 style={{ marginBottom: '15px', textAlign: 'center', color: colors.text }}>Daily Usage</h4>
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis dataKey="date" stroke={colors.textSecondary} tick={{ fill: colors.textSecondary }} />
                <YAxis stroke={colors.textSecondary} tick={{ fill: colors.textSecondary }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: colors.text }} />
                <Bar dataKey="count" name="Usage Count" fill={colors.accent} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weekly Usage Chart */}
        <div className="chart-container" style={chartContainerStyle}>
          <h4 style={{ marginBottom: '15px', textAlign: 'center', color: colors.text }}>Weekly Usage</h4>
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis dataKey="week" stroke={colors.textSecondary} tick={{ fill: colors.textSecondary }} />
                <YAxis stroke={colors.textSecondary} tick={{ fill: colors.textSecondary }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: colors.text }} />
                <Line type="monotone" dataKey="count" name="Usage Count" stroke={colors.accentSecondary} strokeWidth={2} dot={{ r: 4, fill: colors.accentSecondary }} activeDot={{ r: 6, fill: colors.accent }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Monthly Usage Chart */}
        <div className="chart-container" style={chartContainerStyle}>
          <h4 style={{ marginBottom: '15px', textAlign: 'center', color: colors.text }}>Monthly Usage</h4>
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis dataKey="month" stroke={colors.textSecondary} tick={{ fill: colors.textSecondary }} />
                <YAxis stroke={colors.textSecondary} tick={{ fill: colors.textSecondary }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: colors.text }} />
                <Area type="monotone" dataKey="count" name="Usage Count" fill={colors.accent} stroke={colors.accentSecondary} fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsageAnalyticsChart;
