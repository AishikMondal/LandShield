import { useState, useEffect } from 'react';
import { Shield, Radio, ChevronRight, Menu, X } from 'lucide-react';

interface NavbarProps {
  onLaunchCommand: () => void;
}

export function Navbar({ onLaunchCommand }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links = [
    { label: 'GIS Live Map', href: '#gis-map' },
    { label: 'AI Models', href: '#ai-models' },
    { label: 'Citizen Reporting', href: '#citizen-reporting' },
    { label: 'Emergency Contacts', href: '#emergency' },
  ];

  const scrollTo = (href: string) => {
    const el = document.querySelector(href);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
    setMobileOpen(false);
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-[1000] bg-[#0B0F17]/95 backdrop-blur-lg border-b border-[#1E293B] transition-all duration-300 ${scrolled ? 'shadow-lg shadow-black/20' : ''}`}>
      <div className="max-w-7xl mx-auto px-4 lg:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo + Title */}
          <div className="flex items-center gap-3">
            <div className="relative w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500/20 to-emerald-500/10 border border-blue-500/30 flex items-center justify-center">
              <Shield className="w-4.5 h-4.5 text-blue-400" />
              <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-[#0B0F17] animate-pulse" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-100 tracking-tight leading-none">
                LandShield <span className="text-slate-600 font-normal hidden sm:inline">| AI Landslide Intelligence</span>
              </h1>
              <p className="text-[9px] text-slate-500 font-mono tracking-wide mt-0.5">North Eastern Region</p>
            </div>
          </div>

          {/* Desktop Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {links.map(link => (
              <button
                key={link.href}
                onClick={() => scrollTo(link.href)}
                className="px-3 py-2 text-xs font-medium text-slate-400 hover:text-slate-100 hover:bg-slate-800/30 rounded-lg transition-all"
              >
                {link.label}
              </button>
            ))}
          </nav>

          {/* Status + CTA */}
          <div className="flex items-center gap-2 lg:gap-3">
            <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
              <span className="text-[10px] text-emerald-300 font-medium">IMD: Live</span>
              <span className="text-slate-600">·</span>
              <span className="text-[10px] text-slate-400">Sentinel-1: Synced</span>
              <span className="text-slate-600">·</span>
              <span className="text-[10px] text-amber-400/80">Low-BW</span>
            </div>

            <button
              onClick={onLaunchCommand}
              className="flex items-center gap-1.5 px-3 lg:px-4 py-2 rounded-lg bg-blue-500/15 border border-blue-500/40 text-blue-300 text-xs font-semibold hover:bg-blue-500/25 hover:border-blue-400 transition-all group"
            >
              <span>Launch Command Center</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button onClick={() => setMobileOpen(!mobileOpen)} className="lg:hidden p-1.5 text-slate-400 hover:text-slate-100">
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="lg:hidden pb-4 space-y-1">
            {links.map(link => (
              <button
                key={link.href}
                onClick={() => scrollTo(link.href)}
                className="block w-full text-left px-3 py-2.5 text-sm text-slate-400 hover:text-slate-100 hover:bg-slate-800/30 rounded-lg transition-all"
              >
                {link.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}
