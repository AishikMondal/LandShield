import { Shield, Radio } from 'lucide-react';

export function Footer() {
  return (
    <footer className="relative border-t border-[#1E293B] py-10 px-4 lg:px-6 mt-10">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500/20 to-emerald-500/10 border border-blue-500/30 flex items-center justify-center">
                <Shield className="w-4.5 h-4.5 text-blue-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">LandShield</h3>
                <p className="text-[9px] text-slate-500 font-mono">AI Landslide Intelligence Platform</p>
              </div>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-sm">
              A multi-hazard early warning system fusing InSAR, terrain susceptibility, and rainfall dynamics for sub-kilometer landslide risk forecasts across the North Eastern Region of India.
            </p>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">Platform</h4>
            <ul className="space-y-2">
              {[
                { label: 'GIS Live Map', href: '#gis-map' },
                { label: 'AI Models', href: '#ai-models' },
                { label: 'Citizen Reporting', href: '#citizen-reporting' },
                { label: 'Emergency Contacts', href: '#emergency' },
              ].map(link => (
                <li key={link.href}>
                  <button
                    onClick={() => document.querySelector(link.href)?.scrollIntoView({ behavior: 'smooth' })}
                    className="text-xs text-slate-500 hover:text-slate-300 transition-all"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">System Status</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
                <span>IMD Data Feeds: Live</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="w-3 h-3 rounded-full bg-emerald-500 flex items-center justify-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#0B0F17]" />
                </span>
                <span>Sentinel-1 InSAR: Synced</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                <span>Low-Bandwidth Mode: Available</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-[#1E293B]/50 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="text-[10px] text-slate-600 font-mono">
            Built for the North Eastern Region
          </p>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-slate-600">Mock data for demonstration · Not for operational use</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
