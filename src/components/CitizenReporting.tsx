import { FormEvent, useEffect, useRef, useState } from 'react';
import { Upload, MapPin, Camera, CheckCircle2, Clock, FileImage, Loader2, XCircle } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';
import { API_BASE, getReports, submitReport, verifyReport, type CitizenReportApi } from '@/api/client';

const hazardTypes = ['Pavement Cracking', 'Debris on Road', 'Retaining Wall Bulge', 'Active Mudflow', 'Rockfall', 'Ground Subsidence'];
const severities = ['minor', 'moderate', 'major', 'severe'] as const;

export function CitizenReporting() {
  const [reports, setReports] = useState<CitizenReportApi[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [hazard, setHazard] = useState(hazardTypes[0]);
  const [severity, setSeverity] = useState<(typeof severities)[number]>('moderate');
  const [description, setDescription] = useState('');
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = () => getReports().then(r => setReports(r.reports)).catch(() => setReports([]));
  useEffect(() => { refresh(); }, []);

  const locate = () => {
    setStatus('');
    if (!navigator.geolocation) { setStatus('Browser geolocation is unavailable.'); return; }
    navigator.geolocation.getCurrentPosition(
      p => setCoords({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => setStatus('Location permission was denied or unavailable.'),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!coords) { setStatus('Capture your device location before submitting.'); return; }
    setSubmitting(true); setStatus('');
    const form = new FormData();
    form.set('latitude', String(coords.lat)); form.set('longitude', String(coords.lon));
    form.set('hazard_type', hazard); form.set('severity', severity); form.set('description', description);
    form.set('reporter_type', 'RESIDENT'); if (file) form.set('image', file);
    try {
      await submitReport(form); setDescription(''); setFile(null); setStatus('Report stored as UNVERIFIED evidence.'); await refresh();
    } catch (e) { setStatus(e instanceof Error ? e.message : 'Report submission failed.'); }
    finally { setSubmitting(false); }
  };

  return (
    <section id="citizen-reporting" className="relative py-20 px-4 lg:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2"><Camera className="w-4 h-4 text-blue-400" /><span className="text-[11px] font-semibold text-blue-400 uppercase tracking-widest">Section 05</span><div className="h-px flex-1 max-w-[80px] bg-gradient-to-r from-blue-500/30 to-transparent" /></div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">Field & Citizen Incident Portal</h2>
          <p className="text-sm text-slate-400 mt-2 max-w-2xl">Geo-tagged observations are persisted as <span className="text-amber-300">unverified evidence</span> until an authority reviews them. They are never treated as ground truth automatically.</p>
        </div>

        <div className="grid lg:grid-cols-[1fr_1.15fr] gap-6">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-4"><h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide">Submit Field Report</h3><button onClick={() => setShowForm(v => !v)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/15 border border-blue-500/40 text-blue-300 text-xs font-semibold hover:bg-blue-500/25"><Upload className="w-3.5 h-3.5" />New Report</button></div>
            {!showForm && <div className="border border-dashed border-slate-700 rounded-xl p-8 text-center"><FileImage className="w-7 h-7 text-slate-600 mx-auto mb-3" /><p className="text-sm text-slate-300">Open a report to capture GPS, observation type and optional evidence image.</p></div>}
            {showForm && (
              <form onSubmit={onSubmit} className="space-y-4">
                <div><label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Device GPS</label><div className="flex gap-2 mt-1.5"><div className="flex-1 px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-700/50 font-mono text-xs text-emerald-400 flex items-center gap-2"><MapPin className="w-3.5 h-3.5" />{coords ? `${coords.lat.toFixed(5)}, ${coords.lon.toFixed(5)}` : 'Not captured'}</div><button type="button" onClick={locate} className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300">Use GPS</button></div></div>
                <div><label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Hazard Type</label><div className="grid grid-cols-2 gap-2 mt-1.5">{hazardTypes.map(h => <button type="button" key={h} onClick={() => setHazard(h)} className={`px-2.5 py-2 rounded-lg text-xs font-medium border ${hazard===h?'bg-blue-500/15 border-blue-500/40 text-blue-300':'bg-slate-800/30 border-slate-700/50 text-slate-400'}`}>{h}</button>)}</div></div>
                <div><label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Severity</label><div className="grid grid-cols-4 gap-2 mt-1.5">{severities.map(s => <button type="button" key={s} onClick={() => setSeverity(s)} className={`px-2 py-2 rounded-lg text-xs capitalize border ${severity===s?'bg-amber-500/15 border-amber-500/40 text-amber-300':'bg-slate-800/30 border-slate-700/50 text-slate-400'}`}>{s}</button>)}</div></div>
                <div><label className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Observation</label><textarea value={description} onChange={e=>setDescription(e.target.value)} maxLength={1000} className="mt-1.5 w-full min-h-24 rounded-lg bg-slate-900/50 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500/60" placeholder="Describe cracks, debris movement, water seepage or other visible evidence." /></div>
                <div><input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={e=>setFile(e.target.files?.[0] || null)} /><button type="button" onClick={()=>fileRef.current?.click()} className="w-full border border-dashed border-slate-700 rounded-lg p-3 text-xs text-slate-400 hover:border-blue-500/40"><FileImage className="w-4 h-4 inline mr-2" />{file ? file.name : 'Attach JPG/PNG/WebP evidence (max 10MB)'}</button></div>
                {status && <p className="text-xs text-amber-300">{status}</p>}
                <button disabled={submitting} className="w-full py-2.5 rounded-lg bg-blue-500/20 border border-blue-500/40 text-blue-300 text-sm font-semibold disabled:opacity-50">{submitting ? <span className="inline-flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" />Saving</span> : 'Submit Unverified Report'}</button>
              </form>
            )}
          </GlassCard>

          <div><h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wide mb-4">Stored Reports</h3>{reports.length===0 ? <GlassCard className="p-8 text-center"><p className="text-sm text-slate-500">No persisted reports yet. Submit one to test the pipeline.</p></GlassCard> : <div className="space-y-3">{reports.map(r => <ReportCard key={r.id} report={r} onChanged={refresh} />)}</div>}</div>
        </div>
      </div>
    </section>
  );
}

function ReportCard({ report, onChanged }: { report: CitizenReportApi; onChanged: () => void }) {
  const sev: Record<string,string>={minor:'text-emerald-400',moderate:'text-yellow-400',major:'text-orange-400',severe:'text-red-400'};
  const [working, setWorking] = useState(false);
  const [message, setMessage] = useState('');
  const runVerify = async (status: 'VERIFIED' | 'REJECTED' | 'UNVERIFIED') => {
    setWorking(true); setMessage('');
    try { await verifyReport(report.id, status); onChanged(); }
    catch (e) { setMessage(e instanceof Error ? e.message : 'Verification failed'); }
    finally { setWorking(false); }
  };
  const verified = report.verification_status === 'VERIFIED';
  const rejected = report.verification_status === 'REJECTED';
  const statusTone = verified ? 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10' : rejected ? 'text-red-300 border-red-500/30 bg-red-500/10' : 'text-amber-300 border-amber-500/30 bg-amber-500/10';
  return (
    <GlassCard className="p-4">
      <div className="flex gap-4">
        {report.image_path ? <img src={`${API_BASE}${report.image_path}`} alt="Citizen evidence" className="w-16 h-16 rounded-lg object-cover border border-slate-700" /> : <div className="w-16 h-16 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center"><Camera className="w-5 h-5 text-slate-600" /></div>}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-mono text-slate-500">FR-{String(report.id).padStart(4,'0')}</span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-bold border ${statusTone}`}>
              {verified ? <CheckCircle2 className="w-2.5 h-2.5" /> : rejected ? <XCircle className="w-2.5 h-2.5" /> : <Clock className="w-2.5 h-2.5" />}
              {report.verification_status}
            </span>
          </div>
          <p className="text-sm font-semibold text-slate-200 mt-1">{report.hazard_type}</p>
          <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{report.description || 'No description provided.'}</p>
          <div className="flex flex-wrap gap-3 mt-2 text-[10px] text-slate-500">
            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}</span>
            <span>{new Date(report.created_at).toLocaleString()}</span>
            <span className={`font-bold capitalize ${sev[report.severity] || 'text-slate-400'}`}>{report.severity}</span>
          </div>
          {report.verification_status === 'UNVERIFIED' && (
            <div className="flex items-center gap-2 mt-2">
              <button disabled={working} onClick={() => runVerify('VERIFIED')} className="inline-flex items-center gap-1 px-2 py-1 rounded border border-emerald-500/40 bg-emerald-500/10 text-[9px] font-semibold text-emerald-300 disabled:opacity-50">
                <CheckCircle2 className="w-2.5 h-2.5" /> Verify evidence
              </button>
              <button disabled={working} onClick={() => runVerify('REJECTED')} className="inline-flex items-center gap-1 px-2 py-1 rounded border border-red-500/40 bg-red-500/10 text-[9px] font-semibold text-red-300 disabled:opacity-50">
                <XCircle className="w-2.5 h-2.5" /> Reject
              </button>
              {message && <span className="text-[9px] text-amber-300">{message}</span>}
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
