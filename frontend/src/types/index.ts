export interface User {
    id: number;
    email: string;
    full_name: string;
    role: string;
    is_active: boolean;
    daily_usage: number;
    daily_limit: number;
    total_usage: number;
    plan_name: string;
    plan_total_limit: number;
    account_expires: string | null;
    created_at: string;
    deactivated_at: string | null;
    cancelled_user_id: number | null;
}

export interface PurchaseRequest {
    subscription_id: number;
    user_id: number;
    user_email: string;
    plan_id: number;
    plan_name: string;
    request_date: string;
    status: string;
}
