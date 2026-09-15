export type SourceType =
  | 'LIVE_API'
  | 'DEM_DERIVED'
  | 'GIS'
  | 'MODEL_DERIVED'
  | 'DATASET_DEFAULT'
  | 'PROXY_DERIVED'
  | 'USER_INPUT'
  | 'DEMO'
  | 'UNAVAILABLE'
  | 'SENSOR_UNAVAILABLE'
  | 'UNRESOLVED';

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type Exposure = 'HIGH' | 'MODERATE' | 'LOW';

export interface FactPoint {
  value: number | null;
  unit: string;
  source: string;
  source_type: SourceType;
  observed_at?: string | null;
  fallback_used?: boolean;
}

export interface SourceMeta extends FactPoint {
  feature: string;
  name?: string;
}

export interface ImpactedAsset {
  type: string;
  category?: string;
  name: string;
  latitude: number;
  longitude: number;
  distance_m: number;
  exposure?: Exposure;
  source?: string;
}

export interface ModelEvidenceEntry {
  label: string;
  value: number;
  status: string;
}

export interface ModelStatusInfo {
  loaded?: boolean;
  label?: string;
  note?: string;
  status: string;
  reason?: string | null;
  error?: string | null;
}

export interface FusionStatus {
  enabled: boolean;
  available: boolean;
  status: string;
  reason?: string | null;
}

export interface SlopeSensitivityRow {
  slope_angle: number;
  model_output_probability: number;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface SlopeSensitivityResponse {
  slope_sensitivity: SlopeSensitivityRow[];
  model_input_received: {
    feature: string;
    units: string;
    base_features_constant: boolean;
    static_terrain_inputs: string[];
    dynamic_inputs: string[];
  };
  note: string;
  terrain_source?: string | null;
  terrain_source_type?: string | null;
}

export interface RiskAssessment {
  location: {
    latitude: number;
    longitude: number;
    display_name?: string;
    district?: string | null;
    state?: string | null;
    country?: string | null;
    source?: string;
    source_type?: string;
  };
  risk_score: number;
  risk_level: RiskLevel;
  score_basis: string;
  confidence: number | null;
  prediction_horizon: string;
  factors: SourceMeta[];
  terrain: SourceMeta[];
  model_evidence: {
    model1?: ModelEvidenceEntry;
    model3?: ModelEvidenceEntry;
    earthquake_context?: unknown[];
  };
  model_status: Record<string, ModelStatusInfo>;
  fusion_status: FusionStatus;
  degraded_inputs: SourceMeta[];
  why_high_risk: string[];
  influence_radius_m: number;
  impacted_assets: ImpactedAsset[];
  earthquake_context: unknown[];
  recommended_actions: string[];
  model_outputs: Record<string, unknown>;
  provenance: Record<string, unknown>;
  generated_at: string;
  degraded: boolean;
  warnings: string[];
}

export interface HotspotItem {
  rank: number;
  latitude: number;
  longitude: number;
  location_name: string;
  district?: string | null;
  state?: string | null;
  risk_score: number;
  risk_level: RiskLevel;
  generated_at: string;
  data_freshness: string;
  primary_factors: string[];
}

export interface HotspotsPayload {
  status: string;
  last_refresh: string;
  refresh_interval_minutes: number;
  candidates_evaluated: number;
  total_candidates: number;
  hotspots: HotspotItem[];
  freshness: string;
}

export interface LocationAssets {
  latitude: number;
  longitude: number;
  query_radius_m: number;
  influence_policy: string;
  assets: ImpactedAsset[];
  total_found: number;
  source: string;
  source_type: SourceType | string;
}

export interface CitizenReportApi {
  id: number;
  latitude: number;
  longitude: number;
  hazard_type: string;
  severity: string;
  description: string;
  reporter_type: string;
  image_path?: string | null;
  verification_status: string;
  created_at: string;
}

export interface AlertRow {
  id: number;
  dedupe_key: string;
  latitude: number;
  longitude: number;
  risk_score: number;
  risk_level: RiskLevel;
  message: string;
  status: string;
  channel: string;
  created_at: string;
  sent_at?: string | null;
}

export interface AlertEvent {
  alert_id: number;
  title: string;
  message: string;
  location_name: string;
  latitude: number;
  longitude: number;
  risk_level: RiskLevel;
  risk_score: number;
  primary_factors: string[];
  status: string;
  created_at: string;
}

export interface BroadcastPayload {
  latitude: number;
  longitude: number;
  location_name: string;
  risk_level: RiskLevel;
  risk_score: number;
  message?: string;
  primary_factors?: string[];
}

export interface BroadcastResult {
  status: string;
  message?: string;
  alert_id?: number;
  alert?: AlertEvent | null;
  connected_clients: number;
  delivered_local?: number;
  sms?: string;
  email?: string;
  channels?: Record<string, Record<string, unknown>>;
  deduplicated?: boolean;
}

export interface Health {
  api: string;
  database: string;
  model_1: string;
  model_2: string;
  model_3: string;
  model_4: string;
  fusion: string;
  weather: string;
  elevation: string;
  osm: string;
  nominatim: string;
  realtime_alerts: string;
  alert_threshold: number;
  demand: { stream_clients: number };
  demo_mode: boolean;
  models: Record<string, ModelStatusInfo>;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function predictRisk(latitude: number, longitude: number) {
  return request<RiskAssessment>('/api/risk/predict', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ latitude, longitude }),
  });
}

