'use client';
import { useEffect, useState } from 'react';
import { AlertTriangle, ChevronRight, RefreshCw } from 'lucide-react';
import { api, type Shipment, type PredictResponse } from '@/lib/api';
import { riskBg, pct, fmt } from '@/lib/utils';

export default function RiskCenterPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [selected, setSelected] = useState<Shipment | null>(null);
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [predLoading, setPredLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.shipments({ limit: 100 });
      // Sort by risk score desc
      const sorted = [...r.shipments].sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));
      setShipments(sorted);
    } catch (e) { setError(String(e)); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const investigate = async (s: Shipment) => {
    setSelected(s);
    setPrediction(null);
    setPredLoading(true);
    try {
      const res = await api.predict({
        shipment_id: s.shipment_id,
        weather_severity: s.weather_severity,
        traffic_level: s.traffic_level,
        port_congestion: s.port_congestion,
        warehouse_delay_hours: s.warehouse_delay_hours,
        supplier_risk: s.supplier_risk,
        vehicle_utilization: s.vehicle_utilization,
        historical_delay_hours: s.historical_delay_hours,
        delivery_deadline_hours: s.delivery_deadline_hours,
        distance_km: s.distance_km,
        cargo_weight_kg: s.cargo_weight_kg,
        priority: s.priority,
      });
      setPrediction(res);
    } catch (e) { console.error(e); }
    finally { setPredLoading(false); }
  };

  return (
    <div className="flex h-full">
      {/* Shipment table */}
      <div className="flex-1 p-6 space-y-4 overflow-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Risk & Disruption Center</h1>
            <p className="text-sm text-slate-400 mt-0.5">Click a shipment to investigate</p>
          </div>
          <button onClick={load} className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>

        {loading ? (
          <div className="space-y-2">{[...Array(8)].map((_, i) => <div key={i} className="h-12 bg-slate-900 rounded-lg animate-pulse" />)}</div>
        ) : error ? (
          <p className="text-red-400 text-sm">{error}</p>
        ) : (
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800 bg-slate-900/80">
                  <th className="px-4 py-3 font-medium">Shipment</th>
                  <th className="px-4 py-3 font-medium">Route</th>
                  <th className="px-4 py-3 font-medium">Priority</th>
                  <th className="px-4 py-3 font-medium">Risk Level</th>
                  <th className="px-4 py-3 font-medium">Prob.</th>
                  <th className="px-4 py-3 font-medium">Delay</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {shipments.slice(0, 50).map((s) => (
                  <tr
                    key={s.shipment_id}
                    onClick={() => investigate(s)}
                    className={`cursor-pointer hover:bg-slate-800/50 transition-colors ${selected?.shipment_id === s.shipment_id ? 'bg-blue-900/20 border-l-2 border-l-blue-500' : ''}`}
                  >
                    <td className="px-4 py-2.5 font-mono text-xs text-blue-400">{s.shipment_id}</td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs">{s.origin} → {s.destination}</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                        s.priority === 'CRITICAL' ? 'bg-red-900/50 text-red-300'
                        : s.priority === 'HIGH' ? 'bg-orange-900/50 text-orange-300'
                        : s.priority === 'MEDIUM' ? 'bg-blue-900/50 text-blue-300'
                        : 'bg-slate-700 text-slate-300'
                      }`}>{s.priority}</span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${riskBg(s.risk_level)}`}>
                        {s.risk_level || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs">{pct(s.disruption_probability || 0)}</td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs">{fmt(s.expected_delay_hours || 0)}h</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${
                        s.delivery_status === 'DELAYED' ? 'bg-red-900/50 text-red-300'
                        : s.delivery_status === 'AT_RISK' ? 'bg-yellow-900/50 text-yellow-300'
                        : 'bg-green-900/50 text-green-300'
                      }`}>{s.delivery_status?.replace('_', ' ')}</span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-600">
                      <ChevronRight className="w-4 h-4" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Investigation panel */}
      {selected && (
        <div className="w-80 flex-shrink-0 bg-slate-900 border-l border-slate-800 p-5 overflow-auto">
          <h2 className="text-sm font-bold text-white mb-4">Investigation: {selected.shipment_id}</h2>

          {/* Route */}
          <div className="bg-slate-800/50 rounded-lg p-3 mb-4 space-y-1.5">
            <div className="text-xs text-slate-500">Route</div>
            <div className="text-sm text-slate-200">{selected.origin} → {selected.destination}</div>
            <div className="text-xs text-slate-400">{fmt(selected.distance_km, 0)} km · {fmt(selected.cargo_weight_kg, 0)} kg cargo</div>
          </div>

          {predLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => <div key={i} className="h-10 bg-slate-800 rounded animate-pulse" />)}
            </div>
          ) : prediction ? (
            <PredictionPanel s={selected} p={prediction} />
          ) : null}
        </div>
      )}
    </div>
  );
}

function PredictionPanel({ s, p }: { s: Shipment; p: PredictResponse }) {
  return (
    <div className="space-y-4">
      {/* Risk summary */}
      <div className={`rounded-lg border p-3 ${riskBg(p.risk_level)}`}>
        <div className="text-xs font-medium mb-2 opacity-70">ML Risk Assessment</div>
        <div className="text-2xl font-bold">{p.risk_level}</div>
        <div className="text-sm mt-1">Score: {(p.risk_score * 100).toFixed(0)}%</div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-slate-800/50 rounded-lg p-2.5">
          <div className="text-xs text-slate-500">Disruption Prob.</div>
          <div className="text-lg font-bold text-white">{pct(p.disruption_probability)}</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-2.5">
          <div className="text-xs text-slate-500">Expected Delay</div>
          <div className="text-lg font-bold text-white">{fmt(p.expected_delay_hours)}h</div>
        </div>
      </div>

      {/* SHAP factors */}
      <div>
        <div className="text-xs text-slate-500 mb-2 font-medium">Top contributing factors</div>
        <div className="text-xs text-slate-600 mb-3 italic">Model attribution — not causal proof</div>
        <div className="space-y-2">
          {p.risk_factors.slice(0, 6).map((f) => (
            <div key={f.factor}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">{f.label}</span>
                <span className={f.contribution > 0 ? 'text-orange-400' : 'text-green-400'}>
                  {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(4)}
                </span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${f.contribution > 0 ? 'bg-orange-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(Math.abs(f.contribution) * 800 + 5, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended action */}
      <div className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-3">
        <div className="text-xs text-blue-400 font-medium mb-1">Recommended Action</div>
        <p className="text-xs text-slate-300 leading-relaxed">{p.recommended_action}</p>
      </div>
    </div>
  );
}
