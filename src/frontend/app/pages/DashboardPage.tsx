'use client';
import { useEffect, useState } from 'react';
import {
  AlertTriangle, TrendingUp, Truck, Package, RefreshCw, ExternalLink,
  CheckCircle2, Clock, Activity, ShieldAlert, Sparkles, X, ArrowRight
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { api, isConnectionError, formatErrorMessage, type MetricsResponse, type Shipment } from '@/lib/api';
import { useOperations } from '@/lib/OperationsContext';
import { riskBg, riskBarColor, pct, fmt } from '@/lib/utils';

const PIE_COLORS: Record<string, string> = {
  LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444',
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [topRisk, setTopRisk] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const {
    appliedOptimization,
    optimizationTime,
    lastAnalysisTime,
    lastSimulationTime,
    activityLog,
    resetOptimization,
    getAdjustedKPIs,
  } = useOperations();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [m, hr] = await Promise.all([api.metrics(), api.highRisk()]);
      setMetrics(m);
      setTopRisk(hr.shipments.slice(0, 8));
    } catch (e) {
      setError(formatErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState msg={error} onRetry={load} />;
  if (!metrics) return null;

  const { risk_distribution, delay_trend, region_risk } = metrics;
  const liveKPIs = getAdjustedKPIs(metrics.kpis);

  // Dynamic recommendations derived from real data
  const recommendations: Array<{ id: string; title: string; desc: string; priority: 'CRITICAL' | 'HIGH' | 'INFO' }> = [];

  const highestRiskRegion = [...region_risk].sort((a, b) => b.avg_risk_score - a.avg_risk_score)[0];
  if (highestRiskRegion && highestRiskRegion.avg_risk_score > 0.45) {
    recommendations.push({
      id: 'rec-reg',
      title: `Prioritize ${highestRiskRegion.region} Corridor`,
      desc: `Highest average disruption risk (${(highestRiskRegion.avg_risk_score * 100).toFixed(0)}% across ${highestRiskRegion.shipment_count} shipments). Re-route or pre-assign backup carriers.`,
      priority: highestRiskRegion.avg_risk_score > 0.65 ? 'CRITICAL' : 'HIGH',
    });
  }

  if (liveKPIs.critical_risk_count > 0 || liveKPIs.high_risk_count > 0) {
    recommendations.push({
      id: 'rec-risk',
      title: `Mitigate ${liveKPIs.critical_risk_count + liveKPIs.high_risk_count} High/Critical Risk Shipments`,
      desc: `${liveKPIs.critical_risk_count} critical shipments require driver rerouting or urgent warehouse prioritization to prevent ETA breaches.`,
      priority: 'CRITICAL',
    });
  }

  if (delay_trend.length > 0 && delay_trend[0].avg_delay_hours > 3.0) {
    recommendations.push({
      id: 'rec-delay',
      title: `Address Origin Bottleneck in ${delay_trend[0].label}`,
      desc: `Origin averages ${delay_trend[0].avg_delay_hours.toFixed(1)}h delay. Coordinate with dispatch facilities to relieve dock congestion.`,
      priority: 'HIGH',
    });
  }

  if (appliedOptimization) {
    const assigned = appliedOptimization.assignments.filter((a) => a.feasible).length;
    recommendations.push({
      id: 'rec-opt',
      title: `OR-Tools Fleet Plan Active`,
      desc: `${assigned} vehicles reallocated. Utilization increased to ${(appliedOptimization.utilization_after * 100).toFixed(0)}% with ${appliedOptimization.high_risk_reduced} high-priority assignments secured.`,
      priority: 'INFO',
    });
  } else {
    recommendations.push({
      id: 'rec-opt-prompt',
      title: `Run Fleet Optimization`,
      desc: `Current fleet utilization is ${pct(liveKPIs.fleet_utilization_avg)}. Execute OR-Tools solver to balance capacity and reduce total transit costs.`,
      priority: 'INFO',
    });
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header & Status Bar */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-white">Executive Dashboard</h1>
            <p className="text-sm text-slate-400 mt-0.5">Live operational overview — {liveKPIs.total_shipments} active shipments</p>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={load} className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors cursor-pointer">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
          </div>
        </div>

        {/* System Status & Last Updated Bar */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-slate-300 font-medium">System Status: <strong className="text-emerald-400 font-semibold">Operational</strong></span>
            <span className="text-slate-600 hidden md:inline">|</span>
            <span className="text-slate-500 hidden md:inline">ML Engine (XGBoost + SHAP) & OR-Tools Solver</span>
          </div>

          <div className="flex items-center gap-4 text-slate-400">
            <div>
              <span className="text-slate-500">Last Analysis: </span>
              <span className="text-slate-200 font-mono">{lastAnalysisTime || 'Continuous'}</span>
            </div>
            <div>
              <span className="text-slate-500">Last Optimization: </span>
              <span className="text-slate-200 font-mono">{optimizationTime || 'None in session'}</span>
            </div>
            <div className="hidden lg:block">
              <span className="text-slate-500">Last Simulation: </span>
              <span className="text-slate-200 font-mono">{lastSimulationTime || 'None in session'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Applied Optimization Banner */}
      {appliedOptimization && (
        <div className="bg-gradient-to-r from-blue-950/80 via-indigo-950/60 to-slate-900 border border-blue-500/40 rounded-xl p-4 shadow-lg shadow-blue-950/40">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-400 mt-0.5">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider bg-blue-500 text-white px-2 py-0.5 rounded">
                    Optimization Applied
                  </span>
                  <span className="text-xs text-slate-400">at {optimizationTime}</span>
                </div>
                <p className="text-sm text-slate-200 mt-1">
                  Live dashboard KPIs adjusted by OR-Tools solver allocation.
                </p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs">
                  <span className="text-slate-400">
                    Fleet Utilization: <strong className="text-blue-300 font-mono">{pct(appliedOptimization.utilization_before)} → {pct(appliedOptimization.utilization_after)}</strong> ({pct(appliedOptimization.utilization_after - appliedOptimization.utilization_before)} gain)
                  </span>
                  <span className="text-slate-400">
                    High-Risk Mitigated: <strong className="text-emerald-300 font-mono">{appliedOptimization.high_risk_reduced} shipments</strong>
                  </span>
                  <span className="text-slate-400">
                    Est. Cost: <strong className="text-slate-200 font-mono">${appliedOptimization.total_estimated_cost.toLocaleString('en-US', { maximumFractionDigits: 0 })}</strong>
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={resetOptimization}
              className="self-start md:self-center flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-colors cursor-pointer"
            >
              <X className="w-3.5 h-3.5" /> Revert to Baseline
            </button>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Shipments"
          value={String(liveKPIs.total_shipments)}
          sub={`${liveKPIs.disrupted_count} disrupted`}
          icon={<Package className="w-5 h-5 text-blue-400" />}
          color="border-blue-500/20"
        />
        <KPICard
          label="High / Critical Risk"
          value={`${liveKPIs.high_risk_count + liveKPIs.critical_risk_count}`}
          sub={appliedOptimization ? `${liveKPIs.critical_risk_count} critical (${appliedOptimization.high_risk_reduced} mitigated)` : `${liveKPIs.critical_risk_count} critical`}
          icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
          color="border-red-500/20"
          alert={liveKPIs.critical_risk_count > 0}
        />
        <KPICard
          label="On-Time Rate"
          value={pct(liveKPIs.on_time_rate)}
          sub={`${liveKPIs.at_risk_count} at risk`}
          icon={<TrendingUp className="w-5 h-5 text-green-400" />}
          color="border-green-500/20"
        />
        <KPICard
          label="Fleet Utilization"
          value={pct(liveKPIs.fleet_utilization_avg)}
          sub={appliedOptimization ? `Optimal: ${pct(appliedOptimization.utilization_after)}` : `Avg disruption: ${pct(liveKPIs.avg_disruption_probability)}`}
          icon={<Truck className="w-5 h-5 text-purple-400" />}
          color="border-purple-500/20"
        />
      </div>

      {/* Dynamic Recommended Actions & Live Operations Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recommended Actions */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-slate-200">Dynamic Operational Actions</h3>
            </div>
            <span className="text-xs text-slate-500 font-mono">Live derived</span>
          </div>

          <div className="space-y-2.5 flex-1">
            {recommendations.map((rec) => (
              <div
                key={rec.id}
                className={`p-3 rounded-lg border text-xs ${
                  rec.priority === 'CRITICAL'
                    ? 'bg-red-950/20 border-red-500/30'
                    : rec.priority === 'HIGH'
                    ? 'bg-orange-950/20 border-orange-500/30'
                    : 'bg-blue-950/20 border-blue-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-200">{rec.title}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] font-medium uppercase ${
                      rec.priority === 'CRITICAL'
                        ? 'bg-red-900/60 text-red-300'
                        : rec.priority === 'HIGH'
                        ? 'bg-orange-900/60 text-orange-300'
                        : 'bg-blue-900/60 text-blue-300'
                    }`}
                  >
                    {rec.priority}
                  </span>
                </div>
                <p className="text-slate-400 leading-relaxed">{rec.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Live Operations Activity */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-slate-200">Live Operations Activity</h3>
            </div>
            <span className="text-xs text-slate-500 font-mono">{activityLog.length} events</span>
          </div>

          <div className="space-y-2 flex-1 max-h-64 overflow-y-auto pr-1">
            {activityLog.map((act) => (
              <div key={act.id} className="flex items-start gap-2.5 p-2 bg-slate-800/40 rounded-lg border border-slate-800/60">
                <div className="mt-0.5 flex-shrink-0">
                  {act.type === 'optimization' ? (
                    <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                  ) : act.type === 'investigation' ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
                  ) : act.type === 'simulation' ? (
                    <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
                  ) : act.type === 'copilot' ? (
                    <Clock className="w-3.5 h-3.5 text-teal-400" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <p className="text-xs font-medium text-slate-200 truncate">{act.title}</p>
                    <span className="text-[10px] text-slate-500 font-mono flex-shrink-0">{act.timestamp}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{act.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Risk Distribution */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={risk_distribution}
                dataKey="count"
                nameKey="risk_level"
                cx="50%"
                cy="50%"
                outerRadius={60}
              >
                {risk_distribution.map((entry) => (
                  <Cell key={entry.risk_level} fill={PIE_COLORS[entry.risk_level] || '#64748b'} />
                ))}
              </Pie>
              <Tooltip formatter={(v: unknown) => [`${v} shipments`]} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
              <Legend
                formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 11 }}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Delay by Region */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Avg Delay by Origin City</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={delay_trend.slice(0, 8)} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: 12 }}
                formatter={(v: unknown) => [`${Number(v).toFixed(1)}h`, 'Avg Delay']}
              />
              <Bar dataKey="avg_delay_hours" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Region risk */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold text-slate-200 mb-4">Risk Score by Origin</h3>
        <ResponsiveContainer width="100%" height={150}>
          <BarChart data={region_risk.slice(0, 10)} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <XAxis dataKey="region" tick={{ fontSize: 11, fill: '#94a3b8' }} />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 1]} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', fontSize: 12 }}
              formatter={(v: unknown) => [`${(Number(v) * 100).toFixed(1)}%`, 'Risk Score']}
            />
            <Bar dataKey="avg_risk_score" radius={[3, 3, 0, 0]}>
              {region_risk.slice(0, 10).map((entry) => (
                <Cell key={entry.region} fill={
                  entry.avg_risk_score > 0.75 ? '#ef4444'
                  : entry.avg_risk_score > 0.55 ? '#f97316'
                  : entry.avg_risk_score > 0.30 ? '#eab308'
                  : '#22c55e'
                } />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top-risk shipments table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
        <h3 className="text-sm font-semibold text-slate-200 mb-4">Top-Risk Shipments</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-800">
                <th className="pb-2 pr-4 font-medium">ID</th>
                <th className="pb-2 pr-4 font-medium">Route</th>
                <th className="pb-2 pr-4 font-medium">Priority</th>
                <th className="pb-2 pr-4 font-medium">Risk</th>
                <th className="pb-2 pr-4 font-medium">Disruption Prob.</th>
                <th className="pb-2 pr-4 font-medium">Expected Delay</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {topRisk.map((s) => (
                <tr key={s.shipment_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 pr-4 font-mono text-xs text-blue-400">{s.shipment_id}</td>
                  <td className="py-2.5 pr-4 text-slate-300">{s.origin} → {s.destination}</td>
                  <td className="py-2.5 pr-4">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      s.priority === 'CRITICAL' ? 'bg-red-900/50 text-red-300'
                      : s.priority === 'HIGH' ? 'bg-orange-900/50 text-orange-300'
                      : s.priority === 'MEDIUM' ? 'bg-blue-900/50 text-blue-300'
                      : 'bg-slate-700 text-slate-300'
                    }`}>{s.priority}</span>
                  </td>
                  <td className="py-2.5 pr-4">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium border ${riskBg(s.risk_level)}`}>
                      {s.risk_level}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${(s.disruption_probability || 0) * 100}%`,
                            background: riskBarColor(s.risk_level),
                          }}
                        />
                      </div>
                      <span className="text-slate-300 text-xs">{pct(s.disruption_probability || 0)}</span>
                    </div>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-300">{fmt(s.expected_delay_hours || 0)}h</td>
                  <td className="py-2.5">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                      s.delivery_status === 'DELAYED' ? 'bg-red-900/50 text-red-300'
                      : s.delivery_status === 'AT_RISK' ? 'bg-yellow-900/50 text-yellow-300'
                      : 'bg-green-900/50 text-green-300'
                    }`}>{s.delivery_status?.replace('_', ' ')}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


function KPICard({ label, value, sub, icon, color, alert }: {
  label: string; value: string; sub: string; icon: React.ReactNode;
  color: string; alert?: boolean;
}) {
  return (
    <div className={`bg-slate-900 rounded-xl border p-4 ${color} ${alert ? 'ring-1 ring-red-500/30' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-slate-400 font-medium uppercase tracking-wide">{label}</p>
        {icon}
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{sub}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="p-6 space-y-6">
      <div className="h-8 bg-slate-800 rounded-lg w-48 animate-pulse" />
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-slate-900 rounded-xl border border-slate-800 animate-pulse" />
        ))}
      </div>
      <div className="h-64 bg-slate-900 rounded-xl border border-slate-800 animate-pulse" />
    </div>
  );
}

function ErrorState({ msg, onRetry }: { msg: string; onRetry: () => void }) {
  const isBackendDown = isConnectionError(msg) || !msg || msg.includes('Backend server is not running');
  const displayMsg = formatErrorMessage(msg);

  return (
    <div className="p-6 flex flex-col items-center justify-center min-h-[75vh]">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-6">
        <div className="flex flex-col items-center text-center gap-3">
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-full text-red-400">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">
              {isBackendDown ? 'Backend server is not running.' : 'Failed to load dashboard data'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {isBackendDown
                ? 'Unable to connect to the FastAPI backend API at http://localhost:8000.'
                : displayMsg}
            </p>
          </div>
        </div>

        {/* Setup Instructions */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs text-left">
          <div className="text-slate-400 font-sans font-semibold text-xs uppercase tracking-wider">
            Setup Instructions
          </div>

          <div>
            <span className="text-blue-400 font-semibold block mb-1">Backend:</span>
            <div className="bg-slate-900 px-3 py-2 rounded border border-slate-800 text-slate-200 select-all whitespace-pre">
cd src/backend
python -m uvicorn main:app --port 8000
            </div>
          </div>

          <div>
            <span className="text-green-400 font-semibold block mb-1">Frontend:</span>
            <div className="bg-slate-900 px-3 py-2 rounded border border-slate-800 text-slate-200 select-all whitespace-pre">
cd src/frontend
npm run dev
            </div>
          </div>
        </div>

        {/* Health Check Endpoint */}
        <div className="bg-slate-950/50 border border-slate-800/60 rounded-lg p-3 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="text-slate-400 font-medium">Health Check:</span>
          <a
            href="http://localhost:8000/api/health"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1.5 break-all"
          >
            http://localhost:8000/api/health
            <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
          </a>
        </div>

        {/* Retry Button */}
        <button
          onClick={onRetry}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-600/20 cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    </div>
  );
}
