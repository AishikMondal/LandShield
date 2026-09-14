import { useEffect, useState } from 'react';
import { BellRing, CheckCircle2, Loader2, Radio, Send } from 'lucide-react';
import { broadcastAlert, getAlerts, streamAlerts, type AlertEvent, type AlertRow, type RiskLevel } from '@/api/client';
import { riskColorStr } from '@/lib/risk';

interface AlertBroadcastProps {
  disabled?: boolean;
}

export function AlertBroadcast({ disabled }: AlertBroadcastProps) {
  const [locationName, setLocationName] = useState('Gangtok, East Sikkim');
  const [lat, setLat] = useState(27.3314);
  const [lng, setLng] = useState(88.6139);
  const [level, setLevel] = useState<RiskLevel>('HIGH');
  const [message, setMessage] = useState('');
  const [factors, setFactors] = useState(['Heavy rainfall accumulation', 'Steep terrain']);
  const [history, setHistory] = useState<AlertRow[]>([]);
  const [result, setResult] = useState<{ status: string; note: string; connected: number; delivered: number } | null>(null);
  const [sending, setSending] = useState(false);
  const [streamConnected, setStreamConnected] = useState(false);
  const [liveEvents, setLiveEvents] = useState<AlertEvent[]>([]);

  useEffect(() => {
    const s = streamAlerts(ev => setLiveEvents(e => [ev, ...e].slice(0, 8)), setStreamConnected);
    getAlerts().then(r => setHistory(r.alerts)).catch(() => setHistory([]));
    return () => s.close();
  }, []);

  const send = async () => {
    setSending(true);
    setResult(null);
    try {
      const r = await broadcastAlert({
        latitude: lat,
        longitude: lng,
        location_name: locationName,
        risk_level: level,
        risk_score: level === 'CRITICAL' ? 89 : level === 'HIGH' ? 68 : level === 'MODERATE' ? 45 : 22,
        message,
        primary_factors: factors,
      });
      setResult({
        status: r.status,
        note: r.message || '',
        connected: r.connected_clients,
        delivered: r.delivered_local ?? 0,
      });
      getAlerts().then(res => setHistory(res.alerts)).catch(() => undefined);
    } catch (e) {
      setResult({ status: 'error', note: e instanceof Error ? e.message : 'Failed', connected: 0, delivered: 0 });
    } finally {
      setSending(false);
    }
  };

  return (
    <section id="alert-broadcast" className="relative py-20 px-4 lg:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <BellRing className="w-4 h-4 text-red-400" />
            <span className="text-[11px] font-semibold text-red-400 uppercase tracking-widest">Section 03</span>
            <div className="h-px flex-1 max-w-[80px] bg-gradient-to-r from-red-500/30 to-transparent" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">Broadcast Alert Console</h2>
          <p className="text-sm text-slate-400 mt-2 max-w-3xl">
            Compose an official alert and deliver it to connected dashboards in real time over a local SSE channel.
            SMS/email adapters are <span className="text-amber-300">NOT_CONFIGURED</span> unless real credentials are provided — delivery is never faked.
          </p>
        </div>

        <div className="grid lg:grid-cols-[380px_1fr] gap-6">
          <div className="rounded-xl border border-[#1E293B] bg-[#0E141F]/85 backdrop-blur-md p-5 space-y-4">
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Location name</label>
              <input value={locationName} onChange={e => setLocationName(e.target.value)} maxLength={200} className="mt-1.5 w-full rounded-lg bg-slate-900/50 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-red-500/60" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Latitude</label>
                <input type="number" step="any" value={lat} onChange={e => setLat(Number(e.target.value))} className="mt-1.5 w-full rounded-lg bg-slate-900/50 border border-slate-700 px-3 py-2 font-mono text-xs text-emerald-300 outline-none focus:border-red-500/60" />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Longitude</label>
                <input type="number" step="any" value={lng} onChange={e => setLng(Number(e.target.value))} className="mt-1.5 w-full rounded-lg bg-slate-900/50 border border-slate-700 px-3 py-2 font-mono text-xs text-emerald-300 outline-none focus:border-red-500/60" />
              </div>
            </div>
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Risk level</label>
              <div className="grid grid-cols-4 gap-2 mt-1.5">
                {(['LOW', 'MODERATE', 'HIGH', 'CRITICAL'] as RiskLevel[]).map(l => (
                  <button key={l} type="button" onClick={() => setLevel(l)} className={`px-1 py-2 rounded-lg text-[10px] font-bold border ${level === l ? '' : 'bg-slate-800/30 border-slate-700/50 text-slate-500'}`} style={level === l ? { background: `${riskColorStr(l)}22`, borderColor: riskColorStr(l), color: riskColorStr(l) } : undefined}>{l}</button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Message (optional)</label>
              <textarea value={message} onChange={e => setMessage(e.target.value)} maxLength={2000} placeholder="Leave empty to auto-compose from location + level." className="mt-1.5 w-full min-h-20 rounded-lg bg-slate-900/50 border border-slate-700 px-3 py-2 text-xs text-slate-200 outline-none focus:border-red-500/60" />
            </div>
            <div>
              <label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Primary factors</label>
              <input
                value={factors.join('; ')}
                onChange={e => setFactors(e.target.value.split(';').map(s => s.trim()).filter(Boolean))}
                placeholder="Rain; Slope"
                className="mt-1.5 w-full rounded-lg bg-slate-900/50 border border-slate-700 px-3 py-2 text-xs text-slate-200 outline-none focus:border-red-500/60"
              />
            </div>

            <button onClick={send} disabled={sending || disabled} className="w-full py-2.5 rounded-lg bg-red-500/20 border border-red-500/40 text-red-300 text-sm font-semibold hover:bg-red-500/30 disabled:opacity-50 flex items-center justify-center gap-2">
              {sending ? <><Loader2 className="w-4 h-4 animate-spin" />Broadcasting…</> : <><Send className="w-4 h-4" />Broadcast Alert</>}
            </button>

            <div className={`flex items-center gap-2 text-[10px] rounded-lg border px-3 py-2 ${streamConnected ? 'text-emerald-300 border-emerald-500/30 bg-emerald-500/5' : 'text-amber-300 border-amber-500/30 bg-amber-500/5'}`}>
              <Radio className="w-3.5 h-3.5" /> SSE channel: {streamConnected ? 'connected' : 'connecting…'} (open this page in another tab/window to see broadcast delivery there)
            </div>

            {result && (
              <div className={`rounded-lg border p-3 text-xs ${result.status === 'deduplicated' ? 'border-amber-500/30 bg-amber-500/5 text-amber-200' : result.status === 'error' ? 'border-red-500/30 bg-red-500/5 text-red-200' : 'border-emerald-500/30 bg-emerald-500/5 text-emerald-200'}`}>
                <div className="flex items-center gap-2 font-semibold"><CheckCircle2 className="w-3.5 h-3.5" />{result.status.toUpperCase()}</div>
                <p className="mt-1 text-[10px] text-slate-400">{result.note}</p>
                <p className="mt-1 text-[10px] text-slate-500">connected clients: {result.connected} · delivered locally: {result.delivered}</p>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-[#1E293B] bg-[#0E141F]/85 backdrop-blur-md p-5">
              <h3 className="text-xs font-semibold text-slate-200 mb-3 flex items-center gap-1.5"><Radio className="w-3.5 h-3.5 text-red-400" /> Real-time alert feed (this browser)</h3>
              {liveEvents.length === 0 ? (
                <p className="text-[10px] text-slate-500">Waiting for alerts… broadcast one from the console to see it stream here instantly.</p>
              ) : (
                <ul className="space-y-2">
                  {liveEvents.map(ev => (
                    <li key={ev.alert_id} className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-bold" style={{ color: riskColorStr(ev.risk_level) }}>{ev.title}</span>
                        <span className="text-[9px] text-slate-500">{new Date(ev.created_at).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-[10px] text-slate-300 mt-1">{ev.location_name} · {ev.latitude.toFixed(4)}, {ev.longitude.toFixed(4)} · {ev.risk_score}/100</p>
                      <p className="text-[10px] text-slate-400 mt-1 line-clamp-2">{ev.message}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-xl border border-[#1E293B] bg-[#0E141F]/85 backdrop-blur-md p-5">
              <h3 className="text-xs font-semibold text-slate-200 mb-3">Stored alert history</h3>
              {history.length === 0 ? (
                <p className="text-[10px] text-slate-500">No persisted alerts yet.</p>
              ) : (
                <ul className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                  {history.map(a => (
                    <li key={a.id} className="flex items-center justify-between gap-2 text-[10px] border-b border-slate-800 pb-1.5">
                      <span className="truncate">
                        <span className="font-bold" style={{ color: riskColorStr(a.risk_level) }}>{a.risk_level}</span>
                        <span className="text-slate-500"> · {a.message.slice(0, 60)}</span>
                      </span>
                      <span className="font-mono text-slate-500 whitespace-nowrap">{a.created_at.slice(11, 19)} · {a.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}