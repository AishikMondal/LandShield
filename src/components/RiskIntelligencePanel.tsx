import { useEffect, useState } from 'react';
import {
  AlertTriangle, BrainCircuit, Database, Loader2, MapPin, Radar, Satellite, ShieldCheck, Zap,
} from 'lucide-react';
import { getSlopeSensitivity, simulateRisk, simulateSlopeRisk, type RiskAssessment, type SlopeSensitivityResponse, type SourceType } from '@/api/client';
import { riskColor, riskGlow, riskLabel } from '@/lib/risk';
import type { RiskLevel as DisplayLevel } from '@/types';

const sourceTone: Record<SourceType, string> = {
  LIVE_API: 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10',
  DEM_DERIVED: 'text-cyan-300 border-cyan-500/30 bg-cyan-500/10',
  GIS: 'text-teal-300 border-teal-500/30 bg-teal-500/10',
  MODEL_DERIVED: 'text-blue-300 border-blue-500/30 bg-blue-500/10',
  PROXY_DERIVED: 'text-amber-300 border-amber-500/30 bg-amber-500/10',
  DATASET_DEFAULT: 'text-orange-300 border-orange-500/30 bg-orange-500/10',
  USER_INPUT: 'text-violet-300 border-violet-500/30 bg-violet-500/10',
  DEMO: 'text-slate-300 border-slate-500/30 bg-slate-500/10',
  UNAVAILABLE: 'text-red-300 border-red-500/30 bg-red-500/10',
  SENSOR_UNAVAILABLE: 'text-red-300 border-red-500/30 bg-red-500/10',
  UNRESOLVED: 'text-slate-400 border-slate-500/30 bg-slate-500/10',
};

export function SourceBadge({ type }: { type: SourceType }) {
  return (
    <span className={`inline-block mt-1 text-[8px] px-1.5 py-0.5 rounded border ${sourceTone[type] || sourceTone.UNRESOLVED}`}>
      {type}
    </span>
  );
}

function FactorRow({ factor }: { factor: { feature: string; name?: string; value: number | null; unit: string; source_type: SourceType; source?: string } }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg bg-slate-900/30 border border-slate-800 p-2">
      <div className="min-w-0">
        <p className="text-[11px] text-slate-300 truncate">{factor.name || factor.feature}</p>
        <SourceBadge type={factor.source_type} />
      </div>
      <span className="font-mono text-xs text-slate-200 whitespace-nowrap">
        {factor.value == null ? 'unavailable' : `${typeof factor.value === 'number' ? factor.value.toFixed(2) : factor.value} ${factor.unit}`}
      </span>
    </div>
  );
}

