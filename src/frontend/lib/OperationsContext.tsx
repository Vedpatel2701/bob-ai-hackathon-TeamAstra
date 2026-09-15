'use client';
import React, { createContext, useContext, useState, ReactNode } from 'react';
import type { OptimizeResponse, MetricsResponse } from './api';

export interface ActivityItem {
  id: string;
  timestamp: string;
  type: 'optimization' | 'investigation' | 'simulation' | 'copilot' | 'system';
  title: string;
  description: string;
}

interface OperationsContextType {
  appliedOptimization: OptimizeResponse | null;
  optimizationTime: string | null;
  lastAnalysisTime: string | null;
  lastSimulationTime: string | null;
  activityLog: ActivityItem[];
  applyOptimization: (opt: OptimizeResponse) => void;
  resetOptimization: () => void;
  recordInvestigation: (shipmentId: string, riskLevel: string, prob: number, delay: number) => void;
  recordSimulation: (summary: string, affected: number, deltaHighRisk: number) => void;
  recordCopilot: (query: string, tools: string[]) => void;
  getAdjustedKPIs: (baseKPIs: MetricsResponse['kpis']) => MetricsResponse['kpis'];
}

const OperationsContext = createContext<OperationsContextType | undefined>(undefined);

export function OperationsProvider({ children }: { children: ReactNode }) {
  const [appliedOptimization, setAppliedOptimization] = useState<OptimizeResponse | null>(null);
  const [optimizationTime, setOptimizationTime] = useState<string | null>(null);
  const [lastAnalysisTime, setLastAnalysisTime] = useState<string | null>(null);
  const [lastSimulationTime, setLastSimulationTime] = useState<string | null>(null);
  const [activityLog, setActivityLog] = useState<ActivityItem[]>([
    {
      id: 'init-1',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      type: 'system',
      title: 'Operations System Initialized',
      description: 'Connected to live ML risk engine and OR-Tools fleet solver.',
    },
  ]);

  const addActivity = (item: Omit<ActivityItem, 'id' | 'timestamp'>) => {
    const newEntry: ActivityItem = {
      ...item,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    setActivityLog((prev) => [newEntry, ...prev.slice(0, 19)]); // Keep latest 20 events
  };

  const applyOptimization = (opt: OptimizeResponse) => {
    setAppliedOptimization(opt);
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setOptimizationTime(now);
    const feasibleCount = opt.assignments.filter((a) => a.feasible).length;
    addActivity({
      type: 'optimization',
      title: 'Fleet Optimization Applied',
      description: `${feasibleCount} vehicle assignments updated · Utilization ${(opt.utilization_before * 100).toFixed(0)}% → ${(opt.utilization_after * 100).toFixed(0)}% · ${opt.high_risk_reduced} high-risk shipments mitigated`,
    });
  };

  const resetOptimization = () => {
    setAppliedOptimization(null);
    setOptimizationTime(null);
    addActivity({
      type: 'system',
      title: 'Optimization Plan Cleared',
      description: 'Operations reverted to baseline schedule.',
    });
  };

  const recordInvestigation = (shipmentId: string, riskLevel: string, prob: number, delay: number) => {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLastAnalysisTime(now);
    addActivity({
      type: 'investigation',
      title: `Shipment ${shipmentId} Flagged & Analyzed`,
      description: `Risk: ${riskLevel} (${(prob * 100).toFixed(1)}% prob) · Expected delay: ${delay.toFixed(1)}h · SHAP factors calculated`,
    });
  };

  const recordSimulation = (summary: string, affected: number, deltaHighRisk: number) => {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLastSimulationTime(now);
    addActivity({
      type: 'simulation',
      title: 'Scenario Simulation Executed',
      description: `${summary} · ${affected} shipments evaluated (Δ high-risk: ${deltaHighRisk >= 0 ? '+' : ''}${deltaHighRisk})`,
    });
  };

  const recordCopilot = (query: string, tools: string[]) => {
    const displayQuery = query.length > 40 ? query.substring(0, 37) + '...' : query;
    addActivity({
      type: 'copilot',
      title: 'Copilot Investigation Completed',
      description: `"${displayQuery}" · Tools: ${tools.join(', ') || 'RAG Policy'}`,
    });
  };

  const getAdjustedKPIs = (baseKPIs: MetricsResponse['kpis']): MetricsResponse['kpis'] => {
    if (!appliedOptimization) return baseKPIs;

    const reduced = appliedOptimization.high_risk_reduced || 0;
    const newHighRisk = Math.max(0, baseKPIs.high_risk_count - reduced);
    const newDisrupted = Math.max(0, baseKPIs.disrupted_count - Math.round(reduced * 0.7));
    const newAtRisk = Math.max(0, baseKPIs.at_risk_count - reduced);
    const onTimeBoost = baseKPIs.total_shipments > 0 ? (reduced * 0.8) / baseKPIs.total_shipments : 0;

    return {
      ...baseKPIs,
      high_risk_count: newHighRisk,
      disrupted_count: newDisrupted,
      at_risk_count: newAtRisk,
      fleet_utilization_avg: appliedOptimization.utilization_after,
      on_time_rate: Math.min(0.99, baseKPIs.on_time_rate + onTimeBoost),
      avg_disruption_probability: Math.max(0.05, baseKPIs.avg_disruption_probability - (reduced * 0.015)),
    };
  };

  return (
    <OperationsContext.Provider
      value={{
        appliedOptimization,
        optimizationTime,
        lastAnalysisTime,
        lastSimulationTime,
        activityLog,
        applyOptimization,
        resetOptimization,
        recordInvestigation,
        recordSimulation,
        recordCopilot,
        getAdjustedKPIs,
      }}
    >
      {children}
    </OperationsContext.Provider>
  );
}

export function useOperations() {
  const context = useContext(OperationsContext);
  if (!context) {
    throw new Error('useOperations must be used within an OperationsProvider');
  }
  return context;
}
