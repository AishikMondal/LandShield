import type { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  glow?: boolean;
  delay?: number;
  id?: string;
}

export function GlassCard({ children, className = '', glow = false, delay = 0, id }: GlassCardProps) {
  return (
    <div
      id={id}
      className={`bg-[#0E141F]/80 backdrop-blur-md border border-[#1E293B] rounded-xl ${glow ? 'shadow-[0_0_40px_rgba(59,130,246,0.06)]' : ''} ${className}`}
      style={{ animation: `fade-in-up 0.6s ease-out ${delay}s both` }}
    >
      {children}
    </div>
  );
}

interface RiskBadgeProps {
  level: 'low' | 'moderate' | 'high' | 'critical';
  score?: number;
  pulse?: boolean;
  size?: 'sm' | 'md';
}

export function RiskBadge({ level, score, pulse = false, size = 'sm' }: RiskBadgeProps) {
  const colors: Record<string, { bg: string; text: string; border: string; dot: string }> = {
    critical: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/40', dot: 'bg-red-500' },
    high: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/40', dot: 'bg-orange-500' },
    moderate: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', border: 'border-yellow-500/40', dot: 'bg-yellow-500' },
    low: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/40', dot: 'bg-emerald-500' },
  };
  const c = colors[level];
  const labels = { critical: 'CRITICAL', high: 'HIGH', moderate: 'MODERATE', low: 'LOW' };
  const padding = size === 'md' ? 'px-3 py-1.5 text-xs' : 'px-2 py-1 text-[10px]';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md font-bold tracking-wide border ${c.bg} ${c.text} ${c.border} ${padding} ${pulse ? 'animate-pulse' : ''}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {labels[level]}{score !== undefined && ` ${score}`}
    </span>
  );
}

interface SectionHeaderProps {
  eyebrow: string;
  title: string;
  subtitle?: string;
  icon?: ReactNode;
}

export function SectionHeader({ eyebrow, title, subtitle, icon }: SectionHeaderProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-2">
        {icon && <span className="text-blue-400">{icon}</span>}
        <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-widest">{eyebrow}</span>
        <div className="h-px flex-1 max-w-[80px] bg-gradient-to-r from-blue-500/30 to-transparent" />
      </div>
      <h2 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">{title}</h2>
      {subtitle && <p className="text-sm text-slate-400 mt-2 max-w-2xl leading-relaxed">{subtitle}</p>}
    </div>
  );
}

export function MetricBadge({ value, label, sublabel }: { value: string; label: string; sublabel?: string }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-3 rounded-lg bg-[#0E141F]/60 border border-[#1E293B] backdrop-blur-sm min-w-[140px]">
      <span className="text-xl font-bold font-mono text-blue-400">{value}</span>
      <span className="text-[10px] text-slate-300 font-medium mt-1 text-center">{label}</span>
      {sublabel && <span className="text-[9px] text-slate-500 mt-0.5 text-center">{sublabel}</span>}
    </div>
  );
}
