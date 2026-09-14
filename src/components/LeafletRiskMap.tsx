import { Fragment, useCallback, useEffect, useState } from 'react';
import {
  Circle, CircleMarker, MapContainer, Marker, Polygon, TileLayer, Tooltip, useMap, useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { AlertTriangle, Loader2, MapPin } from 'lucide-react';
import { riskZones } from '@/data/mockData';
import { riskColor, riskColorStr } from '@/lib/risk';
import { predictRisk, getHotspots, type HotspotItem, type RiskAssessment } from '@/api/client';
import { RiskIntelligencePanel } from '@/components/RiskIntelligencePanel';
import { HotspotPanel } from '@/components/HotspotPanel';

const hotspotIcon = (rank: number, level: string) => L.divIcon({
  className: '',
  html: `<div style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:9999px;border:2px solid #0B0F17;background:${riskColorStr(level)};color:#0B0F17;font-weight:900;font-size:12px;font-family:ui-monospace,monospace;box-shadow:0 0 0 2px ${riskColorStr(level)}66;">${rank}</div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 13],
});

const assetIcon = (exposure: string | undefined, type: string) => {
  const color = exposure === 'HIGH' ? '#EF4444' : exposure === 'MODERATE' ? '#F59E0B' : '#34D399';
  const glyph = type === 'hospital' ? '✚' : type === 'school' ? '⇶' : type === 'police' ? '⬢' : type === 'parking' ? 'P' : '•';
  return L.divIcon({
    className: '',
    html: `<div style="display:flex;align-items:center;justify-content:center;min-width:16px;height:16px;padding:0 3px;border-radius:4px;border:1.5px solid ${color};background:rgba(11,15,23,0.85);color:${color};font-size:9px;font-weight:800;box-shadow:0 0 6px ${color}55;">${glyph}</div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
};

export function LeafletRiskMap() {
  const [selected, setSelected] = useState<[number, number] | null>(null);
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hotspots, setHotspots] = useState<HotspotItem[]>([]);

  const loadHotspots = useCallback(async () => {
    try {
      const p = await getHotspots(false);
      setHotspots(p.hotspots);
    } catch {
      setHotspots([]);
    }
  }, []);

  useEffect(() => {
    loadHotspots();
  }, [loadHotspots]);

  const analyze = useCallback(async (lat: number, lng: number) => {
    setSelected([lat, lng]);
    setLoading(true);
    setError('');
    try {
      setAssessment(await predictRisk(lat, lng));
    } catch (e) {
      setAssessment(null);
      setError(e instanceof Error ? e.message : 'Risk service unavailable');
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <section id="gis-map" className="relative py-20 px-4 lg:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-semibold text-blue-400 uppercase tracking-widest">Section 02</span>
            <div className="h-px flex-1 max-w-[80px] bg-gradient-to-r from-blue-500/30 to-transparent" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">Interactive Risk Intelligence Map</h2>
          <p className="text-sm text-slate-400 mt-2 max-w-3xl">
            Click or <span className="text-blue-300">double-click</span> anywhere to run live weather + DEM terrain + OSM assets through the loaded models.
            Numbered badges are the dynamic <span className="text-amber-300">Top-5 NER hotspots</span> refreshed from the backend.
          </p>
        </div>

        <div className="grid xl:grid-cols-[1fr_380px] gap-4">
          <div className="relative h-[540px] lg:h-[680px] rounded-xl overflow-hidden border border-[#1E293B] bg-[#080B12]">
            <MapContainer center={[26.05, 91.05]} zoom={6} minZoom={5} maxZoom={17} scrollWheelZoom className="h-full w-full">
              <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <MapClickHandler onAnalyze={analyze} />

              <HotspotMarkers hotspots={hotspots} onSelect={analyze} />

              {riskZones.map(zone => {
                const color = riskColor(zone.riskLevel);
                return (
                  <Fragment key={zone.id}>
                    <Polygon
                      positions={zone.polygon}
                      pathOptions={{ color, weight: 1, dashArray: '5 5', fillColor: color, fillOpacity: 0.05, opacity: 0.35 }}
                    >
                      <Tooltip>{zone.name} · demo reference polygon {zone.riskScore}/100 (not live)</Tooltip>
                    </Polygon>
                  </Fragment>
                );
              })}

              {selected && (
                <Fragment>
                  <Circle center={selected} radius={assessment?.influence_radius_m ?? 1000} pathOptions={{ color: '#3B82F6', weight: 1, dashArray: '4 4', fillColor: '#3B82F6', fillOpacity: 0.06 }}>
                    <Tooltip>Risk influence radius: {assessment?.influence_radius_m ?? 1000} m</Tooltip>
                  </Circle>
                  <CircleMarker center={selected} radius={8} pathOptions={{ color: '#F8FAFC', weight: 2, fillColor: '#3B82F6', fillOpacity: 1 }}>
                    <Tooltip permanent direction="top">Analysis point{assessment ? ` · ${assessment.risk_level} ${assessment.risk_score.toFixed(0)}/100` : ''}</Tooltip>
                  </CircleMarker>
                </Fragment>
              )}

              {assessment?.impacted_assets.map(asset => (
                <Marker
                  key={`${asset.type}-${asset.name}-${asset.latitude}-${asset.longitude}`}
                  position={[asset.latitude, asset.longitude]}
                  icon={assetIcon(asset.exposure, asset.type)}
                >
                  <Tooltip>
                    {asset.name || asset.type} · {asset.distance_m} m
                    {asset.exposure ? ` · ${asset.exposure} exposure` : ''}
                  </Tooltip>
                </Marker>
              ))}
            </MapContainer>

            <div className="absolute top-3 left-3 z-[400] rounded-lg border border-[#1E293B] bg-[#0B0F17]/90 backdrop-blur-sm px-3 py-2 pointer-events-none">
              <p className="text-[9px] uppercase tracking-widest text-slate-500">Data mode</p>
              <p className="text-xs font-semibold text-emerald-300">Live where available · fallback-labelled</p>
              <div className="flex items-center gap-2 mt-1 text-[8px] text-slate-400">
                <HotspotLegendMark label="NER hotspot" color="#F97316" />
                <HotspotLegendMark label="asset" color="#34D399" />
                <HotspotLegendMark label="analysis" color="#3B82F6" />
              </div>
            </div>
          </div>

          <aside className="flex flex-col gap-3 min-h-[540px]">
            <div className="rounded-xl border border-[#1E293B] bg-[#0E141F]/85 backdrop-blur-md p-4 flex-1 overflow-y-auto max-h-[560px]">
              {!selected && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-center px-4">
                  <MapPin className="w-9 h-9 text-blue-400 mb-3" />
                  <h3 className="text-sm font-semibold text-slate-200">Select a location</h3>
                  <p className="text-xs text-slate-500 mt-2">Click or double-click the map to run the real-data + model pipeline.</p>
                </div>
              )}

              {loading && (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-400 mb-3" />
                  <p className="text-sm font-semibold text-slate-200">Collecting intelligence</p>
                  <p className="text-xs text-slate-500 mt-1">Weather · DEM terrain · OSM assets · models · alerts</p>
                  <p className="text-[9px] text-slate-600 mt-2">First run can take ~30 s while live services respond.</p>
                </div>
              )}

              {error && !loading && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
                  <div className="flex items-center gap-2 text-red-300 text-sm font-semibold"><AlertTriangle className="w-4 h-4" /> Backend unavailable</div>
                  <p className="text-xs text-red-200/70 mt-2 break-words">{error}</p>
                  <p className="text-[10px] text-slate-500 mt-3">Start the FastAPI backend on port 8000 and retry.</p>
                </div>
              )}

              {assessment && !loading && <RiskIntelligencePanel assessment={assessment} />}
            </div>

            <HotspotPanel onSelect={analyze} />
          </aside>
        </div>
      </div>
    </section>
  );
}

function HotspotLegendMark({ label, color }: { label: string; color: string }) {
  return <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: color }} />{label}</span>;
}

function HotspotMarkers({ hotspots, onSelect }: { hotspots: HotspotItem[]; onSelect: (lat: number, lng: number) => void }) {
  return (
    <Fragment>
      {hotspots.map(h => (
        <Marker key={h.rank} position={[h.latitude, h.longitude]} icon={hotspotIcon(h.rank, h.risk_level)} eventHandlers={{ click: () => onSelect(h.latitude, h.longitude) }}>
          <Tooltip direction="top">
            #{h.rank} · {h.location_name} · {h.risk_level} {h.risk_score.toFixed(0)}/100
          </Tooltip>
        </Marker>
      ))}
    </Fragment>
  );
}

function MapClickHandler({ onAnalyze }: { onAnalyze: (lat: number, lng: number) => void }) {
  const map = useMap();
  useMapEvents({
    click: e => {
      map.panTo([e.latlng.lat, e.latlng.lng], { animate: true, duration: 0.4 });
      onAnalyze(e.latlng.lat, e.latlng.lng);
    },
    dblclick: e => {
      map.flyTo([e.latlng.lat, e.latlng.lng], Math.max(map.getZoom(), 10), { animate: true, duration: 0.6 });
      onAnalyze(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}