'use client';
import { useState } from 'react';
import { BarChart2, Truck, AlertTriangle, Search, Sliders, MessageSquare, Activity } from 'lucide-react';
import DashboardPage from './pages/DashboardPage';
import RiskCenterPage from './pages/RiskCenterPage';
import FleetOptimizerPage from './pages/FleetOptimizerPage';
import SimulatorPage from './pages/SimulatorPage';
import CopilotPage from './pages/CopilotPage';

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart2 },
  { id: 'risk', label: 'Risk Center', icon: AlertTriangle },
  { id: 'fleet', label: 'Fleet Optimizer', icon: Truck },
  { id: 'simulator', label: 'What-If Simulator', icon: Sliders },
  { id: 'copilot', label: 'AI Copilot', icon: MessageSquare },
] as const;

type Page = typeof NAV[number]['id'];

export default function Home() {
  const [page, setPage] = useState<Page>('dashboard');

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            <span className="text-sm font-bold text-white tracking-wide">SupplyChainAI</span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 ml-7">Risk & Fleet Intelligence</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setPage(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                page === id
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-slate-800">
          <p className="text-xs text-slate-600">IBM Bob Hackathon 2026</p>
          <p className="text-xs text-slate-700">TeamAstra</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {page === 'dashboard' && <DashboardPage />}
        {page === 'risk' && <RiskCenterPage />}
        {page === 'fleet' && <FleetOptimizerPage />}
        {page === 'simulator' && <SimulatorPage />}
        {page === 'copilot' && <CopilotPage />}
      </main>
    </div>
  );
}
