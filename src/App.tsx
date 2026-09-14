import { Navbar } from '@/components/Navbar';
import { TopoBackground } from '@/components/TopoBackground';
import { Hero } from '@/components/Hero';
import { ModelNavBar } from '@/components/ModelNavBar';
import { LeafletRiskMap } from '@/components/LeafletRiskMap';
import { AlertBroadcast } from '@/components/AlertBroadcast';
import { AlertBanner } from '@/components/AlertBanner';
import { AIModels } from '@/components/AIModels';
import { CitizenReporting } from '@/components/CitizenReporting';
import { EmergencyContacts } from '@/components/EmergencyContacts';
import { Footer } from '@/components/Footer';

export default function App() {
  const scrollToMap = () => {
    document.querySelector('#gis-map')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="relative min-h-screen bg-[#0B0F17] text-slate-200 overflow-x-hidden">
      <TopoBackground />
      <div className="relative z-10">
        <Navbar onLaunchCommand={scrollToMap} />
        <ModelNavBar />
        <main>
          <Hero onLaunchCommand={scrollToMap} />
          <LeafletRiskMap />
          <AlertBroadcast />
          <AIModels />
          <CitizenReporting />
          <EmergencyContacts />
        </main>
        <Footer />
      </div>
      <AlertBanner />
    </div>
  );
}
