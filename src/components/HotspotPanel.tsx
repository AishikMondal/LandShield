import { useCallback, useEffect, useState } from 'react';
import { Loader2, RefreshCcw } from 'lucide-react';
import { getHotspots, type HotspotItem } from '@/api/client';
import { riskColorStr } from '@/lib/risk';

interface HotspotPanelProps {
  onSelect: (lat: number, lng: number) => void;
  className?: string;
}

export function HotspotPanel({ onSelect, className = '' }: HotspotPanelProps) {
  const [hotspots, setHotspots] = useState<HotspotItem[]>([]);
  const [meta, setMeta] = useState({ status: 'idle', freshness: 'no data yet', total_candidates: 0, last_refresh: '' });
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async (force = false) => {
    setLoading(true);
    try {
      const p = await getHotspots(force);
      setHotspots(p.hotspots);
      setMeta({ status: p.status, freshness: p.freshness, total_candidates: p.total_candidates, last_refresh: p.last_refresh });
    } catch {
      setHotspots([]);
      setMeta(m => ({ ...m, status: 'error' }));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(false); }, [refresh]);

  return (
    <div className={`rounded-xl border border-[#1E293B] bg-[#0E141F]/85 backdrop-blur-md p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-xs font-semibold text-slate-200">Top-5 NER Hotspots</h3>
          <p className="text-[9px] text-slate-500 mt-0.5">{meta.status} · {meta.freshness}</p>
        </div>
        <button
          onClick={() => refresh(true)}
          disabled={loading}
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800/40 border border-slate-700 text-[10px] text-slate-300 hover:bg-slate-700/40 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCcw className="w-3 h-3" />} Refresh
        </button>
      </div>

      {hotspots.length === 0 ? (
        <p className="text-[10px] text-slate-500">
          {meta.status === 'refreshing'
            ? 'Backend is evaluating all NER candidates right now — this can take a couple of minutes on a congested public network.'
            : 'No hotspot data yet — trigger one refresh to evaluate all NER candidate towns.'}
        </p>
      ) : (
        <ul className="space-y-1.5">
          {hotspots.map(h => (
            <li key={h.rank}>
              <button onClick={() => onSelect(h.latitude, h.longitude)} className="w-full text-left rounded-lg bg-slate-900/40 border border-slate-800 hover:border-amber-500/40 p-2 transition-colors">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black font-mono text-[#0B0F17]" style={{ background: riskColorStr(h.risk_level) }}>{h.rank}</span>
                    <span className="text-[11px] text-slate-200 truncate">{h.location_name}</span>
                  </div>
                  <span className="font-mono text-[11px] font-bold" style={{ color: riskColorStr(h.risk_level) }}>{h.risk_score.toFixed(0)}</span>
                </div>
                <p className="text-[9px] text-slate-500 mt-1 pl-7 truncate">
                  {h.risk_level} · {h.state}
                  {h.primary_factors.length ? ` · ${h.primary_factors[0]}` : ''}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}