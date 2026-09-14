export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical';

export interface RiskZone {
  id: string;
  name: string;
  district: string;
  state: string;
  lat: number;
  lng: number;
  riskScore: number;
  riskLevel: RiskLevel;
  rainfall24h: number;
  soilMoisture: number;
  predictedFailureRisk: number;
  polygon: [number, number][];
}

export interface ModelFeature {
  label: string;
  percentage: number;
  detail: string;
}

export interface HourlyPoint {
  time: string;
  rainfall24: number;
  rainfall72: number;
  soilMoisture: number;
  isForecast: boolean;
}

export interface ImpactItem {
  icon: 'road' | 'settlement' | 'hospital' | 'bridge';
  label: string;
  detail: string;
  severity: RiskLevel;
}
