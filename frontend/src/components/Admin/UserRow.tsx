import React, { memo } from 'react';
import { FaEdit, FaTrash, FaBan, FaCheck, FaKey, FaInfinity } from 'react-icons/fa';
import type { User } from '../../types';

interface UserEditData {
    email: string;
    full_name: string;
    account_expires: string;
    is_active: boolean;
}

interface UserRowProps {
    user: User;
    isEditing: boolean;
    editUserData?: UserEditData;
    onEditChange: (field: keyof UserEditData, value: string | boolean) => void;
    onSave: (id: number) => void;
    onCancel: () => void;
    onStartEdit: (user: User) => void;
    onToggleStatus: (id: number, currentStatus: boolean) => void;
    onResetPassword: (id: number) => void;
    onDelete: (id: number) => void;
}

const UserRow: React.FC<UserRowProps> = ({
    user,
    isEditing,
    editUserData,
    onEditChange,
    onSave,
    onCancel,
    onStartEdit,
    onToggleStatus,
    onResetPassword,
    onDelete
}) => {

    if (isEditing && editUserData) {
        return (
            <tr>
                <td>{user.id}</td>
                <td>
                    <input
                        type="email"
                        value={editUserData.email}
                        onChange={(e) => onEditChange('email', e.target.value)}
                        className="form-input"
                        style={{ padding: '5px', fontSize: '14px', color: '#333' }}
                    />
                </td>
                <td>
                    <input
                        type="text"
                        value={editUserData.full_name}
                        onChange={(e) => onEditChange('full_name', e.target.value)}
                        className="form-input"
                        style={{ padding: '5px', fontSize: '14px', color: '#333' }}
                    />
                </td>
                <td>
                    <select
                        value={editUserData.is_active.toString()}
                        onChange={(e) => onEditChange('is_active', e.target.value === 'true')}
                        className="form-input"
                        style={{ padding: '5px', fontSize: '14px', color: '#333' }}
                    >
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                    </select>
                </td>
                <td>
                    <div>
                        {user.daily_usage}/{user.daily_limit}
                    </div>
                </td>
                <td>
                    <div>
                        <div style={{ fontWeight: 600, color: '#997E67' }}>{user.plan_name}</div>
                        <div style={{ fontSize: '0.8em', color: '#997E67' }}>
                            {user.total_usage}/{user.plan_total_limit > 0 ? user.plan_total_limit : <FaInfinity />} total
                        </div>
                    </div>
                </td>
                <td className="actions-cell">
                    <div className="action-buttons">
                        <button className="edit-btn" onClick={() => onSave(user.id)} title="Save">
                            <FaCheck /> <span className="btn-text">Save</span>
                        </button>
                        <button className="deactivate-btn" onClick={onCancel} title="Cancel">
                            <FaBan /> <span className="btn-text">Cancel</span>
                        </button>
                        <button className="edit-btn" onClick={() => onResetPassword(user.id)} title="Reset Password">
                            <FaKey /> <span className="btn-text">Reset Pwd</span>
                        </button>
                        <button className="deactivate-btn" onClick={() => onDelete(user.id)} title="Delete User">
                            <FaTrash /> <span className="btn-text">Delete</span>
                        </button>
                    </div>
                </td>
            </tr>
        );
    }

    return (
        <tr>
            <td>{user.id}</td>
            <td>{user.email}</td>
            <td>{user.full_name}</td>
            <td>
                <span className={`status-badge ${user.is_active ? 'status-completed' : 'status-failed'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                    {user.cancelled_user_id !== null && <span className="deleted-indicator"> (Deleted)</span>}
                </span>
            </td>
            <td>
                <div>
                    {user.daily_usage}/{user.daily_limit}
                </div>
            </td>
            <td>
                <div>
                    <div style={{ fontWeight: 600, color: '#997E67' }}>{user.plan_name}</div>
                    <div style={{ fontSize: '0.8em', color: '#997E67' }}>
                        {user.total_usage}/{user.plan_total_limit > 0 ? user.plan_total_limit : <FaInfinity />} total
                    </div>
                </div>
            </td>
            <td className="actions-cell">
                <div className="action-buttons">
                    <button className="edit-btn" onClick={() => onStartEdit(user)} title="Edit User">
                        <FaEdit /> <span className="btn-text">Edit</span>
                    </button>
                    <button
                        className={user.is_active ? 'deactivate-btn' : 'activate-btn'}
                        onClick={() => onToggleStatus(user.id, user.is_active)}
                        title={user.is_active ? 'Deactivate User' : 'Activate User'}
                        disabled={user.cancelled_user_id !== null}
                    >
                        {user.is_active ? <FaBan title="Deactivate" /> : <FaCheck title="Activate" />}
                        <span className="btn-text">{user.is_active ? 'Deactivate' : (user.cancelled_user_id !== null ? 'Cannot Activate' : 'Activate')}</span>
                    </button>
                    <button className="edit-btn" onClick={() => onResetPassword(user.id)} title="Reset Password">
                        <FaKey /> <span className="btn-text">Reset Pwd</span>
                    </button>
                    <button className="deactivate-btn" onClick={() => onDelete(user.id)} title="Delete User">
                        <FaTrash /> <span className="btn-text">Delete</span>
                    </button>
                </div>
            </td>
        </tr>
    );
};

export default memo(UserRow);
