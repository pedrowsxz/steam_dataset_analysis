import { useState } from 'react';
import TabBar from './components/TabBar';
import ColdStartBanner from './components/ColdStartBanner';
import { useHealthCheck } from './hooks/useHealthCheck';
import OverviewTab from './tabs/OverviewTab';
import PricingTab from './tabs/PricingTab';
import TrendsTab from './tabs/TrendsTab';
import BiArtifactTab from './tabs/BiArtifactTab';
import './App.css';

const TAB_COMPONENTS = {
  overview: OverviewTab,
  pricing: PricingTab,
  trends: TrendsTab,
  bi: BiArtifactTab,
};

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const healthStatus = useHealthCheck();
  const ActiveTabComponent = TAB_COMPONENTS[activeTab];

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Steam Marketplace, Mapped</h1>
        <p className="app__subtitle">
          27,075 titles from the Databricks Gold layer, served live from Postgres.
        </p>
      </header>

      <TabBar active={activeTab} onChange={setActiveTab} />

      <main className="app__main">
        <ColdStartBanner status={healthStatus} />
        <ActiveTabComponent />
      </main>
    </div>
  );
}
