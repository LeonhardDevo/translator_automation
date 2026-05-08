import React, { useState, useEffect, useMemo } from 'react';
import apiClient from '../../api/axiosInstance';
import './PurchaseRequests.css';
import type { PurchaseRequest } from '../../types';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { FiRefreshCw, FiClock, FiCheckCircle, FiXCircle, FiClipboard, FiInbox, FiCheck, FiX } from 'react-icons/fi';

const ITEMS_PER_PAGE = 10;

const PurchaseRequests: React.FC = () => {
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [confirmAction, setConfirmAction] = useState<{ id: number; action: 'approve' | 'reject' } | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchPurchaseRequests();
  }, []);

  const fetchPurchaseRequests = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/pricing/admin/purchase-requests');
      setRequests(response.data);
    } catch (error) {
      console.error('Error fetching purchase requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (subscriptionId: number) => {
    setConfirmAction(null);
    try {
      const response = await apiClient.post(`/pricing/admin/approve-subscription/${subscriptionId}`);

      if (response.status === 200) {
        // Refresh the list
        await fetchPurchaseRequests();
        alert('[SUCCESS] Subscription approved successfully! The user can now use their plan.');
      } else {
        const errorData = response.data;
        alert(`[ERROR] Error: ${errorData.detail}`);
      }
    } catch (error: any) {
      console.error('Error approving subscription:', error);
      alert(`[ERROR] Error approving subscription: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleReject = async (subscriptionId: number) => {
    setConfirmAction(null);
    try {
      const response = await apiClient.post(`/pricing/admin/reject-subscription/${subscriptionId}`);

      if (response.status === 200) {
        // Refresh the list
        await fetchPurchaseRequests();
        alert('[ERROR] Subscription rejected. The user has been notified.');
      } else {
        const errorData = response.data;
        alert(`[ERROR] Error: ${errorData.detail}`);
      }
    } catch (error: any) {
      console.error('Error rejecting subscription:', error);
      alert(`[ERROR] Error rejecting subscription: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const filteredRequests = useMemo(() => {
    return requests.filter(request => {
      if (filter === 'all') return true;
      if (filter === 'pending') return request.status === 'pending_payment';
      if (filter === 'approved') return request.status === 'active';
      if (filter === 'rejected') return request.status === 'rejected';
      return true;
    });
  }, [requests, filter]);

  // Pagination Logic
  const totalPages = Math.ceil(filteredRequests.length / ITEMS_PER_PAGE);
  const paginatedRequests = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredRequests.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredRequests, currentPage]);

  const handleFilterChange = (newFilter: 'all' | 'pending' | 'approved' | 'rejected') => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  if (loading) {
    return (
      <div className="purchase-requests-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading purchase requests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="purchase-requests-container">
      <div className="requests-header">
        <div>
          <h2 className="requests-title">Purchase Requests</h2>
          <p className="requests-subtitle">
            Review and approve client purchase requests after verifying physical payment
          </p>
        </div>
        <button className="refresh-btn" onClick={fetchPurchaseRequests} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FiRefreshCw /> Refresh
        </button>
      </div>

      <div className="filter-tabs">
        <button
          className={`filter-tab ${filter === 'pending' ? 'active' : ''}`}
          onClick={() => handleFilterChange('pending')}
        >
          <span className="tab-icon"><FiClock /></span>
          Pending
          <span className="tab-badge">{requests.filter(r => r.status === 'pending_payment').length}</span>
        </button>
        <button
          className={`filter-tab ${filter === 'approved' ? 'active' : ''}`}
          onClick={() => handleFilterChange('approved')}
        >
          <span className="tab-icon"><FiCheckCircle /></span>
          Approved
          <span className="tab-badge">{requests.filter(r => r.status === 'active').length}</span>
        </button>
        <button
          className={`filter-tab ${filter === 'rejected' ? 'active' : ''}`}
          onClick={() => handleFilterChange('rejected')}
        >
          <span className="tab-icon"><FiXCircle /></span>
          Rejected
          <span className="tab-badge">{requests.filter(r => r.status === 'rejected').length}</span>
        </button>
        <button
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => handleFilterChange('all')}
        >
          <span className="tab-icon"><FiClipboard /></span>
          All
          <span className="tab-badge">{requests.length}</span>
        </button>
      </div>

      {paginatedRequests.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"><FiInbox size={48} /></div>
          <h3>No {filter !== 'all' ? filter : ''} purchase requests</h3>
          <p>Purchase requests will appear here when clients select pricing plans</p>
        </div>
      ) : (
        <>
          <div className="pagination-info" style={{ marginBottom: '10px', color: 'var(--color-text-secondary)', textAlign: 'right' }}>
            Showing {paginatedRequests.length} of {filteredRequests.length} requests
          </div>

          <div className="requests-grid">
            {paginatedRequests.map((request) => (
              <div
                key={request.subscription_id}
                className={`request-card ${request.status === 'pending_payment' ? 'pending' : request.status}`}
              >
                <div className="card-header">
                  <div className="user-info">
                    <div className="user-avatar">
                      {request.user_email.charAt(0).toUpperCase()}
                    </div>
                    <div className="user-details">
                      <h4 className="user-email">{request.user_email}</h4>
                      <p className="user-id">User ID: #{request.user_id}</p>
                    </div>
                  </div>
                  <div className={`status-badge ${request.status}`}>
                    {request.status === 'pending_payment' ? <><FiClock className="inline mr-1" /> Pending</> :
                      request.status === 'active' ? <><FiCheckCircle className="inline mr-1" /> Approved</> :
                        request.status === 'rejected' ? <><FiXCircle className="inline mr-1" /> Rejected</> : request.status}
                  </div>
                </div>

                <div className="card-body">
                  <div className="plan-info">
                    <div className="info-row">
                      <span className="info-label">Plan:</span>
                      <span className="info-value plan-name">{request.plan_name}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Request Date:</span>
                      <span className="info-value">{getTimeAgo(request.request_date)}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Full Date:</span>
                      <span className="info-value">{new Date(request.request_date).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="card-footer">
                  {request.status === 'pending_payment' ? (
                    <div className="action-buttons">
                      <button
                        className="approve-btn"
                        onClick={() => setConfirmAction({ id: request.subscription_id, action: 'approve' })}
                      >
                        <FiCheck className="inline" /> Approve
                      </button>
                      <button
                        className="reject-btn"
                        onClick={() => setConfirmAction({ id: request.subscription_id, action: 'reject' })}
                      >
                        <FiX className="inline" /> Reject
                      </button>
                    </div>
                  ) : (
                    <div className="action-disabled">
                      <span>No actions available</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '20px', alignItems: 'center' }}>
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{
                  padding: '8px 16px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                  cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.3s ease',
                  background: currentPage === 1 ? 'var(--color-bg-medium)' : 'var(--gradient-primary)',
                  color: currentPage === 1 ? 'var(--color-text-muted)' : 'white',
                  opacity: currentPage === 1 ? 0.6 : 1
                }}
              >
                <FaChevronLeft /> Prev
              </button>

              <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Page {currentPage} of {totalPages}
              </span>

              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                style={{
                  padding: '8px 16px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '8px',
                  cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.3s ease',
                  background: currentPage === totalPages ? 'var(--color-bg-medium)' : 'var(--gradient-primary)',
                  color: currentPage === totalPages ? 'var(--color-text-muted)' : 'white',
                  opacity: currentPage === totalPages ? 0.6 : 1
                }}
              >
                Next <FaChevronRight />
              </button>
            </div>
          )}
        </>
      )}

      {/* Confirmation Modal */}
      {confirmAction && (
        <div className="modal-overlay" onClick={() => setConfirmAction(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm {confirmAction.action === 'approve' ? 'Approval' : 'Rejection'}</h3>
            <p>
              {confirmAction.action === 'approve'
                ? '[WARNING] Are you sure you want to approve this subscription? Make sure you have received the payment from the client.'
                : '[WARNING] Are you sure you want to reject this subscription request?'}
            </p>
            <div className="modal-actions">
              <button
                className="modal-cancel-btn"
                onClick={() => setConfirmAction(null)}
              >
                Cancel
              </button>
              <button
                className={confirmAction.action === 'approve' ? 'modal-approve-btn' : 'modal-reject-btn'}
                onClick={() =>
                  confirmAction.action === 'approve'
                    ? handleApprove(confirmAction.id)
                    : handleReject(confirmAction.id)
                }
              >
                {confirmAction.action === 'approve' ? 'Confirm Approval' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchaseRequests;
