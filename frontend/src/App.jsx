import { useState } from 'react';
import Sidebar from './components/Sidebar';
import DataView from './components/data/DataView';
import DemoView from './components/demo/DemoView';

export default function App() {
  const [activeTab, setActiveTab] = useState('demo');
  const [activeDataSub, setActiveDataSub] = useState('restaurants');

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-bg-surface)] p-3">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        activeDataSub={activeDataSub}
        onDataSubChange={setActiveDataSub}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-hidden rounded-2xl border border-[var(--color-border)] ml-3 bg-white">
        {activeTab === 'data' && (
          <DataView activeCollection={activeDataSub} />
        )}
        {activeTab === 'demo' && (
          <DemoView />
        )}
      </main>
    </div>
  );
}
