export function TopoBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#070A0F] via-[#0B0F17] to-[#0B0F17]" />

      {/* Topographic contour SVG */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.12]"
        viewBox="0 0 1200 800"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <pattern id="topo-grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#1A2A44" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="1200" height="800" fill="url(#topo-grid)" />

        {/* Contour lines - mountain ridges */}
        <g stroke="#2563EB" fill="none" strokeWidth="1" opacity="0.4">
          {[...Array(12)].map((_, i) => {
            const y = 100 + i * 55;
            const amp = 30 + i * 4;
            return (
              <path
                key={`contour-${i}`}
                d={`M -50 ${y} 
                  C 100 ${y - amp}, 200 ${y + amp}, 350 ${y - amp/2}
                  S 550 ${y + amp}, 700 ${y - amp}
                  S 900 ${y + amp/2}, 1100 ${y - amp/2}
                  S 1300 ${y + amp}, 1300 ${y}`}
                opacity={1 - i * 0.05}
              />
            );
          })}
        </g>

        {/* Secondary contour set */}
        <g stroke="#10B981" fill="none" strokeWidth="0.8" opacity="0.2">
          {[...Array(8)].map((_, i) => {
            const y = 50 + i * 80;
            return (
              <path
                key={`contour2-${i}`}
                d={`M -50 ${y + 20}
                  C 150 ${y}, 300 ${y + 40}, 500 ${y + 10}
                  S 800 ${y + 50}, 1000 ${y + 20}
                  S 1250 ${y + 40}, 1250 ${y + 20}`}
              />
            );
          })}
        </g>
      </svg>

      {/* Radial glow accent */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-500/5 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-0 w-[400px] h-[300px] bg-emerald-500/3 rounded-full blur-[100px]" />
      <div className="absolute top-1/3 left-0 w-[300px] h-[200px] bg-orange-500/3 rounded-full blur-[80px]" />

      {/* Grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(#3B82F6 1px, transparent 1px), linear-gradient(90deg, #3B82F6 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
    </div>
  );
}
