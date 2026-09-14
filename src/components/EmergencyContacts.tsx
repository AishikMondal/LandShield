import { useEffect, useState } from 'react';
import { Phone, MessageSquare, Shield, Users, MapPin, AlertTriangle } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';
import { getAlerts, type AlertRow } from '@/api/client';

const emergencyContacts = [
  { name: 'SDRF Sikkim Command Centre', phone: '+91 3592 280 999', region: 'Gangtok, Sikkim', type: 'sdrf' },
  { name: 'NDRF 1st Bn (Guwahati)', phone: '+91 361 260 1192', region: 'Guwahati, Assam', type: 'ndrf' },
  { name: 'SDRF Meghalaya', phone: '+91 364 222 5500', region: 'Shillong, Meghalaya', type: 'sdrf' },
  { name: 'Emergency Hotline (All India)', phone: '112', region: 'Universal Emergency Number', type: 'universal' },
];

export function EmergencyContacts() {
  const [alerts,setAlerts]=useState<AlertRow[]>([]);
  const [streamClients,setStreamClients]=useState(0);
  const refresh=()=>getAlerts().then(r=>{setAlerts(r.alerts);setStreamClients(r.stream_clients);}).catch(()=>setAlerts([]));
  useEffect(()=>{refresh();},[]);
  return <section id="emergency" className="relative py-20 px-4 lg:px-6"><div className="max-w-7xl mx-auto">
    <div className="mb-8"><div className="flex items-center gap-2 mb-2"><AlertTriangle className="w-4 h-4 text-red-400" /><span className="text-[11px] font-semibold text-red-400 uppercase tracking-widest">Section 06</span><div className="h-px flex-1 max-w-[80px] bg-gradient-to-r from-red-500/30 to-transparent" /></div><h2 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">Emergency Response & Alert State</h2><p className="text-sm text-slate-400 mt-2 max-w-3xl">Risk assessments above the configured threshold create deduplicated alert records. External SMS is intentionally not claimed until a real provider is configured.</p></div>
    <div className="grid lg:grid-cols-[1fr_1fr] gap-6">
      <div><h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-4">Reference Contacts — verify before operational use</h3><div className="grid sm:grid-cols-2 gap-3">{emergencyContacts.map((c,i)=><GlassCard key={i} className="p-4"><div className="flex gap-3"><div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center"><Shield className="w-5 h-5 text-blue-400" /></div><div><p className="text-sm font-semibold text-slate-200">{c.name}</p><p className="text-[10px] text-slate-500 mt-1 flex gap-1"><MapPin className="w-3 h-3" />{c.region}</p><a href={`tel:${c.phone.replace(/\s/g,'')}`} className="flex items-center gap-1.5 mt-2 text-sm font-mono font-bold text-blue-300"><Phone className="w-3.5 h-3.5" />{c.phone}</a></div></div></GlassCard>)}</div></div>
      <GlassCard className="p-5"><h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-4 flex items-center gap-2"><MessageSquare className="w-4 h-4 text-blue-400" />Persisted Alerts</h3><p className="text-[9px] text-slate-500 mb-3">Browsers currently connected to the realtime stream: <span className="text-emerald-300 font-mono">{streamClients}</span> — use the Broadcast Console to deliver to them.</p>{alerts.length===0?<div className="p-6 text-center rounded-lg bg-slate-900/40 border border-slate-700/50"><Users className="w-6 h-6 text-slate-600 mx-auto mb-2" /><p className="text-xs text-slate-500">No alert records yet. A risk result at/above the backend threshold will create one.</p></div>:<div className="space-y-3 max-h-80 overflow-y-auto pr-1">{alerts.map(a=><div key={a.id} className="p-3 rounded-lg bg-slate-900/40 border border-slate-700/50"><div className="flex items-center justify-between gap-2"><span className={`text-[10px] font-bold ${a.risk_level==='CRITICAL'?'text-red-400':a.risk_level==='HIGH'?'text-orange-400':a.risk_level==='MODERATE'?'text-yellow-400':'text-emerald-400'}`}>{a.risk_level} · {a.risk_score}</span><span className="text-[9px] font-mono text-slate-500">{a.status} · {a.channel}</span></div><p className="text-xs text-slate-300 mt-2 leading-relaxed">{a.message}</p><div className="flex items-center justify-between mt-3"><span className="text-[9px] text-slate-600">{new Date(a.created_at).toLocaleString()}</span><span className="text-[9px] font-mono text-slate-600">{a.latitude.toFixed(3)}, {a.longitude.toFixed(3)}</span></div></div>)}</div>}<p className="text-[9px] text-slate-600 mt-4">Alerts are created with an idempotent dedupe key (zone + level + score bucket) and a cooldown window.</p></GlassCard>
    </div>
  </div></section>;
}