export function RiskIntelligencePanel({ assessment }: { assessment: RiskAssessment }) {
  const level = assessment.risk_level.toLowerCase() as DisplayLevel;
  const color = riskColor(level);

  const [rainfallMultiplier, setRainfallMultiplier] = useState(1.5);
  const [scenario, setScenario] = useState<RiskAssessment | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const [sensitivity, setSensitivity] = useState<SlopeSensitivityResponse | null>(null);
  const [sensitivityLoading, setSensitivityLoading] = useState(false);
  const currentSlope = assessment.terrain.find(f => f.feature === 'Slope_Angle')?.value ?? 30;
  const [slopeAngle, setSlopeAngle] = useState(currentSlope);
  const [slopeScenario, setSlopeScenario] = useState<RiskAssessment | null>(null);
  const [slopeSimulating, setSlopeSimulating] = useState(false);

  useEffect(() => {
    setSlopeAngle(currentSlope);
    setSlopeScenario(null);
  }, [assessment.location.latitude, assessment.location.longitude, currentSlope]);

  useEffect(() => {
    const loadSensitivity = async () => {
      try {
        setSensitivityLoading(true);
        setSensitivity(await getSlopeSensitivity(assessment.location.latitude, assessment.location.longitude));
      } catch {
        setSensitivity(null);
      } finally {
        setSensitivityLoading(false);
      }
    };
    loadSensitivity();
  }, [assessment.location.latitude, assessment.location.longitude]);

  const runScenario = async () => {
    setSimulating(true);
    try {
      setScenario(await simulateRisk(assessment.location.latitude, assessment.location.longitude, rainfallMultiplier, 0));
    } catch {
      setScenario(null);
    } finally {
      setSimulating(false);
    }
  };

  const runSlopeScenario = async () => {
    setSlopeSimulating(true);
    try {
      setSlopeScenario(await simulateSlopeRisk(assessment.location.latitude, assessment.location.longitude, slopeAngle));
    } catch {
      setSlopeScenario(null);
    } finally {
      setSlopeSimulating(false);
    }
  };

  const model1 = assessment.model_evidence?.model1;
  const model3 = assessment.model_evidence?.model3;

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] uppercase tracking-widest text-slate-500">Risk intelligence</span>
          <span className={`text-[9px] px-2 py-1 rounded border ${assessment.degraded ? 'text-amber-300 border-amber-500/30 bg-amber-500/10' : 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10'}`}>
            {assessment.degraded ? 'DEGRADED INPUTS' : 'FULL INPUTS'}
          </span>
        </div>
        <div className="mt-2 flex items-center gap-3">
          <div className={`py-2 px-4 rounded-xl border border-slate-700/60 ${riskGlow(level)}`}>
            <div className="flex items-center gap-3">
              <span className="text-4xl font-black font-mono" style={{ color }}>{assessment.risk_score.toFixed(1)}</span>
              <span className="text-sm font-bold" style={{ color }}>{riskLabel(level)}</span>
            </div>
            <p className="text-[9px] font-mono text-slate-500 mt-1">
              influence radius: {assessment.influence_radius_m} m
            </p>
          </div>
        </div>
        <p className="text-[10px] text-slate-500 mt-2">Basis: {assessment.score_basis}</p>
        <p className="text-[10px] text-slate-600 mt-1">{assessment.prediction_horizon}</p>
      </div>

      <div className="rounded-lg bg-slate-900/40 border border-slate-700/50 p-3">
        <div className="flex items-center gap-2 text-xs text-slate-300">
          <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span className="truncate">{assessment.location.display_name || 'Selected coordinate'}</span>
        </div>
        <p className="text-[10px] font-mono text-slate-500 mt-1">
          {assessment.location.latitude.toFixed(5)}, {assessment.location.longitude.toFixed(5)}
          {assessment.location.state ? ` · ${assessment.location.state}${assessment.location.district ? ` / ${assessment.location.district}` : ''}` : ''}
        </p>
        <p className="text-[9px] text-slate-600 mt-0.5">Geocode source: {assessment.location.source_type || 'UNAVAILABLE'} {assessment.location.source ? `(${assessment.location.source})` : ''}</p>
      </div>

      {assessment.why_high_risk.length > 0 && (
        <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-3">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-orange-300 mb-2">
            <Zap className="w-3.5 h-3.5" /> Why this score
          </div>
          <ul className="space-y-1">
            {assessment.why_high_risk.map((r, i) => <li key={i} className="text-[10px] text-orange-100/70">• {r}</li>)}
          </ul>
        </div>
      )}

      <div className="rounded-lg border border-blue-500/15 bg-blue-500/5 p-3">
        <button onClick={() => setShowEvidence(v => !v)} className="w-full flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-blue-300">
            <BrainCircuit className="w-3.5 h-3.5" /> Model evidence
          </span>
          <span className="text-[10px] text-slate-500">{showEvidence ? '−' : '+'}</span>
        </button>
        {showEvidence && (
          <div className="mt-3 space-y-2">
            <EvidenceRow label={model1?.label || 'Susceptibility probability'} value={model1?.value ?? null} status={model1?.status || 'unknown'} />
            <EvidenceRow label={model3?.label || 'Environmental anomaly evidence'} value={model3?.value ?? null} status={model3?.status || 'unknown'} />
            <EvidenceRow label="Slope_Angle coefficient (model 1, logistic)" value={assessment.model_outputs?.model1_feature_importance?.[0]?.coefficient as number ?? null} status={assessment.model_outputs?.model1_feature_importance?.[0]?.direction || 'unknown'} />
            <FusionRow assessment={assessment} />
            <div className="grid grid-cols-4 gap-1.5 pt-1">
              {Object.entries(assessment.model_status || {}).map(([k, v]) => (
                <div key={k} className="rounded bg-slate-900/40 border border-slate-800 p-1 text-center">
                  <p className="text-[8px] font-mono text-slate-500">{k}</p>
                  <p className={`text-[8px] font-bold ${v.status === 'ACTIVE' ? 'text-emerald-400' : v.status === 'disabled' || v.status === 'DISABLED' ? 'text-slate-500' : 'text-amber-400'}`}>{v.status}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="flex items-center gap-2 mb-2"><Database className="w-3.5 h-3.5 text-cyan-400" /><h4 className="text-[10px] uppercase tracking-widest font-semibold text-slate-400">Weather factors (live)</h4></div>
        <div className="space-y-2">
          {(assessment.factors || []).map(f => <FactorRow key={f.feature} factor={f} />)}
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-2"><Radar className="w-3.5 h-3.5 text-cyan-400" /><h4 className="text-[10px] uppercase tracking-widest font-semibold text-slate-400">Terrain factors (DEM)</h4></div>
        <div className="space-y-2">
          {(assessment.terrain || []).map(f => <FactorRow key={f.feature} factor={f} />)}
        </div>
      </div>

      <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-cyan-300">
            <Radar className="w-3.5 h-3.5" /> Slope model evidence
          </div>
          <span className="text-[9px] font-mono text-slate-500">MODEL 1 · LOGISTIC</span>
        </div>
        <div className="mt-2 text-[10px] text-slate-300">
          <span className="font-bold text-cyan-200">Why this matters:</span> Slope angle is used as a terrain feature by the susceptibility model.
        </div>
        <div className="mt-2 text-[10px] text-slate-300">
          <span className="font-bold text-cyan-200">Model-derived influence:</span>{' '}
          {assessment.model_outputs?.model1_feature_importance?.[0]?.coefficient != null
            ? `coefficient ${Number(assessment.model_outputs.model1_feature_importance[0].coefficient).toFixed(4)} (${assessment.model_outputs.model1_feature_importance[0].direction || 'learned direction'})`
            : 'coefficient unavailable'}
        </div>
        <div className="mt-2 text-[9px] text-slate-500">
          The trained susceptibility model learns the slope effect together with elevation, aspect, weather, and soil features; no separate slope rule or manual risk adjustment is applied.
        </div>
      </div>

      {sensitivity && (
        <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-violet-300">
              <BrainCircuit className="w-3.5 h-3.5" /> Slope sensitivity
            </div>
            <span className="text-[9px] font-mono text-slate-500">{sensitivityLoading ? 'loading' : 'what-if'}</span>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {sensitivity.slope_sensitivity.map(row => (
              <div key={row.slope_angle} className="rounded bg-slate-900/40 border border-slate-800 p-2 text-center">
                <p className="text-[8px] text-slate-500">{row.slope_angle}°</p>
                <p className="font-mono text-[10px] text-violet-300">p={row.model_output_probability.toFixed(4)}</p>
                <p className="text-[8px] text-slate-500">{row.risk_level}</p>
              </div>
            ))}
          </div>
          <p className="text-[9px] text-slate-500 mt-2">{sensitivity.note}</p>
        </div>
      )}

      <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-[10px] uppercase tracking-widest font-semibold text-cyan-300">What-if slope angle simulator</h4>
          <span className="text-[9px] font-mono text-slate-500">scenario only</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-2">Current DEM slope: <span className="font-mono text-cyan-200">{currentSlope.toFixed(2)}°</span></p>
        <label className="block text-[10px] text-slate-400 mt-3" htmlFor="slope-angle-simulator">Slope angle: <span className="font-mono text-slate-200">{slopeAngle.toFixed(2)}°</span></label>
        <input
          id="slope-angle-simulator"
          className="w-full mt-2 accent-cyan-400"
          type="range"
          min="0"
          max="90"
          step="0.1"
          value={slopeAngle}
          onChange={e => setSlopeAngle(Number(e.target.value))}
        />
        <button onClick={runSlopeScenario} disabled={slopeSimulating} className="mt-2 w-full py-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-200 text-xs font-semibold disabled:opacity-50">
          {slopeSimulating ? <span className="inline-flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Running model…</span> : 'Run slope simulation'}
        </button>
        {slopeScenario && (() => {
          const change = slopeScenario.risk_score - assessment.risk_score;
          const interpretation = Math.abs(change) < 0.05
            ? 'Risk remained approximately unchanged'
            : change > 0 ? 'Risk increased' : 'Risk decreased';
          return (
            <div className="mt-3 space-y-2">
              <div className="grid grid-cols-3 gap-1.5">
                <div className="rounded bg-slate-900/40 border border-slate-800 p-2 text-center">
                  <p className="text-[8px] text-slate-500">CURRENT</p>
                  <p className="font-mono text-[10px] text-slate-200">{assessment.risk_score.toFixed(2)}%</p>
                </div>
                <div className="rounded bg-slate-900/40 border border-slate-800 p-2 text-center">
                  <p className="text-[8px] text-slate-500">WHAT-IF</p>
                  <p className="font-mono text-[10px] text-cyan-200">{slopeScenario.risk_score.toFixed(2)}%</p>
                </div>
                <div className="rounded bg-slate-900/40 border border-slate-800 p-2 text-center">
                  <p className="text-[8px] text-slate-500">CHANGE</p>
                  <p className="font-mono text-[10px] text-cyan-200">{change >= 0 ? '+' : ''}{change.toFixed(2)}%</p>
                </div>
              </div>
              <p className="text-[10px] text-cyan-100/80">{interpretation}</p>
              <p className="text-[9px] text-slate-500">Simulated scenario — actual terrain remains unchanged.</p>
            </div>
          );
        })()}
      </div>

      <div>
        <div className="flex items-center gap-2 mb-2"><Satellite className="w-3.5 h-3.5 text-amber-400" /><h4 className="text-[10px] uppercase tracking-widest font-semibold text-slate-400">Nearby impacted assets (OSM)</h4></div>
        {assessment.impacted_assets.length === 0 ? (
          <p className="text-xs text-slate-500">No OSM assets returned in the query radius — live OpenStreetMap may be unreachable for this point.</p>
        ) : (
          <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
            {assessment.impacted_assets.slice(0, 15).map((asset, i) => (
              <div key={`${asset.name}-${i}`} className="flex items-center justify-between text-[10px] border-b border-slate-800 pb-1.5">
                <span className="text-slate-300 truncate pr-2">
                  {asset.name || asset.category || asset.type}
                  <span className="text-slate-600"> · {asset.type}</span>
                </span>
                <span className="flex items-center gap-2 whitespace-nowrap">
                  {asset.exposure && <span className={`text-[8px] font-bold ${asset.exposure === 'HIGH' ? 'text-red-400' : asset.exposure === 'MODERATE' ? 'text-amber-400' : 'text-emerald-400'}`}>{asset.exposure}</span>}
                  <span className="font-mono text-slate-400">{asset.distance_m} m</span>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <div className="flex items-center gap-2 mb-2"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /><h4 className="text-[10px] uppercase tracking-widest font-semibold text-slate-400">Action guidance</h4></div>
        <ul className="space-y-1.5">{(assessment.recommended_actions || []).map(action => <li key={action} className="text-[10px] text-slate-400 leading-relaxed">• {action}</li>)}</ul>
      </div>

      <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-3">
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-[10px] uppercase tracking-widest font-semibold text-violet-300">What-if rainfall simulator</h4>
          <span className="text-[9px] font-mono text-slate-500">×{rainfallMultiplier.toFixed(1)}</span>
        </div>
        <input className="w-full mt-2 accent-violet-400" type="range" min="0.5" max="3" step="0.1" value={rainfallMultiplier} onChange={e => setRainfallMultiplier(Number(e.target.value))} />
        <button onClick={runScenario} disabled={simulating} className="mt-2 w-full py-2 rounded-lg border border-violet-500/30 bg-violet-500/10 text-violet-200 text-xs font-semibold disabled:opacity-50">
          {simulating ? <span className="inline-flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Running model…</span> : 'Run scenario through backend'}
        </button>
        {scenario && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="rounded bg-slate-900/40 p-2 text-center">
              <p className="text-[9px] text-slate-500">CURRENT</p>
              <p className="font-mono font-bold text-slate-200">{assessment.risk_score.toFixed(1)}</p>
            </div>
            <div className="rounded bg-slate-900/40 p-2 text-center">
              <p className="text-[9px] text-slate-500">SCENARIO</p>
              <p className="font-mono font-bold text-violet-300">{scenario.risk_score.toFixed(1)}</p>
            </div>
          </div>
        )}
      </div>

      {assessment.degraded_inputs.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-semibold text-amber-300 mb-2">
            <AlertTriangle className="w-3.5 h-3.5" /> Degraded inputs ({assessment.degraded_inputs.length})
          </div>
          <ul className="space-y-1">
            {assessment.degraded_inputs.map(f => (
              <li key={f.feature} className="text-[9px] text-amber-100/60">
                • {f.feature} → {f.source_type === 'SENSOR_UNAVAILABLE' ? 'no field sensor' : f.source_type === 'DATASET_DEFAULT' ? 'satellite dataset default (Copernicus not configured)' : 'unresolved from live data'}
              </li>
            ))}
          </ul>
        </div>
      )}

      {assessment.warnings.length > 0 && (
        <details className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-2">
          <summary className="text-[10px] text-amber-300 cursor-pointer">Pipeline warnings ({assessment.warnings.length})</summary>
          <ul className="mt-2 space-y-1">{assessment.warnings.map(w => <li key={w} className="text-[9px] text-amber-100/60">• {w}</li>)}</ul>
        </details>
      )}
    </div>
  );
}

function EvidenceRow({ label, value, status }: { label: string; value: number | null; status: string }) {
  return (
    <div className="flex items-center justify-between rounded bg-slate-900/40 border border-slate-800 px-2 py-1.5">
      <div><p className="text-[10px] text-slate-300">{label}</p><p className="text-[8px] uppercase text-slate-600">{status}</p></div>
      <span className={`font-mono text-xs ${value == null ? 'text-slate-600' : 'text-blue-300'}`}>{value == null ? '—' : `${value.toFixed(4)}`}</span>
    </div>
  );
}

function FusionRow({ assessment }: { assessment: RiskAssessment }) {
  const fs = assessment.fusion_status;
  return (
    <div className="flex items-center justify-between rounded bg-slate-900/40 border border-slate-800 px-2 py-1.5">
      <div>
        <p className="text-[10px] text-slate-300">Experimental ensemble fusion</p>
        <p className="text-[8px] uppercase text-slate-600">{fs.status}{fs.reason ? ` · ${fs.reason}` : ''}</p>
      </div>
      <span className={`font-mono text-[9px] font-bold ${fs.enabled ? 'text-emerald-400' : 'text-slate-500'}`}>{fs.enabled ? 'ACTIVE' : 'off'}</span>
    </div>
  );
}