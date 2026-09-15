'use client';
import { useEffect, useState } from 'react';
import { Zap, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { api, type Vehicle, type OptimizeResponse } from '@/lib/api';
import { pct, fmt } from '@/lib/utils';

export default function FleetOptimizerPage() {
  const [fleet, setFleet] = useState<Vehicle[]>([]);
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.fleet().then((r) => { setFleet(r.vehicles); setLoading(false); }).catch((e) => { setError(String(e)); setLoading(false); });
  }, []);

  const runOptimize = async () => {
    setOptimizing(true);
    setError('');
    try {
      const r = await api.optimize({});
      setResult(r);
    } catch (e) { setError(String(e)); }
    finally { setOptimizing(false); }
  };

  const feasible = result?.assignments.filter((a) => a.feasible) ?? [];
  const infeasible = result?.assignments.filter((a) => !a.feasible) ?? [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Fleet Optimizer</h1>
          <p className="text-sm text-slate-400 mt-0.5">OR-Tools constraint optimization · capacity, priority, cost</p>
        </div>
        <button
          onClick={runOptimize}
          disabled={optimizing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {optimizing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {optimizing ? 'Optimizing...' : 'Optimize Fleet'}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm bg-red-900/20 border border-red-500/20 rounded-lg p-3">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fleet status */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Fleet Status</h3>
          {loading ? (
            <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i} className="h-10 bg-slate-800 rounded animate-pulse" />)}</div>
          ) : (
            <div className="space-y-2 max-h-80 overflow-auto">
              {fleet.slice(0, 20).map((v) => (
                <div key={v.vehicle_id} className={`flex items-center justify-between p-2.5 rounded-lg border ${v.availability ? 'bg-slate-800/30 border-slate-700' : 'bg-slate-900/50 border-slate-800 opacity-50'}`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${v.availability ? 'bg-green-400' : 'bg-slate-600'}`} />
                    <div>
                      <div className="text-xs font-medium text-slate-200">{v.vehicle_id}</div>
                      <div className="text-xs text-slate-500">{v.vehicle_type} · {v.current_location}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-300">{pct(v.current_utilization)}</div>
                    <div className="text-xs text-slate-500">{fmt(v.capacity_kg, 0)} kg · ${fmt(v.operating_cost_per_km, 2)}/km</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Optimization result */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Optimization Result</h3>
          {!result ? (
            <div className="flex flex-col items-center justify-center h-48 text-slate-500 gap-2">
              <Zap className="w-8 h-8 opacity-30" />
              <p className="text-sm">Click "Optimize Fleet" to run OR-Tools solver</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Metrics */}
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Assignments" value={`${feasible.length}`} sub={`${infeasible.length} unassigned`} />
                <Metric label="Total Cost" value={`$${result.total_estimated_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}`} sub={`${result.optimization_time_ms.toFixed(0)}ms`} />
                <Metric label="Utilization Before" value={pct(result.utilization_before)} sub="avg fleet" />
                <Metric label="Utilization After" value={pct(result.utilization_after)} sub={`+${pct(result.utilization_after - result.utilization_before)}`} />
              </div>

              <div className="text-xs text-slate-500">
                Solver: <span className={`font-mono ${result.solver_status === 'OPTIMAL' ? 'text-green-400' : 'text-yellow-400'}`}>{result.solver_status}</span>
                {' · '}{result.high_risk_reduced} high-priority assigned
              </div>

              {/* Assignments */}
              <div className="space-y-1.5 max-h-52 overflow-auto">
                {result.assignments.filter(a => a.feasible).slice(0, 15).map((a) => (
                  <div key={a.shipment_id} className="flex items-center gap-2 p-2 bg-slate-800/40 rounded-lg">
                    <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-mono text-blue-400">{a.shipment_id}</span>
                      <span className="text-xs text-slate-500 mx-1">→</span>
                      <span className="text-xs text-slate-300">{a.vehicle_id}</span>
                    </div>
                    <span className="text-xs text-slate-400">${fmt(a.estimated_cost, 0)}</span>
                  </div>
                ))}
                {infeasible.slice(0, 5).map((a) => (
                  <div key={a.shipment_id} className="flex items-center gap-2 p-2 bg-slate-900/60 rounded-lg opacity-60">
                    <XCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-mono text-slate-400">{a.shipment_id}</span>
                      <span className="text-xs text-slate-600 ml-2">{a.reason}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="bg-slate-800/40 rounded-lg p-2.5">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-base font-bold text-white">{value}</div>
      <div className="text-xs text-slate-500">{sub}</div>
    </div>
  );
}
