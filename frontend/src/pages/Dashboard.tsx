import React, { useState, useEffect } from 'react';
import { useUser } from '../contexts/UserContext';
import UsageMeter from '../components/Dashboard/UsageMeter';
import ImageTranslator from '../components/ImageTranslator';
import UserManagement from '../components/Admin/UserManagement';
import PricingAnalytics from '../components/Admin/PricingAnalytics';
import PurchaseRequests from '../components/Admin/PurchaseRequests';
import Modal from '../components/Modal';

const Dashboard: React.FC = () => {
  const { state, dispatch } = useUser();
  const [isAdminView, setIsAdminView] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);

  useEffect(() => {
    // Check if current user is admin and update view accordingly
    if (state.user?.role === 'admin') {
      setIsAdminView(true);
    }
  }, [state.user]);

  // Fetch usage data if not already loaded
  useEffect(() => {
    const fetchUsage = async () => {
      if (!state.usage) {
        try {
          const response = await fetch('/pricing/usage', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          });
          const data = await response.json();
          dispatch({ type: 'SET_USAGE', payload: data });
        } catch (error) {
          console.error('Error fetching usage:', error);
        }
      }
    };

    fetchUsage();
  }, [state.usage, dispatch]);

  // Check if user has reached their limit and show modal if needed
  useEffect(() => {
    if (state.usage && state.usage.remaining <= 0) {
      setShowLimitModal(true);
    }
  }, [state.usage]);

  const handleCloseModal = () => {
    setShowLimitModal(false);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {isAdminView ? (
        <div>
          <h2 className="text-2xl font-semibold mb-6">Admin Dashboard</h2>

          <PricingAnalytics />

          <div className="mt-8">
            <h3 className="text-xl font-medium mb-4">Purchase Requests</h3>
            <PurchaseRequests />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
            <div>
              <h3 className="text-xl font-medium mb-4">User Management</h3>
              <UserManagement />
            </div>

            <div>
              <h3 className="text-xl font-medium mb-4">Pricing Plans</h3>
              <div className="bg-white p-6 rounded-lg border">
                <p>Manage pricing plans and their features here.</p>
                <button className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                  Manage Plans
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            <div className="lg:col-span-2">
              <h2 className="text-2xl font-semibold mb-4">Translate Documents</h2>
              <ImageTranslator />
            </div>

            <div>
              <h2 className="text-2xl font-semibold mb-4">Usage</h2>
              <UsageMeter usage={state.usage} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-xl font-medium mb-4">Account Information</h3>
            <p>Email: {state.user?.email}</p>
            <p>Status: {state.user?.is_active ? 'Active' : 'Inactive'}</p>
          </div>
        </div>
      )}

      {/* Limit exceeded modal */}
      <Modal
        isOpen={showLimitModal}
        onClose={handleCloseModal}
        title="Limit Reached"
      >
        <div className="text-center py-4">
          <p className="text-lg mb-4">
            You have reached your translation limit for this billing cycle.
          </p>
          <p className="mb-6">
            Please purchase a new plan to continue using our translation services.
          </p>
          <a
            href="/pricing"
            className="inline-block bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            onClick={() => {
              // Close modal before navigating
              setTimeout(() => {
                window.location.href = '/pricing';
              }, 300);
            }}
          >
            Purchase New Plan
          </a>
        </div>
      </Modal>
    </div>
  );
};

export default Dashboard;