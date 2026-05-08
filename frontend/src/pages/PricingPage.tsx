import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface PricingPlan {
  id: number;
  name: string;
  description: string;
  price: number;
  period: string;
  maxTranslations: number;
  features: string[];
  popular?: boolean;
}

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-green-500 mr-2" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

const PricingPage: React.FC = () => {
  const [loadingPlan, setLoadingPlan] = useState<number | null>(null);

  const pricingPlans: PricingPlan[] = [
    {
      id: 1,
      name: 'Free Trial',
      description: '1-day free trial with limited translations',
      price: 0,
      period: 'per count',
      maxTranslations: 10,
      features: [
        '10 image translations',
        'Basic translation quality',
        'Email support'
      ]
    },
    {
      id: 2,
      name: 'Basic',
      description: 'Basic plan with standard translation allowance',
      price: 9.99,
      period: 'per count',
      maxTranslations: 100,
      features: [
        '100 image translations',
        'Standard translation quality',
        'Priority email support',
        'Early access to new features'
      ]
    },
    {
      id: 3,
      name: 'Professional',
      description: 'Professional plan with higher translation limits',
      price: 29.99,
      period: 'per count',
      maxTranslations: 1000,
      features: [
        '1000 image translations',
        'Premium translation quality',
        '24/7 chat support',
        'Advanced customization options'
      ],
      popular: true
    },
    {
      id: 4,
      name: 'Enterprise',
      description: 'Enterprise plan with highest translation limits',
      price: 99.99,
      period: 'per count',
      maxTranslations: 10000,
      features: [
        '10000 image translations',
        'Premium translation quality',
        '24/7 phone support',
        'Custom integrations',
        'Dedicated account manager'
      ]
    }
  ];

  const handleSelectPlan = async (planId: number) => {
    setLoadingPlan(planId);
    try {
      // Call backend to select the plan
      const response = await fetch(`/pricing/select-plan/${planId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to select plan');
      }

      const data = await response.json();
      alert(data.message);
    } catch (error: any) {
      console.error('Plan selection error:', error);
      alert(`Error selecting plan: ${error.message}`);
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className="container mx-auto py-12 px-4">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Select a plan that fits your translation needs.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
        {pricingPlans.map((plan) => (
          <Card
            key={plan.id}
            className={`flex flex-col ${
              plan.popular ? 'border-2 border-blue-500 transform scale-105' : ''
            }`}
          >
            {plan.popular && (
              <div className="bg-blue-900 text-white text-center py-1 text-sm font-semibold">
                MOST POPULAR
              </div>
            )}
            <CardHeader className="text-center">
              <CardTitle>{plan.name}</CardTitle>
              <CardDescription>{plan.description}</CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold">${plan.price}</span>
                <span className="text-gray-500">/{plan.period}</span>
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {plan.maxTranslations.toLocaleString()} images/month
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <ul className="space-y-2">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <CheckIcon />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                className="w-full"
                onClick={() => handleSelectPlan(plan.id)}
                disabled={loadingPlan === plan.id}
              >
                {loadingPlan === plan.id ? 'Processing...' : 'Select Plan'}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default PricingPage;