export function simulateRisk(latitude: number, longitude: number, rainfallMultiplier: number, soilMoistureDelta: number) {
  return request<RiskAssessment>('/api/risk/simulate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude, longitude, rainfall_multiplier: rainfallMultiplier, soil_moisture_delta: soilMoistureDelta }),
  });
}

export function simulateSlopeRisk(latitude: number, longitude: number, slopeAngle: number) {
  return request<RiskAssessment>('/api/risk/simulate-slope', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude, longitude, slope_angle: slopeAngle }),
  });
}

export function getHotspots(force = false) {
  return request<HotspotsPayload>(`/api/risk/hotspots?force=${force ? 1 : 0}`);
}

export function getSlopeSensitivity(latitude: number, longitude: number) {
  return request<SlopeSensitivityResponse>(`/api/risk/slope-sensitivity?latitude=${latitude}&longitude=${longitude}`);
}

export function getLocationAssets(latitude: number, longitude: number, radiusM?: number) {
  const radius = radiusM ? `&radius_m=${radiusM}` : '';
  return request<LocationAssets>(`/api/location/assets?latitude=${latitude}&longitude=${longitude}${radius}`);
}

export async function getReports() {
  return request<{ reports: CitizenReportApi[] }>('/api/reports');
}

export async function submitReport(form: FormData) {
  return request<{ report: CitizenReportApi }>('/api/reports', { method: 'POST', body: form });
}

export async function verifyReport(id: number, status: 'VERIFIED' | 'REJECTED' | 'UNVERIFIED') {
  return request<{ report: CitizenReportApi }>(`/api/reports/${id}/verify`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
}

export async function getAlerts() {
  return request<{ alerts: AlertRow[]; stream_clients: number }>('/api/alerts');
}

export async function broadcastAlert(payload: BroadcastPayload) {
  return request<BroadcastResult>('/api/alerts/broadcast', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
}

export async function getModelsStatus() {
  return request<{ models: Record<string, ModelStatusInfo>; fusion: FusionStatus & ModelStatusInfo }>('/api/models/status');
}

export async function getHealth() {
  return request<Health>('/api/health');
}

export interface AlertStream {
  close: () => void;
  readyState: () => number;
}

export function streamAlerts(
  onAlert: (alert: AlertEvent) => void,
  onStatus?: (connected: boolean) => void,
): AlertStream {
  const source = new EventSource(`${API_BASE}/api/alerts/stream`);
  let connected = false;

  source.onopen = () => {
    connected = true;
    onStatus?.(true);
  };
  source.onerror = () => {
    if (connected) {
      connected = false;
      onStatus?.(false);
    }
  };
  source.addEventListener('alert', (event: MessageEvent<string>) => {
    try {
      onAlert(JSON.parse(event.data) as AlertEvent);
    } catch {
      /* ignore malformed events */
    }
  });

  return {
    close: () => source.close(),
    readyState: () => source.readyState,
  };
}

export { API_BASE };