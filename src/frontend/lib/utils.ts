import type { RiskLevel, Priority } from '@/lib/api';

export function riskColor(level?: RiskLevel | string): string {
  switch (level) {
    case 'CRITICAL': return 'text-red-400';
    case 'HIGH': return 'text-orange-400';
    case 'MEDIUM': return 'text-yellow-400';
    case 'LOW': return 'text-green-400';
    default: return 'text-slate-400';
  }
}

export function riskBg(level?: RiskLevel | string): string {
  switch (level) {
    case 'CRITICAL': return 'bg-red-500/15 border-red-500/30 text-red-300';
    case 'HIGH': return 'bg-orange-500/15 border-orange-500/30 text-orange-300';
    case 'MEDIUM': return 'bg-yellow-500/15 border-yellow-500/30 text-yellow-300';
    case 'LOW': return 'bg-green-500/15 border-green-500/30 text-green-300';
    default: return 'bg-slate-700/50 border-slate-600 text-slate-300';
  }
}

export function priorityBg(p?: Priority | string): string {
  switch (p) {
    case 'CRITICAL': return 'bg-red-900/50 text-red-300';
    case 'HIGH': return 'bg-orange-900/50 text-orange-300';
    case 'MEDIUM': return 'bg-blue-900/50 text-blue-300';
    case 'LOW': return 'bg-slate-700/50 text-slate-300';
    default: return 'bg-slate-700/50 text-slate-300';
  }
}

export function statusBg(s?: string): string {
  switch (s) {
    case 'DELAYED': return 'bg-red-900/50 text-red-300';
    case 'AT_RISK': return 'bg-yellow-900/50 text-yellow-300';
    case 'ON_TIME': return 'bg-green-900/50 text-green-300';
    default: return 'bg-slate-700/50 text-slate-300';
  }
}

export function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

export function fmt(v: number, decimals = 1): string {
  return v.toFixed(decimals);
}

export function riskBarColor(level?: string): string {
  switch (level) {
    case 'CRITICAL': return '#ef4444';
    case 'HIGH': return '#f97316';
    case 'MEDIUM': return '#eab308';
    case 'LOW': return '#22c55e';
    default: return '#64748b';
  }
}
