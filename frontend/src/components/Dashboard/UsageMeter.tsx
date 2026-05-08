import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface Usage {
  current_usage: number;
  limit: number;
  remaining: number;
  reset_date: string;
}

interface UsageMeterProps {
  usage: Usage | null;
}

const UsageMeter: React.FC<UsageMeterProps> = ({ usage }) => {
  if (!usage) return null;

  const percentageUsed = Math.min(100, (usage.current_usage / usage.limit) * 100);
  const resetDate = new Date(usage.reset_date);
  const today = new Date();
  const daysUntilReset = Math.ceil(
    (resetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Usage</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-2">
          <div className="flex justify-between text-sm mb-1">
            <span>{usage.current_usage} used</span>
            <span>{usage.remaining} remaining</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className={`h-2.5 rounded-full ${
                percentageUsed > 80 ? 'bg-red-500' : 
                percentageUsed > 60 ? 'bg-yellow-500' : 'bg-green-500'
              }`} 
              style={{ width: `${percentageUsed}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0</span>
            <span>{usage.limit} translations</span>
          </div>
        </div>
        
        {percentageUsed >= 100 && (
          <div className="mt-3 p-2 bg-red-100 border border-red-300 rounded text-sm text-red-700">
            You have reached your usage limit. Please upgrade your plan.
          </div>
        )}
        {percentageUsed >= 80 && percentageUsed < 100 && (
          <div className="mt-3 p-2 bg-yellow-100 border border-yellow-300 rounded text-sm text-yellow-700">
            You're approaching your usage limit. Consider upgrading your plan.
          </div>
        )}
        
        <div className="mt-3 text-sm text-gray-600">
          Reset in {daysUntilReset} day{daysUntilReset !== 1 ? 's' : ''}
        </div>
      </CardContent>
    </Card>
  );
};

export default UsageMeter;