import React, { useState, useEffect, useMemo } from 'react';
import { FiGift, FiStar, FiAward, FiPackage, FiRefreshCw, FiCheck } from 'react-icons/fi';
import { FaCrown } from 'react-icons/fa';
import apiClient from '../../api/axiosInstance';
import './PricingCards.css';
import { useTranslation } from 'react-i18next';

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

const PricingCards: React.FC = () => {
    const { t } = useTranslation();
    const [plans, setPlans] = useState<PricingPlan[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
    const [processingPlanId, setProcessingPlanId] = useState<number | null>(null);

    useEffect(() => {
        fetchPricingPlans();
    }, []);

    const fetchPricingPlans = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await apiClient.get('/pricing/pricing-plans?active_only=true');
            setPlans(response.data);
        } catch (err: unknown) {
            console.error('Error fetching pricing plans:', err);
            setError(t('pricing.error_loading_plans'));
        } finally {
            setLoading(false);
        }
    };

    const handleSelectPlan = async (planId: number) => {
        setProcessingPlanId(planId);
        try {
            const response = await apiClient.post(`/pricing/select-plan/${planId}`);

            if (response.status === 200) {
                setSelectedPlanId(planId);
                alert(t('pricing.plan_selected_success'));
            }
        } catch (err: unknown) {
            console.error('Error selecting plan:', err);
            alert(`${t('common.error')}: ${t('pricing.plan_selection_failed')}`);
        } finally {
            setProcessingPlanId(null);
        }
    };

    const getMostPopularPlanIndex = (): number => {
        if (plans.length >= 3) {
            return 1;
        }
        return -1;
    };

    const mostPopularIndex = useMemo(() => getMostPopularPlanIndex(), [plans]);

    const getCardIcon = (planName: string): React.ReactNode => {
        const name = planName.toLowerCase();
        if (name.includes('free') || name.includes('trial')) {
            return <FiGift size={40} />;
        } else if (name.includes('basic')) {
            return <FiStar size={40} />;
        } else if (name.includes('pro') || name.includes('professional')) {
            return <FiAward size={40} />;
        } else if (name.includes('enterprise')) {
            return <FaCrown size={40} />;
        }
        return <FiPackage size={40} />;
    };

    if (loading) {
        return (
            <div className="pricing-cards-container">
                <div className="pricing-loading">
                    <div className="spinner"></div>
                    <p>{t('pricing.loading_plans')}</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="pricing-cards-container">
                <div className="pricing-error">
                    <p>{t('pricing.retry_loading')}</p>
                    <button onClick={fetchPricingPlans} className="retry-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                        <FiRefreshCw /> {t('pricing.retry')}
                    </button>
                </div>
            </div>
        );
    }

    if (plans.length === 0) {
        return (
            <div className="pricing-cards-container">
                <div className="pricing-empty">
                    <p>{t('pricing.no_plans_available')}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="pricing-cards-container">
            <div className="pricing-cards-grid">
                {plans.map((plan, index) => {
                    const isPopular = index === mostPopularIndex;
                    const isSelected = selectedPlanId === plan.id;
                    const isProcessing = processingPlanId === plan.id;

                    return (
                        <div
                            key={plan.id}
                            className={`pricing-card ${isPopular ? 'popular' : ''} ${isSelected ? 'selected' : ''}`}
                        >
                            {isPopular && (
                                <div className="popular-badge">
                                    ⭐ {t('pricing.most_popular')}
                                </div>
                            )}

                            <div className="pricing-card-header">
                                <div className="plan-icon">{getCardIcon(plan.name)}</div>
                                <h3 className="plan-name">{plan.name}</h3>
                                <p className="plan-description">{plan.description}</p>
                            </div>

                            <div className="pricing-card-price">
                                <div className="price-amount">
                                    <span className="currency">$</span>
                                    <span className="amount">{plan.price_for_max_translation_per_counts.toFixed(2)}</span>
                                </div>
                                <div className="price-period">{t('pricing.for_translations', { count: plan.max_translation_count })}</div>
                            </div>

                            <div className="pricing-card-features">
                                <ul>
                                    <li>
                                        <span className="check-icon"><FiCheck /></span>
                                        {plan.max_translation_count.toLocaleString()} {t('pricing.image_translations')}
                                    </li>
                                    <li>
                                        <span className="check-icon"><FiCheck /></span>
                                        {plan.price_for_max_translation_per_counts === 0 ? t('pricing.free_forever') : t('pricing.one_time_payment')}
                                    </li>
                                    <li>
                                        <span className="check-icon"><FiCheck /></span>
                                        {t('pricing.email_support')}
                                    </li>
                                    {isPopular && (
                                        <li>
                                            <span className="check-icon"><FiCheck /></span>
                                            {t('pricing.best_value')}
                                        </li>
                                    )}
                                </ul>
                            </div>

                            <div className="pricing-card-action">
                                <button
                                    className={`select-plan-btn ${isProcessing ? 'processing' : ''} ${isSelected ? 'selected' : ''}`}
                                    onClick={() => handleSelectPlan(plan.id)}
                                    disabled={isProcessing || isSelected}
                                >
                                    {isProcessing ? (
                                        <>
                                            <span className="btn-spinner"></span> {t('pricing.processing')}
                                        </>
                                    ) : isSelected ? (
                                        <><FiCheck className="mr-1 inline" /> {t('pricing.request_sent')}</>
                                    ) : (
                                        <>{t('pricing.select_plan')}</>
                                    )}
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default React.memo(PricingCards);
