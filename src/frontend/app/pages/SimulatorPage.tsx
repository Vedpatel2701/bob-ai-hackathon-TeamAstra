'use client';
import { useState } from 'react';
import { Play, Loader2, ArrowRight, TrendingUp, TrendingDown } from 'lucide-react';
import { api, type SimulateResponse } from '@/lib/api';
import { pct, fmt } from '@/lib/utils';

const DEFAULT: { weather: number; traffic: number; port: number } = { weather: 0, traffic: 0, port: 0 };

export default function SimulatorPage() {
  const [weather, setWeather] = useState(0);
  const [traffic, setTraffic] = useState(0);
  const [port, setPort] = useState(0);
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setRunning(true);
    setError('');
    try {
      const r = await api.simulate({
        weather_severity_delta: weather,
        traffic_level_delta: traffic,
        port_congestion_delta: port,
        vehicle_unavailable_ids: [],
      });
      setResult(r);
    } catch (e) { setError(String(e)); }
    finally { setRunning(false); }
  };

  const reset = () => { setWeather(0); setTraffic(0); setPort(0); setResult(null); };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">What-If Simulator</h1>
        <p className="text-sm text-slate-400 mt-0.5">Adjust conditions and recalculate risk across all shipments</p>
      </div>

      {/* Controls */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-5">
        <h3 className="text-sm font-semibold text-slate-200">Scenario Parameters</h3>

        <SliderControl label="Weather Severity" value={weather} onChange={setWeather}
          description={weather === 0 ? 'No change' : `${weather > 0 ? '+' : ''}${(weather * 100).toFixed(0)}% change in weather severity`}
          color={weather > 0 ? 'text-orange-400' : 'text-green-400'}
        />
        <SliderControl label="Traffic Level" value={traffic} onChange={setTraffic}
          description={traffic === 0 ? 'No change' : `${traffic > 0 ? '+' : ''}${(traffic * 100).toFixed(0)}% change in traffic level`}
          color={traffic > 0 ? 'text-orange-400' : 'text-green-400'}
        />
        <SliderControl label="Port Congestion" value={port} onChange={setPort}
          description={port === 0 ? 'No change' : `${port > 0 ? '+' : ''}${(port * 100).toFixed(0)}% change in port congestion`}
          color={port > 0 ? 'text-orange-400' : 'text-green-400'}
        />

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <div className="flex gap-3">
          <button
            onClick={run}
            disabled={running}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {running ? 'Running...' : 'Run Simulation'}
          </button>
          <button onClick={reset} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors">
            Reset
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="text-sm font-semibold text-slate-200">Simulation Results</div>
            <div className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">{result.simulation_label}</div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Current */}
            <ScenarioCard title="Current Scenario" metrics={result.current} variant="current" />
            {/* Simulated */}
            <ScenarioCard title="Simulated Scenario" metrics={result.simulated} variant="simulated" />
          </div>

          {/* Deltas */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-4">Impact Summary — {result.affected_shipments} shipments affected</h3>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              <DeltaCard
                label="Disruption Probability"
                value={result.delta.disruption_probability_avg}
                format="pct"
              />
              <DeltaCard
                label="Expected Delay"
                value={result.delta.expected_delay_avg_hours}
                format="hours"
              />
              <DeltaCard
                label="High-Risk Shipments"
                value={result.delta.high_risk_count}
                format="count"
              />
              <DeltaCard
                label="Critical-Risk Shipments"
                value={result.delta.critical_risk_count}
                format="count"
              />
              <DeltaCard
                label="Estimated Fleet Cost"
                value={result.delta.estimated_fleet_cost}
                format="cost"
              />
              <DeltaCard
                label="Fleet Utilization"
                value={result.delta.fleet_utilization_avg}
                format="pct"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SliderControl({ label, value, onChange, description, color }: {
  label: string; value: number; onChange: (v: number) => void;
  description: string; color: string;
}) {
  return (
    <div>
      <div className="flex justify-between mb-2">
        <label className="text-sm text-slate-300 font-medium">{label}</label>
        <span className={`text-sm font-mono font-bold ${color}`}>
          {value === 0 ? '±0%' : `${value > 0 ? '+' : ''}${(value * 100).toFixed(0)}%`}
        </span>
      </div>
      <input
        type="range"
        min={-50}
        max={50}
        step={5}
        value={value * 100}
        onChange={(e) => onChange(Number(e.target.value) / 100)}
        className="w-full accent-blue-500"
      />
      <p className="text-xs text-slate-500 mt-1">{description}</p>
    </div>
  );
}

function ScenarioCard({ title, metrics, variant }: {
  title: string;
  metrics: SimulateResponse['current'];
  variant: 'current' | 'simulated';
}) {
  const bg = variant === 'current' ? 'border-slate-700' : 'border-blue-500/30';
  return (
    <div className={`bg-slate-900 rounded-xl border p-4 ${bg}`}>
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-2 h-2 rounded-full ${variant === 'current' ? 'bg-slate-400' : 'bg-blue-400'}`} />
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      </div>
      <div className="space-y-2">
        <Row label="Avg Disruption Prob." value={pct(metrics.disruption_probability_avg)} />
        <Row label="Avg Expected Delay" value={`${fmt(metrics.expected_delay_avg_hours)}h`} />
        <Row label="High-Risk Shipments" value={String(metrics.high_risk_count)} />
        <Row label="Critical-Risk" value={String(metrics.critical_risk_count)} />
        <Row label="Est. Fleet Cost" value={`$${metrics.estimated_fleet_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}`} />
        <Row label="Fleet Utilization" value={pct(metrics.fleet_utilization_avg)} />
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-200 font-medium">{value}</span>
    </div>
  );
}

function DeltaCard({ label, value, format }: { label: string; value: number; format: 'pct' | 'hours' | 'count' | 'cost' }) {
  const isNeg = value < 0;
  const isZero = Math.abs(value) < 0.0001;

  let display = '';
  if (format === 'pct') display = `${value > 0 ? '+' : ''}${(value * 100).toFixed(1)}%`;
  else if (format === 'hours') display = `${value > 0 ? '+' : ''}${value.toFixed(1)}h`;
  else if (format === 'count') display = `${value > 0 ? '+' : ''}${Math.round(value)}`;
  else if (format === 'cost') display = `${value > 0 ? '+$' : '-$'}${Math.abs(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

  const color = isZero ? 'text-slate-400' : isNeg ? 'text-green-400' : 'text-red-400';
  const Icon = isZero ? null : isNeg ? TrendingDown : TrendingUp;

  return (
    <div className="bg-slate-800/40 rounded-lg p-3">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className={`flex items-center gap-1.5 text-base font-bold ${color}`}>
        {Icon && <Icon className="w-4 h-4" />}
        {display}
      </div>
    </div>
  );
}
