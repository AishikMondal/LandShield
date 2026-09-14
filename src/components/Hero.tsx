import { Shield, Activity, MapPin, ChevronRight, Database, AlertTriangle } from 'lucide-react';
import { MetricBadge } from './ui/GlassCard';
import { riskZones } from '@/data/mockData';
import { riskColor } from '@/lib/risk';

interface HeroProps { onLaunchCommand: () => void; }

export function Hero({ onLaunchCommand }: HeroProps) {
  return (
    <section className="relative min-h-screen flex flex-col justify-center pt-20 pb-12 px-4 lg:px-6">
      <div className="max-w-7xl mx-auto w-full relative z-10">
        <div className="mb-6 flex items-center gap-3 px-4 py-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 backdrop-blur-sm animate-fade-in-up">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-200/90"><span className="font-bold">Prototype transparency:</span> live APIs are used where available; missing sensor/model inputs are explicitly marked as fallback or unavailable.</p>
        </div>

        <div className="max-w-4xl">
          <div className="flex items-center gap-2 mb-4 animate-fade-in-up"><div className="px-2.5 py-1 rounded-md bg-slate-800/50 border border-slate-700 text-[10px] font-semibold text-slate-400 tracking-wider uppercase">SIH26001 · Landslide Risk Intelligence</div></div>
          <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold text-slate-50 tracking-tight leading-[1.1] animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            Data → Models → Risk
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-blue-300 to-emerald-400 mt-1">Impact → Action</span>
            <span className="block text-xl md:text-2xl lg:text-3xl font-semibold text-slate-400 mt-3">for the North Eastern Region</span>
          </h1>
          <p className="text-sm md:text-base text-slate-400 mt-6 max-w-3xl leading-relaxed animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            An operational prototype that combines real coordinate selection, public weather/terrain/GIS data, supplied ML artifacts, explainable provenance and nearby-asset exposure. Unsupported sensor inputs are never presented as live readings.
          </p>
        </div>

        <div className="flex flex-wrap gap-3 mt-8 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-[#0E141F]/60 border border-[#1E293B] backdrop-blur-sm"><MapPin className="w-4 h-4 text-blue-400" /><div><span className="text-sm font-bold text-slate-100">Click-anywhere GIS</span><p className="text-[9px] text-slate-500 mt-0.5">Coordinate-driven analysis</p></div></div>
          <MetricBadge value="3" label="Usable supplied models" sublabel="Model 4 safely excluded" />
          <MetricBadge value="LIVE" label="Weather + DEM + OSM" sublabel="Graceful fallbacks" />
          <MetricBadge value="SQLite" label="Reports + Alerts" sublabel="Persistent local demo" />
        </div>

        <div className="flex flex-wrap items-center gap-3 mt-8 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
          <button onClick={onLaunchCommand} className="group flex items-center gap-2 px-5 py-3 rounded-xl bg-blue-500/20 border border-blue-500/50 text-blue-200 text-sm font-semibold hover:bg-blue-500/30 hover:border-blue-400 transition-all backdrop-blur-sm"><Shield className="w-4 h-4" />Launch Command Center<ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" /></button>
          <button onClick={() => document.querySelector('#ai-models')?.scrollIntoView({ behavior: 'smooth' })} className="flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-300 text-sm font-medium hover:bg-slate-800 hover:text-slate-100 transition-all"><Activity className="w-4 h-4" />Inspect Model Stack</button>
        </div>

        <div className="mt-10">
          <div className="flex items-center gap-2 mb-3"><Database className="w-3.5 h-3.5 text-amber-400" /><p className="text-[10px] uppercase tracking-widest text-slate-500">Dataset/demo reference zones — click to re-analyze with current data</p></div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
            {riskZones.map(zone => { const color=riskColor(zone.riskLevel); return <div key={zone.id} className="group p-3 rounded-lg bg-[#0E141F]/50 border border-[#1E293B] backdrop-blur-sm hover:border-slate-600 transition-all cursor-pointer" onClick={onLaunchCommand}><div className="flex items-center justify-between mb-1"><span className="text-[9px] font-mono text-slate-500">{zone.id}</span><div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} /></div><p className="text-[10px] text-slate-300 font-medium truncate">{zone.name}</p><div className="flex items-center justify-between mt-1.5"><span className="text-xs font-mono text-slate-500">demo {zone.riskScore}</span><span className="text-[8px] text-slate-600">{zone.state.slice(0,4).toUpperCase()}</span></div></div>})}
          </div>
        </div>
      </div>

      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 opacity-50"><span className="text-[9px] text-slate-500 uppercase tracking-widest">Scroll to Explore</span><div className="w-5 h-9 rounded-full border border-slate-700 flex justify-center pt-1.5"><div className="w-1 h-1.5 rounded-full bg-slate-500 animate-bounce" /></div></div>
    </section>
  );
}
