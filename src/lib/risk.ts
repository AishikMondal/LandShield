import type { RiskLevel } from '@/types';

export function riskColor(level: RiskLevel): string {
  switch (level) {
    case 'critical': return '#EF4444';
    case 'high': return '#F97316';
    case 'moderate': return '#EAB308';
    case 'low': return '#10B981';
  }
}

export function riskColorStr(level: string): string {
  return riskColor((level || 'low').toLowerCase() as RiskLevel);
}

export function riskLabelStr(level: string): string {
  return (level || 'LOW').toUpperCase();
}

export function riskColorFromScore(score: number): string {
  if (score >= 80) return '#EF4444';
  if (score >= 55) return '#F97316';
  if (score >= 25) return '#EAB308';
  return '#10B981';
}

export function riskLevelFromScore(score: number): RiskLevel {
  if (score >= 80) return 'critical';
  if (score >= 55) return 'high';
  if (score >= 25) return 'moderate';
  return 'low';
}

export function riskLabel(level: RiskLevel): string {
  switch (level) {
    case 'critical': return 'CRITICAL';
    case 'high': return 'HIGH';
    case 'moderate': return 'MODERATE';
    case 'low': return 'LOW';
  }
}

export function riskGlow(level: RiskLevel): string {
  switch (level) {
    case 'critical': return 'shadow-[0_0_24px_rgba(239,68,68,0.5)]';
    case 'high': return 'shadow-[0_0_16px_rgba(249,115,22,0.35)]';
    case 'moderate': return 'shadow-[0_0_12px_rgba(234,179,8,0.25)]';
    case 'low': return 'shadow-[0_0_10px_rgba(16,185,129,0.2)]';
  }
}
