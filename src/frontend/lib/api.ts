export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export function isConnectionError(error: unknown): boolean {
  if (!error) return false;
  const msg = (error instanceof Error ? error.message : String(error)).toLowerCase();
  return (
    msg.includes('failed to fetch') ||
    msg.includes('networkerror') ||
    msg.includes('network error') ||
    msg.includes('connection refused') ||
    msg.includes('econnrefused') ||
    msg.includes('err_connection_refused') ||
    msg.includes('cannot reach backend') ||
    msg.includes('backend server is not running') ||
    msg.includes('fetch failed') ||
    msg.includes('load failed') ||
    msg.includes('network request failed')
  );
}

export function formatErrorMessage(error: unknown): string {
  if (isConnectionError(error)) {
    return 'Backend server is not running.';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return String(error || 'An unexpected error occurred.');
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
  } catch {
    throw new Error('Backend server is not running.');
  }
  if (!res.ok) {
    const err = await res.text().catch(() => 'Unknown error');
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch<{ status: string }>('/health'),
  metrics: () => apiFetch<MetricsResponse>('/metrics'),
  shipments: (params?: { limit?: number; offset?: number; priority?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    if (params?.priority) qs.set('priority', params.priority);
    return apiFetch<ShipmentListResponse>(`/shipments?${qs}`);
  },
  highRisk: () => apiFetch<{ total: number; shipments: Shipment[] }>('/shipments/high-risk?limit=20'),
  shipment: (id: string) => apiFetch<Shipment>(`/shipments/${id}`),
  fleet: () => apiFetch<FleetResponse>('/fleet'),
  predict: (body: PredictRequest) => apiFetch<PredictResponse>('/predict', { method: 'POST', body: JSON.stringify(body) }),
  optimize: (body?: { shipment_ids?: string[] }) => apiFetch<OptimizeResponse>('/optimize', { method: 'POST', body: JSON.stringify(body || {}) }),
  simulate: (body: SimulateRequest) => apiFetch<SimulateResponse>('/simulate', { method: 'POST', body: JSON.stringify(body) }),
  copilot: (message: string) => apiFetch<CopilotResponse>('/copilot', { method: 'POST', body: JSON.stringify({ message }) }),
};

// ── Types ─────────────────────────────────────────────────────────────────────

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type DeliveryStatus = 'ON_TIME' | 'AT_RISK' | 'DELAYED';

export interface Shipment {
  shipment_id: string;
  vehicle_id?: string;
  origin: string;
  destination: string;
  distance_km: number;
  cargo_weight_kg: number;
  priority: Priority;
  weather_severity: number;
  traffic_level: number;
  port_congestion: number;
  warehouse_delay_hours: number;
  supplier_risk: number;
  vehicle_utilization: number;
  historical_delay_hours: number;
  delivery_deadline_hours: number;
  actual_delay_hours: number;
  disruption: number;
  delivery_status: DeliveryStatus;
  risk_score?: number;
  risk_level?: RiskLevel;
  disruption_probability?: number;
  expected_delay_hours?: number;
}

export interface ShipmentListResponse {
  total: number;
  shipments: Shipment[];
}

export interface Vehicle {
  vehicle_id: string;
  vehicle_type: string;
  capacity_kg: number;
  current_location: string;
  availability: boolean;
  current_utilization: number;
  operating_cost_per_km: number;
  reliability_score: number;
}

export interface FleetResponse {
  total: number;
  available: number;
  vehicles: Vehicle[];
}

export interface PredictRequest {
  shipment_id?: string;
  weather_severity: number;
  traffic_level: number;
  port_congestion: number;
  warehouse_delay_hours: number;
  supplier_risk: number;
  vehicle_utilization: number;
  historical_delay_hours: number;
  delivery_deadline_hours: number;
  distance_km: number;
  cargo_weight_kg: number;
  priority: Priority;
}

export interface RiskFactor {
  factor: string;
  value: number;
  contribution: number;
  label: string;
}

export interface PredictResponse {
  shipment_id?: string;
  disruption_probability: number;
  expected_delay_hours: number;
  risk_score: number;
  risk_level: RiskLevel;
  risk_factors: RiskFactor[];
  recommended_action: string;
}

export interface Assignment {
  shipment_id: string;
  vehicle_id?: string;
  priority: string;
  estimated_cost: number;
  feasible: boolean;
  reason?: string;
}

export interface OptimizeResponse {
  assignments: Assignment[];
  unassigned_shipments: string[];
  total_estimated_cost: number;
  utilization_before: number;
  utilization_after: number;
  high_risk_reduced: number;
  solver_status: string;
  optimization_time_ms: number;
}

export interface SimulateRequest {
  weather_severity_delta: number;
  traffic_level_delta: number;
  port_congestion_delta: number;
  vehicle_unavailable_ids: string[];
}

export interface ScenarioMetrics {
  disruption_probability_avg: number;
  expected_delay_avg_hours: number;
  high_risk_count: number;
  critical_risk_count: number;
  estimated_fleet_cost: number;
  fleet_utilization_avg: number;
}

export interface SimulateResponse {
  current: ScenarioMetrics;
  simulated: ScenarioMetrics;
  delta: Record<string, number>;
  affected_shipments: number;
  simulation_label: string;
}

export interface CopilotResponse {
  answer: string;
  tools_used: { tool_name: string; arguments: Record<string, unknown>; result_summary: string }[];
  sources: string[];
  confidence: number;
}

export interface KPIMetrics {
  total_shipments: number;
  high_risk_count: number;
  critical_risk_count: number;
  on_time_rate: number;
  fleet_utilization_avg: number;
  avg_disruption_probability: number;
  avg_expected_delay_hours: number;
  disrupted_count: number;
  at_risk_count: number;
}

export interface MetricsResponse {
  kpis: KPIMetrics;
  risk_distribution: { risk_level: RiskLevel; count: number; percentage: number }[];
  delay_trend: { label: string; avg_delay_hours: number; disruption_rate: number }[];
  region_risk: { region: string; avg_risk_score: number; shipment_count: number }[];
}
