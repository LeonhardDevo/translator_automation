import React, { useState, useEffect } from 'react';
import apiClient from '../api/axiosInstance';
import '../styles/SystemManagement.css';

interface ApiKey {
  id: number;
  key: string;
  description: string;
  created_at: string;
  last_used: string | null;
}

const SystemManagement: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyDescription, setNewKeyDescription] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoadingKeys, setIsLoadingKeys] = useState(false);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);
  const [showApiSection, setShowApiSection] = useState(true);
  const [showLogsSection, setShowLogsSection] = useState(true);
  const [showJwtSection, setShowJwtSection] = useState(true);
  const [jwtConfig, setJwtConfig] = useState({
    current_access_token_expire_minutes: 60,
    current_refresh_token_expire_days: 30,
    current_max_concurrent_sessions: 5,
    enforce_strong_auth: false,
    total_active_sessions: 0,
    active_sessions: []
  });
  const [jwtUpdates, setJwtUpdates] = useState({
    access_token_expire_minutes: '',
    refresh_token_expire_days: '',
    max_concurrent_sessions: '',
    enforce_strong_auth: false
  });
  const [isLoadingJwt, setIsLoadingJwt] = useState(false);

  // Load API keys on component mount
  useEffect(() => {
    loadApiKeys();
    loadSystemLogs();
  }, []);

  useEffect(() => {
    loadJwtConfig();
  }, []);

  const loadJwtConfig = async () => {
    setIsLoadingJwt(true);
    try {
      const response = await apiClient.get('/admin/jwt-session-config');
      setJwtConfig(response.data);
    } catch (error) {
      console.error('Failed to load JWT config:', error);
      alert('Failed to load JWT session configuration.');
    } finally {
      setIsLoadingJwt(false);
    }
  };

  const updateJwtConfig = async () => {
    setIsLoadingJwt(true);
    try {
      const configUpdate: any = {};
      if (jwtUpdates.access_token_expire_minutes) {
        configUpdate.access_token_expire_minutes = parseInt(jwtUpdates.access_token_expire_minutes);
      }
      if (jwtUpdates.refresh_token_expire_days) {
        configUpdate.refresh_token_expire_days = parseInt(jwtUpdates.refresh_token_expire_days);
      }
      if (jwtUpdates.max_concurrent_sessions) {
        configUpdate.max_concurrent_sessions = parseInt(jwtUpdates.max_concurrent_sessions);
      }
      configUpdate.enforce_strong_auth = jwtUpdates.enforce_strong_auth;

      await apiClient.post('/admin/jwt-session-config', configUpdate);
      alert('JWT session configuration updated successfully!');
      loadJwtConfig(); // Refresh the config
    } catch (error) {
      console.error('Failed to update JWT config:', error);
      alert('Failed to update JWT session configuration.');
    } finally {
      setIsLoadingJwt(false);
    }
  };

  const handleJwtInputChange = (field: string, value: string | boolean) => {
    setJwtUpdates(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const loadApiKeys = async () => {
    setIsLoadingKeys(true);
    try {
      const response = await apiClient.get('/admin/gemini-api-keys');
      // The API response already matches our expected format
      setApiKeys(response.data);
    } catch (error) {
      console.error('Failed to load API keys:', error);
      alert('Failed to load API keys. Please try again later.');
    } finally {
      setIsLoadingKeys(false);
    }
  };

  const loadSystemLogs = async () => {
    setIsLoadingLogs(true);
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      // Mock system logs data
      setLogs([
        '[2023-01-01 10:00:00] INFO: System started successfully',
        '[2023-01-01 10:05:23] DEBUG: Database connection established',
        '[2023-01-01 10:15:45] WARN: High memory usage detected (85%)',
        '[2023-01-01 10:30:12] ERROR: Failed to process document batch',
        '[2023-01-01 11:00:30] INFO: User login: admin@example.com',
        '[2023-01-01 11:15:20] DEBUG: API rate limit check passed',
        '[2023-01-01 12:00:00] INFO: Daily maintenance completed',
        '[2023-01-01 13:45:10] WARN: Translation service timeout',
        '[2023-01-01 14:20:33] INFO: Backup completed successfully',
        '[2023-01-01 15:10:55] ERROR: Database connection lost',
        '[2023-01-01 15:11:02] INFO: Database connection restored',
        '[2023-01-01 16:30:40] DEBUG: Performance metrics collected',
        '[2023-01-01 17:00:00] INFO: System shutdown initiated'
      ]);
    } catch (error) {
      console.error('Failed to load system logs:', error);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const generateNewApiKey = async () => {
    if (!newKeyDescription.trim()) {
      alert('Please enter a valid API key');
      return;
    }

    try {
      // For Gemini API keys, the description field actually contains the API key itself
      await apiClient.post('/admin/gemini-api-keys', {
        key: newKeyDescription  // The input field contains the actual API key
      });

      // Reload the keys to reflect the newly added key
      loadApiKeys();
      setNewKeyDescription(''); // Clear the input field
    } catch (error) {
      console.error('Failed to add API key:', error);
      alert('Failed to add API key. Please check the key format and try again.');
    }
  };

  const revokeApiKey = async (keyId: number) => {
    if (!window.confirm('Are you sure you want to remove this API key? This action cannot be undone.')) {
      return;
    }

    try {
      // Note: keyId is 1-based for display, but the backend expects 0-based index
      const keyIndex = keyId - 1;
      await apiClient.delete(`/admin/gemini-api-keys/${keyIndex}`);

      // Reload the keys to reflect the removal
      loadApiKeys();
    } catch (error) {
      console.error('Failed to remove API key:', error);
      alert('Failed to remove API key. Please try again.');
    }
  };

  const refreshLogs = () => {
    loadSystemLogs();
  };

  const clearLogs = () => {
    if (window.confirm('Are you sure you want to clear all logs? This action cannot be undone.')) {
      setLogs([]);
    }
  };

  return (
    <div className="system-management-container">
      <div className="system-management-header">
        <h2 className="system-management-title">System Management</h2>
      </div>

      {/* API Keys Management Section */}
      <div className="toggle-system-section">
        <button
          className="system-btn system-btn-primary"
          onClick={() => setShowApiSection(!showApiSection)}
        >
          {showApiSection ? 'Hide' : 'Show'} API Keys Management
        </button>
      </div>

      {showApiSection && (
        <div className="api-keys-section">
          <h3 className="section-title">API Key Management</h3>

          {/* Add New API Key Form */}
          <div className="key-form">
            <div className="key-form-group">
              <label htmlFor="apiKeyValue">Google Gemini API Key:</label>
              <input
                type="text"
                id="apiKeyValue"
                value={newKeyDescription}
                onChange={(e) => setNewKeyDescription(e.target.value)}
                placeholder="Enter the full Google Gemini API key (starts with AIza...)"
              />
            </div>

            <button
              className="system-btn system-btn-success"
              onClick={generateNewApiKey}
              disabled={isLoadingKeys}
            >
              Add New API Key
            </button>
          </div>

          {/* API Keys List */}
          <div>
            <h4>Existing API Keys ({apiKeys.length})</h4>
            {isLoadingKeys ? (
              <p>Loading API keys...</p>
            ) : apiKeys.length > 0 ? (
              <div>
                {apiKeys.map((apiKey) => (
                  <div key={apiKey.id} className="api-key-item">
                    <div className="api-key-value">
                      {apiKey.key.substring(0, 8)}...{apiKey.key.substring(apiKey.key.length - 4)}
                    </div>
                    <div style={{ minWidth: '200px' }}>
                      <div><strong>{apiKey.description}</strong></div>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>
                        Created: {new Date(apiKey.created_at).toLocaleString()}<br />
                        {apiKey.last_used ? `Last used: ${new Date(apiKey.last_used).toLocaleString()}` : 'Never used'}
                      </div>
                    </div>
                    <div className="api-key-actions">
                      <button
                        className="system-btn system-btn-danger"
                        onClick={() => revokeApiKey(apiKey.id)}
                        title="Revoke API Key"
                      >
                        Revoke
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No API keys found.</p>
            )}
          </div>
        </div>
      )}

      {/* JWT Session Management Section */}
      <div className="toggle-system-section">
        <button
          className="system-btn system-btn-primary"
          onClick={() => setShowJwtSection(!showJwtSection)}
        >
          {showJwtSection ? 'Hide' : 'Show'} JWT Session Management
        </button>
      </div>

      {showJwtSection && (
        <div className="jwt-config-section">
          <h3 className="section-title">JWT Session Configuration</h3>

          <div className="jwt-config-display">
            <div className="config-item">
              <strong>Current Access Token Expiration:</strong> {jwtConfig.current_access_token_expire_minutes} minutes
            </div>
            <div className="config-item">
              <strong>Current Refresh Token Expiration:</strong> {jwtConfig.current_refresh_token_expire_days} days
            </div>
            <div className="config-item">
              <strong>Max Concurrent Sessions:</strong> {jwtConfig.current_max_concurrent_sessions}
            </div>
            <div className="config-item">
              <strong>Strong Auth Enforcement:</strong> {jwtConfig.enforce_strong_auth ? 'Enabled' : 'Disabled'}
            </div>
            <div className="config-item">
              <strong>Total Active Sessions:</strong> {jwtConfig.total_active_sessions}
            </div>
          </div>

          <div className="jwt-config-form">
            <h4>Update JWT Configuration</h4>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="accessTokenExpire">Access Token Expire (minutes):</label>
                <input
                  type="number"
                  id="accessTokenExpire"
                  value={jwtUpdates.access_token_expire_minutes}
                  onChange={(e) => handleJwtInputChange('access_token_expire_minutes', e.target.value)}
                  placeholder={jwtConfig.current_access_token_expire_minutes.toString()}
                />
              </div>

              <div className="form-group">
                <label htmlFor="refreshTokenExpire">Refresh Token Expire (days):</label>
                <input
                  type="number"
                  id="refreshTokenExpire"
                  value={jwtUpdates.refresh_token_expire_days}
                  onChange={(e) => handleJwtInputChange('refresh_token_expire_days', e.target.value)}
                  placeholder={jwtConfig.current_refresh_token_expire_days.toString()}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="maxConcurrentSessions">Max Concurrent Sessions:</label>
                <input
                  type="number"
                  id="maxConcurrentSessions"
                  value={jwtUpdates.max_concurrent_sessions}
                  onChange={(e) => handleJwtInputChange('max_concurrent_sessions', e.target.value)}
                  placeholder={jwtConfig.current_max_concurrent_sessions.toString()}
                />
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={jwtUpdates.enforce_strong_auth}
                    onChange={(e) => handleJwtInputChange('enforce_strong_auth', e.target.checked)}
                  />
                  Enforce Strong Authentication
                </label>
              </div>
            </div>

            <button
              className="system-btn system-btn-success"
              onClick={updateJwtConfig}
              disabled={isLoadingJwt}
            >
              Update JWT Configuration
            </button>
          </div>
        </div>
      )}

      {/* System Logs Section */}
      <div className="toggle-system-section">
        <button
          className="system-btn system-btn-primary"
          onClick={() => setShowLogsSection(!showLogsSection)}
        >
          {showLogsSection ? 'Hide' : 'Show'} System Logs
        </button>
      </div>

      {showLogsSection && (
        <div className="system-logs-section">
          <h3 className="section-title">System Logs</h3>

          <div className="system-controls">
            <button
              className="system-btn system-btn-primary"
              onClick={refreshLogs}
              disabled={isLoadingLogs}
            >
              Refresh Logs
            </button>
            <button
              className="system-btn system-btn-danger"
              onClick={clearLogs}
              disabled={logs.length === 0}
            >
              Clear Logs
            </button>
          </div>

          <div className="logs-container">
            {isLoadingLogs ? (
              <div>Loading logs...</div>
            ) : logs.length > 0 ? (
              logs.map((log, index) => {
                let logClass = 'log-entry ';

                if (log.includes('ERROR')) {
                  logClass += 'error';
                } else if (log.includes('WARN')) {
                  logClass += 'warn';
                } else if (log.includes('INFO')) {
                  logClass += 'info';
                } else if (log.includes('DEBUG')) {
                  logClass += 'debug';
                }

                return (
                  <div key={index} className={logClass}>
                    {log}
                  </div>
                );
              })
            ) : (
              <div>No logs available.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemManagement;