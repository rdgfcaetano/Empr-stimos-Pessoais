const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export type User = { id: number; name: string; email: string; role: "admin" | "partner"; is_active: boolean };
export type Client = { id: number; partner_id: number; name: string; phone: string; address?: string; notes?: string; created_at: string };
export type Loan = {
  id: number; client_id: number; partner_id: number; principal: string; interest_rate: string; interest_type: "monthly" | "daily" | "both";
  loan_date: string; due_date: string; late_fee: string; late_interest_rate: string; status: "open" | "paid" | "overdue" | "renegotiated";
  totals?: { interest: string; updated_value: string; late_fee: string; late_interest: string; paid: string; total_due: string; days_late: number };
};
export type Payment = { id: number; loan_id: number; responsible_user_id: number; responsible_user_name?: string; paid_at: string; amount: string; notes?: string; created_at: string };
export type Dashboard = { total_loaned: string; total_received: string; profit: string; client_count: number; active_loan_count: number; overdue_count: number; monthly: any[] };

export function token() {
  return localStorage.getItem("token");
}

export function setSession(accessToken: string, user: User) {
  localStorage.setItem("token", accessToken);
  localStorage.setItem("user", JSON.stringify(user));
}

export function currentUser(): User | null {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

export function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Erro inesperado" }));
    throw new Error(error.detail || "Erro inesperado");
  }
  return response.json();
}

export const brl = (value: string | number) =>
  Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
