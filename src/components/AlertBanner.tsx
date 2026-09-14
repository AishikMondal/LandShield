import { useEffect, useState } from 'react';
import { BellOff, BellRing, X } from 'lucide-react';
import { streamAlerts, type AlertEvent } from '@/api/client';
import { riskColorStr } from '@/lib/risk';

export function AlertBanner() {
  const [alert, setAlert] = useState<AlertEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const [notifyEnabled, setNotifyEnabled] = useState(false);

  useEffect(() => {
    const s = streamAlerts(ev => {
      setAlert(ev);
      try {
        if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
          new Notification(ev.title, { body: `${ev.location_name} · ${ev.risk_level} ${ev.risk_score}/100\n${ev.message}` });
        }
      } catch {
        /* browser refused */
      }
    }, setConnected);
    return () => s.close();
  }, []);

  const enableNotify = async () => {
    try {
      if (typeof Notification === 'undefined') return;
      const p = await Notification.requestPermission();
      setNotifyEnabled(p === 'granted');
    } catch {
      /* ignore */
    }
  };

  return (
    <>
      <div className="fixed top-16 right-4 z-[900] flex items-center gap-1.5 rounded-full border border-[#1E293B] bg-[#0B0F17]/90 backdrop-blur px-3 py-1.5 text-[9px] font-mono">
        <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
        <span className={`uppercase tracking-wider ${connected ? 'text-emerald-300' : 'text-amber-300'}`}>{connected ? 'Alerts live' : 'Alerts connecting'}</span>
        {!notifyEnabled && typeof Notification !== 'undefined' && Notification.permission !== 'granted' && (
          <button onClick={enableNotify} className="ml-1 text-slate-400 hover:text-slate-200"><BellRing className="w-3 h-3" /></button>
        )}
      </div>

      {alert && (
        <div className={`fixed top-20 right-4 z-[900] w-[340px] max-w-[calc(100vw-2rem)] rounded-xl border-2 p-4 shadow-2xl backdrop-blur-md animate-[slideIn_.25s_ease-out]`}
          style={{ borderColor: riskColorStr(alert.risk_level), background: 'rgba(11,15,23,0.95)' }}>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[10px] font-mono uppercase tracking-widest opacity-70">Live alert · {new Date(alert.created_at).toLocaleTimeString()}</p>
              <h3 className="text-sm font-bold mt-0.5" style={{ color: riskColorStr(alert.risk_level) }}>{alert.title}</h3>
            </div>
            <button onClick={() => setAlert(null)} className="shrink-0 rounded p-1 text-slate-400 hover:text-slate-200"><X className="w-4 h-4" /></button>
          </div>
          <p className="text-xs text-slate-300 mt-2 font-semibold">{alert.location_name} · {alert.risk_score}/100</p>
          <p className="text-[11px] text-slate-400 mt-1 leading-relaxed line-clamp-4">{alert.message}</p>
          {alert.primary_factors?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {alert.primary_factors.slice(0, 3).map((f, i) => <span key={i} className="text-[8px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">{f}</span>)}
            </div>
          )}
          <div className="flex items-center gap-2 mt-3 text-[9px] text-slate-500">
            <BellOff className="w-3 h-3" /> Dismiss to acknowledge.
          </div>
        </div>
      )}
    </>
  );
}