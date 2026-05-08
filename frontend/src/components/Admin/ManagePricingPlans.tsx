import React, { useState, useEffect } from 'react';
import apiClient from '../../api/axiosInstance';
import '../../App.css';

interface PricingPlan {
  id: number;
  name: string;
  max_translation_count: number;
  price_for_max_translation_per_counts: number;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const ManagePricingPlans: React.FC = () => {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PricingPlan | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    max_translation_count: 10,
    price_for_max_translation_per_counts: 0,
    description: '',
    is_active: true
  });

  useEffect(() => {
    fetchPricingPlans();
  }, []);

  const fetchPricingPlans = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/pricing/pricing-plans?active_only=false');
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching pricing plans:', error);
      alert('Failed to fetch pricing plans');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingPlan) {
        // Update existing plan
        await apiClient.put(`/pricing/pricing-plans/${editingPlan.id}`, formData);
        alert('Pricing plan updated successfully');
      } else {
        // Create new plan
        await apiClient.post('/pricing/pricing-plans', formData);
        alert('Pricing plan created successfully');
      }
      
      // Reset form and refresh data
      setFormData({
        name: '',
        max_translation_count: 10,
        price_for_max_translation_per_counts: 0,
        description: '',
        is_active: true
      });
      setEditingPlan(null);
      setShowForm(false);
      fetchPricingPlans();
    } catch (error: any) {
      console.error('Error saving pricing plan:', error);
      alert(`Failed to ${editingPlan ? 'update' : 'create'} pricing plan: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleEdit = (plan: PricingPlan) => {
    setEditingPlan(plan);
    setFormData({
      name: plan.name,
      max_translation_count: plan.max_translation_count,
      price_for_max_translation_per_counts: plan.price_for_max_translation_per_counts,
      description: plan.description,
      is_active: plan.is_active
    });
    setShowForm(true);
  };

  const handleDelete = async (planId: number) => {
    if (!window.confirm('Are you sure you want to delete this pricing plan? This action cannot be undone.')) {
      return;
    }

    try {
      await apiClient.delete(`/pricing/pricing-plans/${planId}`);
      alert('Pricing plan deleted successfully');
      fetchPricingPlans();
    } catch (error: any) {
      console.error('Error deleting pricing plan:', error);
      alert(`Failed to delete pricing plan: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const val = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? Number(val) : val
    }));
  };

  if (loading) return <div className="loading-spinner">Loading pricing plans...</div>;

  return (
    <div className="card documents-list" style={{ background: 'var(--gradient-card)', border: '1px solid var(--color-border)' }}>
      <div className="card-header d-flex justify-content-between align-items-center" style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '15px', marginBottom: '20px' }}>
        <h2 className="mb-0" style={{ color: 'var(--color-text-heading)', margin: 0 }}>Pricing Plans Management</h2>
        <button 
          className="form-button"
          style={{ 
            background: showForm ? 'var(--color-bg-medium)' : 'var(--gradient-primary)',
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            color: 'white',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s ease'
          }}
          onClick={() => {
            setEditingPlan(null);
            setFormData({
              name: '',
              max_translation_count: 10,
              price_for_max_translation_per_counts: 0,
              description: '',
              is_active: true
            });
            setShowForm(!showForm);
          }}
        >
          {showForm ? (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
              </svg> Cancel
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
              </svg> Add New Plan
            </>
          )}
        </button>
      </div>
      <div className="card-body">
        {showForm && (
          <form onSubmit={handleSubmit} style={{ 
            padding: '20px', 
            border: '1px solid var(--color-border)', 
            borderRadius: '12px', 
            marginBottom: '20px',
            background: 'rgba(15, 23, 42, 0.6)'
          }}>
            <h3 style={{ color: 'var(--color-text-heading)', marginBottom: '20px' }}>{editingPlan ? 'Edit Plan' : 'Create New Plan'}</h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Plan Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid var(--color-border)', 
                    borderRadius: '6px',
                    background: '#1E293B',
                    color: 'var(--color-text-primary)'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Max Translation Count *</label>
                <input
                  type="number"
                  name="max_translation_count"
                  value={formData.max_translation_count}
                  onChange={handleInputChange}
                  min="0"
                  required
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid var(--color-border)', 
                    borderRadius: '6px',
                    background: '#1E293B',
                    color: 'var(--color-text-primary)'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Price for Max Count ($)</label>
                <input
                  type="number"
                  name="price_for_max_translation_per_counts"
                  value={formData.price_for_max_translation_per_counts}
                  onChange={handleInputChange}
                  min="0"
                  step="0.01"
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid var(--color-border)', 
                    borderRadius: '6px',
                    background: '#1E293B',
                    color: 'var(--color-text-primary)'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Description *</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    border: '1px solid var(--color-border)', 
                    borderRadius: '6px',
                    background: '#1E293B',
                    color: 'var(--color-text-primary)'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({...prev, is_active: e.target.checked}))}
                  id="isActiveCheckbox"
                  style={{ marginRight: '8px', accentColor: 'var(--color-accent-dark)' }}
                />
                <label htmlFor="isActiveCheckbox" style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>
                  Is Active?
                </label>
              </div>
            </div>
            
            <div style={{ marginTop: '20px' }}>
              <button type="submit" className="form-button" style={{ 
                background: 'var(--gradient-primary)', 
                padding: '12px 24px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                color: 'white',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                  <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                </svg> {editingPlan ? 'Update Plan' : 'Create Plan'}
              </button>
            </div>
          </form>
        )}

        <div className="table-responsive" style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse', 
            background: '#1E293B',
            borderRadius: '12px',
            overflow: 'hidden',
            border: '1px solid var(--color-border)'
          }}>
            <thead>
              <tr style={{ background: 'var(--gradient-primary)', color: 'white' }}>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>ID</th>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>Name</th>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>Max Translation Count</th>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>Price for Max Count</th>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>Description</th>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>Active</th>
                <th style={{ padding: '16px', textAlign: 'left', fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {plans.length > 0 ? (
                plans.map((plan, index) => (
                  <tr key={plan.id} style={{ 
                    background: index % 2 === 0 ? 'transparent' : 'rgba(34, 211, 238, 0.05)',
                    borderBottom: '1px solid var(--color-border)',
                    transition: 'background 0.2s ease'
                  }}>
                    <td style={{ padding: '16px', color: 'var(--color-text-primary)' }}>{plan.id}</td>
                    <td style={{ padding: '16px', color: 'var(--color-text-heading)', fontWeight: 600 }}>{plan.name}</td>
                    <td style={{ padding: '16px', color: 'var(--color-text-primary)' }}>{plan.max_translation_count.toLocaleString()}</td>
                    <td style={{ padding: '16px', color: 'var(--color-accent-dark)', fontWeight: 600 }}>${plan.price_for_max_translation_per_counts.toFixed(2)}</td>
                    <td style={{ padding: '16px', color: 'var(--color-text-secondary)' }}>{plan.description}</td>
                    <td style={{ padding: '16px' }}>
                      <span style={{ 
                        padding: '6px 12px', 
                        borderRadius: '20px', 
                        fontSize: '12px', 
                        fontWeight: 600,
                        background: plan.is_active ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)' : 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
                        color: 'white'
                      }}>
                        {plan.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          style={{
                            padding: '8px 12px',
                            background: 'var(--gradient-primary)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            color: 'white',
                            fontSize: '13px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                            transition: 'all 0.2s ease'
                          }}
                          onClick={() => handleEdit(plan)}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.652-.652l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                          </svg> Edit
                        </button>
                        <button 
                          style={{
                            padding: '8px 12px',
                            background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            color: 'white',
                            fontSize: '13px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                            transition: 'all 0.2s ease'
                          }}
                          onClick={() => handleDelete(plan.id)}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                            <path fillRule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                          </svg> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)' }}>
                    No pricing plans found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ManagePricingPlans;
