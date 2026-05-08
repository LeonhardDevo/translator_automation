import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FaBan, FaTrash, FaKey, FaChevronLeft, FaChevronRight, FaPlus } from 'react-icons/fa';
import apiClient from '../../api/axiosInstance';
import UserRow from './UserRow';
import type { User } from '../../types';
import './UserManagement.css';

interface UserManagementProps {
  onUserChange?: () => void;
}

const ITEMS_PER_PAGE = 10;

const UserManagement: React.FC<UserManagementProps> = ({ onUserChange }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [showDeletedUsers, setShowDeletedUsers] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  // Create User State
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');
  const [showPasswordInput, setShowPasswordInput] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [createdUserEmail, setCreatedUserEmail] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Edit User State
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editUserData, setEditUserData] = useState({
    email: '',
    full_name: '',
    account_expires: '',
    is_active: true
  });

  // Modal States
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [targetUserId, setTargetUserId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmDeleteText, setConfirmDeleteText] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/admin/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const notifyChange = useCallback(() => {
    if (onUserChange) onUserChange();
    fetchUsers();
  }, [onUserChange]);

  const toggleUserStatus = useCallback(async (userId: number, currentStatus: boolean) => {
    try {
      const user = users.find(u => u.id === userId);
      if (user && user.cancelled_user_id !== null) {
        alert('Cannot activate a deleted user.');
        return;
      }

      if (currentStatus) {
        await apiClient.delete(`/admin/users/${userId}`);
      } else {
        await apiClient.post(`/admin/users/${userId}/activate`);
      }
      notifyChange();
    } catch (error) {
      console.error('Failed to update user status:', error);
      alert('Failed to update user status');
    }
  }, [users, notifyChange]);

  const startEditUser = useCallback((user: User) => {
    setEditingUserId(user.id);
    setEditUserData({
      email: user.email,
      full_name: user.full_name || '',
      account_expires: user.account_expires || '',
      is_active: user.is_active
    });
  }, []);

  const handleEditChange = useCallback((field: string, value: string | boolean) => {
    setEditUserData(prev => ({ ...prev, [field]: value }));
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingUserId(null);
    setEditUserData({
      email: '',
      full_name: '',
      account_expires: '',
      is_active: true
    });
  }, []);

  const saveEditedUser = useCallback(async (userId: number) => {
    try {
      await apiClient.put(`/admin/users/${userId}`, editUserData);
      setEditingUserId(null);
      notifyChange();
    } catch (error) {
      console.error('Failed to update user:', error);
      alert('Failed to update user');
    }
  }, [editUserData, notifyChange]);

  // Create User Handlers
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);

    try {
      const passwordToUse = showPasswordInput ? newUserPassword : Math.random().toString(36).slice(-8) + 'Aa1!';
      await apiClient.post('/admin/users', {
        email: newUserEmail,
        full_name: newUserName,
        password: passwordToUse,
        role: newUserRole
      });

      setGeneratedPassword(passwordToUse);
      setCreatedUserEmail(newUserEmail);

      setNewUserName('');
      setNewUserEmail('');
      setNewUserPassword('');
      setNewUserRole('user');
      setShowPasswordInput(false);

      notifyChange();
    } catch (error: any) {
      console.error('Failed to create user:', error);
      alert(`Failed to create user: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Password Modal Handlers
  const openPasswordResetModal = useCallback((userId: number) => {
    setTargetUserId(userId);
    setNewPassword('');
    setShowPasswordModal(true);
  }, []);

  const closePasswordResetModal = () => {
    setShowPasswordModal(false);
    setTargetUserId(null);
    setNewPassword('');
  };

  const resetUserPassword = async () => {
    if (!targetUserId || !newPassword) {
      alert('Please provide a new password');
      return;
    }

    try {
      await apiClient.post(`/admin/users/${targetUserId}/reset-password`, {
        password: newPassword
      });
      alert('Password reset successfully');
      closePasswordResetModal();
    } catch (error: any) {
      console.error('Failed to reset password:', error);
      alert(`Failed to reset password: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Delete Handlers
  const openDeleteModal = useCallback((userId: number) => {
    setTargetUserId(userId);
    setConfirmDeleteText('');
    setShowDeleteModal(true);
  }, []);

  const closeDeleteModal = () => {
    setShowDeleteModal(false);
    setTargetUserId(null);
    setConfirmDeleteText('');
  };

  const deleteUser = async () => {
    if (!targetUserId) return;
    if (confirmDeleteText.toLowerCase() !== 'delete user') {
      alert('Please type "delete user" to confirm');
      return;
    }

    try {
      await apiClient.delete(`/admin/users/${targetUserId}/soft-delete`);
      alert('User deleted successfully');
      closeDeleteModal();
      notifyChange();
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      alert(`Failed to delete user: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Optimization: Filtered Users with useMemo
  const filteredUsers = useMemo(() => {
    if (showDeletedUsers) return users;
    return users.filter(user => user.cancelled_user_id === null);
  }, [users, showDeletedUsers]);

  // Optimization: Pagination
  const totalPages = Math.ceil(filteredUsers.length / ITEMS_PER_PAGE);
  const paginatedUsers = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredUsers.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredUsers, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  if (loading && users.length === 0) {
    return <div className="loading-spinner">Loading users...</div>;
  }

  // Custom button styles
  const createButtonStyle = (isActive: boolean): React.CSSProperties => ({
    padding: '10px 20px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.3s ease',
    background: isActive ? 'var(--color-bg-medium)' : 'var(--gradient-primary)',
    color: 'white',
    boxShadow: isActive ? 'none' : 'var(--shadow-primary)'
  });

  const paginationButtonStyle = (disabled: boolean): React.CSSProperties => ({
    padding: '8px 16px',
    border: '1px solid var(--color-border)',
    borderRadius: '8px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.3s ease',
    background: disabled ? 'var(--color-bg-medium)' : 'var(--gradient-primary)',
    color: disabled ? 'var(--color-text-muted)' : 'white',
    opacity: disabled ? 0.6 : 1
  });

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px 16px',
    border: '1px solid var(--color-border)',
    borderRadius: '8px',
    background: '#1E293B',
    color: 'var(--color-text-primary)',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.3s ease'
  };

  return (
    <div className="user-management-container">
      <div className="upload-section" style={{ width: '100%' }}>
        <h2 style={{ color: 'var(--color-text-heading)', marginBottom: '20px' }}>Create New User</h2>
        <button
          style={createButtonStyle(showCreateForm)}
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          <FaPlus /> {showCreateForm ? 'Cancel' : 'Create User'}
        </button>

        {showCreateForm && (
          <form onSubmit={handleCreateUser} style={{ marginTop: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '15px' }}>
              <div>
                <input
                  type="text"
                  placeholder="Full Name"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  required
                  style={inputStyle}
                />
              </div>

              <div>
                <input
                  type="email"
                  placeholder="Email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  required
                  style={inputStyle}
                />
              </div>

              <div>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  style={inputStyle}
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '15px' }}>
              <label className="toggle-label" style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                <span style={{ color: 'var(--color-text-primary)' }}>Set Password Manually</span>
                <div className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={showPasswordInput}
                    onChange={(e) => setShowPasswordInput(e.target.checked)}
                    id="manual-password-toggle"
                  />
                  <span className="toggle-slider"></span>
                </div>
              </label>
            </div>

            {showPasswordInput && (
              <div style={{ marginBottom: '15px' }}>
                <input
                  type="password"
                  placeholder="Password"
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  required={showPasswordInput}
                  style={inputStyle}
                />
              </div>
            )}

            <div style={{ textAlign: 'left', marginTop: '20px' }}>
              <button
                type="submit"
                disabled={isGenerating}
                style={{
                  padding: '12px 24px',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                  background: isGenerating ? 'var(--color-bg-medium)' : 'var(--gradient-primary)',
                  color: 'white',
                  opacity: isGenerating ? 0.7 : 1,
                  transition: 'all 0.3s ease'
                }}
              >
                {isGenerating ? 'Creating...' : 'Create User'}
              </button>
            </div>

            {generatedPassword && (
              <div className="stat-card" style={{ marginTop: '20px', border: '1px solid var(--color-accent-dark)' }}>
                <p style={{ color: 'var(--color-text-heading)', fontWeight: 600 }}>New User Created!</p>
                <p style={{ color: 'var(--color-text-primary)' }}><strong>Email:</strong> {createdUserEmail}</p>
                <p style={{ color: 'var(--color-accent-dark)' }}><strong>Password:</strong> {generatedPassword}</p>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>Please share this information securely with the user.</p>
              </div>
            )}
          </form>
        )}
      </div>

      <div className="documents-list" style={{ maxWidth: '100%', width: '100%', overflowX: 'auto', margin: '20px auto 0' }}>
        <h2 style={{ color: 'var(--color-text-heading)', marginBottom: '20px' }}>User Management</h2>
        <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '15px', justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <label className="toggle-label">
            <span style={{ color: 'var(--color-text-primary)' }}>Show Deleted Users</span>
            <div className="toggle-switch">
              <input
                type="checkbox"
                checked={showDeletedUsers}
                onChange={(e) => {
                  setShowDeletedUsers(e.target.checked);
                  setCurrentPage(1);
                }}
                id="show-deleted-users-toggle"
              />
              <span className="toggle-slider"></span>
            </div>
          </label>

          <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.9em' }}>
            Showing {paginatedUsers.length} of {filteredUsers.length} users
          </div>
        </div>

        <div className="table-responsive">
          <table className="user-management-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Name</th>
                <th>Status</th>
                <th>Daily Usage</th>
                <th>Plan / Total</th>
                <th className="actions-header">Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedUsers && paginatedUsers.length > 0 ? (
                paginatedUsers.map((user) => (
                  <UserRow
                    key={user.id}
                    user={user}
                    isEditing={editingUserId === user.id}
                    editUserData={editingUserId === user.id ? editUserData : undefined}
                    onStartEdit={startEditUser}
                    onEditChange={handleEditChange}
                    onSave={saveEditedUser}
                    onCancel={cancelEdit}
                    onToggleStatus={toggleUserStatus}
                    onResetPassword={openPasswordResetModal}
                    onDelete={openDeleteModal}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: 'var(--color-text-muted)' }}>No users found</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '20px', alignItems: 'center' }}>
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              style={paginationButtonStyle(currentPage === 1)}
            >
              <FaChevronLeft /> Prev
            </button>

            <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              style={paginationButtonStyle(currentPage === totalPages)}
            >
              Next <FaChevronRight />
            </button>
          </div>
        )}
      </div>

      {/* Password Reset Modal */}
      {showPasswordModal && (
        <div className="modal-overlay" onClick={closePasswordResetModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{ color: 'var(--color-text-heading)', marginBottom: '20px' }}>Reset User Password</h3>
            <div style={{ marginBottom: '20px' }}>
              <input
                type="password"
                placeholder="Enter new password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div className="modal-actions">
              <button 
                onClick={closePasswordResetModal}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                  background: 'var(--color-bg-medium)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <FaBan /> Cancel
              </button>
              <button 
                onClick={resetUserPassword}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'var(--gradient-primary)',
                  color: 'white',
                  cursor: 'pointer',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <FaKey /> Reset Password
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete User Modal */}
      {showDeleteModal && (
        <div className="modal-overlay" onClick={closeDeleteModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{ color: 'var(--color-text-heading)', marginBottom: '20px' }}>Delete User</h3>
            <p style={{ color: 'var(--color-text-primary)', marginBottom: '15px' }}>Are you sure you want to delete this user? This action cannot be undone.</p>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: '15px' }}>Type "delete user" to confirm:</p>
            <div style={{ marginBottom: '20px' }}>
              <input
                type="text"
                placeholder='Type "delete user" to confirm'
                value={confirmDeleteText}
                onChange={(e) => setConfirmDeleteText(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div className="modal-actions">
              <button 
                onClick={closeDeleteModal}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                  background: 'var(--color-bg-medium)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <FaBan /> Cancel
              </button>
              <button 
                onClick={deleteUser}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
                  color: 'white',
                  cursor: 'pointer',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <FaTrash /> Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
