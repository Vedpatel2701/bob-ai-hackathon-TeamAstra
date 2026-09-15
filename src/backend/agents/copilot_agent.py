"""Agentic AI copilot — orchestrates tools to answer operational questions."""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Tool registry ──────────────────────────────────────────────────────────────

TOOL_DESCRIPTIONS = {
    "get_shipments": "Retrieve current shipment list with status and risk information",
    "get_high_risk_shipments": "Get shipments with HIGH or CRITICAL risk level",
    "get_shipment_details": "Get detailed information about a specific shipment by ID",
    "predict_delay": "Predict disruption probability and expected delay for a shipment",
    "calculate_risk": "Calculate the composite risk score for a shipment",
    "analyze_root_cause": "Identify the top contributing factors to a shipment's predicted risk",
    "get_fleet_status": "Get current fleet availability and utilization",
    "optimize_fleet": "Run the fleet optimizer to produce recommended vehicle assignments",
    "run_simulation": "Simulate the effect of changed conditions on risk and fleet metrics",
    "get_policy": "Retrieve relevant operational policy for a given situation",
}

# Intent patterns mapped to primary tools
INTENT_PATTERNS = [
    (r"(highest.?risk|most.?at.?risk|critical|urgent|immediate attention)", ["get_high_risk_shipments"]),
    (r"(why.*(delayed|risk|at risk|disrupted)|root.?cause|factors|contributing)", ["get_shipment_details", "analyze_root_cause"]),
    (r"(what.*happen|simulate|if.*weather|if.*traffic|scenario|what.?if)", ["run_simulation"]),
    (r"(optimize|fleet.*assign|assign.*vehicle|best.*vehicle)", ["get_fleet_status", "optimize_fleet"]),
    (r"(fleet|vehicles?|available|availability|utilization)", ["get_fleet_status"]),
    (r"(miss.*deadline|deadline|on.?time|overdue)", ["get_high_risk_shipments"]),
    (r"(policy|procedure|protocol|playbook|rule|should we)", ["get_policy"]),
    (r"(recommend|should I do|action|next step)", ["get_shipment_details", "analyze_root_cause"]),
    (r"(sh-\d+|shipment\s+\d+|shipment\s+sh)", ["get_shipment_details", "analyze_root_cause"]),
    (r"(today.*shipment|all.*shipment|show.*shipment|list.*shipment)", ["get_shipments"]),
]


def _extract_shipment_id(text: str) -> Optional[str]:
    """Extract shipment ID from user message."""
    match = re.search(r"(SHP?-\d+)", text.upper())
    if match:
        sid = match.group(1)
        if sid.startswith("SHP-"):
            sid = "SH-" + sid[4:]
        return sid
    match = re.search(r"shipment\s+#?(\d+)", text.lower())
    if match:
        return f"SH-{match.group(1)}"
    return None


def _select_tools(message: str) -> list[str]:
    """Select appropriate tools based on message intent."""
    msg_lower = message.lower()
    selected = []
    for pattern, tools in INTENT_PATTERNS:
        if re.search(pattern, msg_lower):
            for t in tools:
                if t not in selected:
                    selected.append(t)
            if len(selected) >= 3:
                break
    if not selected:
        selected = ["get_shipments"]
    return selected


class SupplyChainAgent:
    """Orchestrates tool calls and generates structured responses."""

    def __init__(self, data_service, ml_service, risk_engine_fn, optimizer_fn, sim_fn):
        self._data = data_service
        self._ml = ml_service
        self._risk = risk_engine_fn
        self._optimize = optimizer_fn
        self._sim = sim_fn

        # Load RAG retriever
        try:
            rag_path = Path(__file__).resolve().parents[2] / "rag"
            sys.path.insert(0, str(rag_path))
            from retrieval.retriever import get_retriever
            self._retriever = get_retriever()
        except Exception as e:
            logger.warning(f"RAG retriever unavailable: {e}")
            self._retriever = None

    def answer(self, message: str, context: Optional[dict] = None) -> dict:
        """Process a user message and return a structured copilot response."""
        tools_used = []
        sources = []
        shipment_id = _extract_shipment_id(message)
        selected_tools = _select_tools(message)

        # ── Execute tools ──────────────────────────────────────────────────────
        results = {}
        for tool_name in selected_tools:
            try:
                result, summary = self._execute_tool(tool_name, message, shipment_id, results)
                results[tool_name] = result
                tools_used.append({
                    "tool_name": tool_name,
                    "arguments": {"shipment_id": shipment_id} if shipment_id else {},
                    "result_summary": summary,
                })
            except Exception as e:
                logger.warning(f"Tool {tool_name} failed: {e}")
                tools_used.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "result_summary": f"Tool unavailable: {str(e)[:100]}",
                })

        # ── RAG retrieval ──────────────────────────────────────────────────────
        rag_context = ""
        if self._retriever:
            try:
                docs = self._retriever.retrieve(message, top_k=2)
                for doc in docs:
                    if doc["score"] > 0.05:
                        rag_context += f"\n\n[Policy: {doc['document']}]\n{doc['snippet']}"
                        sources.append(doc["document"])
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")

        # ── Generate answer ────────────────────────────────────────────────────
        answer = self._generate_answer(message, results, rag_context, shipment_id)

        confidence = 0.85 if results else 0.60

        return {
            "answer": answer,
            "tools_used": tools_used,
            "sources": sources,
            "confidence": confidence,
        }

    def _execute_tool(
        self, tool_name: str, message: str, shipment_id: Optional[str], existing_results: dict
    ) -> tuple[Any, str]:
        if tool_name == "get_shipments":
            shipments = self._data.get_shipments().head(20).to_dict(orient="records")
            return shipments, f"Retrieved {len(shipments)} shipments"

        elif tool_name == "get_high_risk_shipments":
            # Use precomputed risk cache — fast, no ML calls
            df = self._data.get_shipments()
            risk_cache = self._data.get_all_risk()
            high_risk = []
            for _, row in df.iterrows():
                sid = str(row.get("shipment_id", ""))
                risk = risk_cache.get(sid)
                if risk and risk["risk_level"] in ("HIGH", "CRITICAL"):
                    high_risk.append({**row.to_dict(), **risk})
            high_risk.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
            top_5 = high_risk[:5]
            return top_5, f"Found {len(high_risk)} high/critical risk shipments; top 5 returned"

        elif tool_name == "get_shipment_details":
            if not shipment_id:
                # Fall back to highest-risk shipment
                return self._execute_tool("get_high_risk_shipments", message, None, existing_results)
            row = self._data.get_shipment_by_id(shipment_id)
            if not row:
                return {}, f"Shipment {shipment_id} not found"
            return row, f"Retrieved details for {shipment_id}"

        elif tool_name == "predict_delay":
            target_id = shipment_id
            if not target_id and "get_high_risk_shipments" in existing_results:
                top = existing_results["get_high_risk_shipments"]
                if top:
                    target_id = top[0].get("shipment_id")
            if not target_id:
                return {}, "No shipment ID available for prediction"
            row = self._data.get_shipment_by_id(target_id)
            if not row:
                return {}, f"Shipment {target_id} not found"
            pred = self._ml.predict(row)
            return pred, (
                f"Shipment {target_id}: disruption probability "
                f"{pred['disruption_probability']:.0%}, "
                f"expected delay {pred['expected_delay_hours']:.1f}h"
            )

        elif tool_name == "calculate_risk":
            target_id = shipment_id
            if not target_id:
                return {}, "No shipment ID for risk calculation"
            # Use cache first
            cached = self._data.get_risk(target_id)
            if cached:
                return cached, f"Risk: {cached['risk_level']} (score: {cached['risk_score']:.2f})"
            return {}, f"Shipment {target_id} not found"

        elif tool_name == "analyze_root_cause":
            target_id = shipment_id
            if not target_id and "get_high_risk_shipments" in existing_results:
                top = existing_results["get_high_risk_shipments"]
                if top:
                    target_id = top[0].get("shipment_id")
            if not target_id:
                return {}, "No shipment ID for root cause analysis"
            row = self._data.get_shipment_by_id(target_id)
            if not row:
                return {}, f"Shipment {target_id} not found"
            pred = self._ml.predict(row)
            factors = pred.get("shap_factors", [])[:5]
            factor_names = [f["label"] for f in factors]
            return {
                "shipment_id": target_id,
                "disruption_probability": pred["disruption_probability"],
                "expected_delay_hours": pred["expected_delay_hours"],
                "top_factors": factors,
            }, f"Top factors for {target_id}: {', '.join(factor_names[:3])}"

        elif tool_name == "get_fleet_status":
            fleet = self._data.get_fleet().to_dict(orient="records")
            available = [v for v in fleet if v.get("availability")]
            return {
                "total": len(fleet),
                "available": len(available),
                "vehicles": fleet[:10],
            }, f"Fleet: {len(available)}/{len(fleet)} vehicles available"

        elif tool_name == "optimize_fleet":
            shipments = self._data.get_shipments().head(20).to_dict(orient="records")
            fleet = self._data.get_fleet().to_dict(orient="records")
            result = self._optimize(shipments, fleet)
            return result, (
                f"Optimization complete: {len(result.get('assignments', []))} assignments, "
                f"cost ${result.get('total_estimated_cost', 0):.0f}, "
                f"status: {result.get('solver_status', 'UNKNOWN')}"
            )

        elif tool_name == "run_simulation":
            # Extract simulation parameters from message
            w_delta = 0.2 if re.search(r"(severe|heavy|bad|wors|increas).*(weather|storm)|weather.*(increas|wors|bad|severe)", message.lower()) else (
                -0.2 if re.search(r"(improv|decreas|better).*(weather|storm)|weather.*(improv|decreas|better)", message.lower()) else 0.0
            )
            t_delta = 0.3 if re.search(r"(heavy|high|bad|wors|increas).*(traffic|congestion)|traffic.*(increas|wors|bad|high|heavy)", message.lower()) else 0.0
            p_delta = 0.3 if re.search(r"(port.*congestion|congested.*port|port.*delay|port.*increas)", message.lower()) else 0.0

            # Extract vehicle IDs to remove
            unavail = re.findall(r"V-\d{3}", message.upper())

            shipments = self._data.get_shipments().to_dict(orient="records")
            fleet = self._data.get_fleet().to_dict(orient="records")
            result = self._sim(
                shipments=shipments,
                fleet=fleet,
                ml_service=self._ml,
                risk_engine_fn=self._risk,
                weather_severity_delta=w_delta,
                traffic_level_delta=t_delta,
                port_congestion_delta=p_delta,
                vehicle_unavailable_ids=unavail,
            )
            delta = result.get("delta", {})
            return result, (
                f"Simulation: disruption probability "
                f"{delta.get('disruption_probability_avg', 0):+.1%}, "
                f"delay {delta.get('expected_delay_avg_hours', 0):+.1f}h"
            )

        elif tool_name == "get_policy":
            if self._retriever:
                docs = self._retriever.retrieve(message, top_k=2)
                return docs, f"Retrieved {len(docs)} policy document(s)"
            return [], "Policy documents unavailable"

        return {}, f"Unknown tool: {tool_name}"

    def _generate_answer(
        self,
        message: str,
        results: dict,
        rag_context: str,
        shipment_id: Optional[str],
    ) -> str:
        """Generate a structured natural-language response from tool results."""
        parts = []
        msg_lower = message.lower()

        # High-risk shipments response
        if "get_high_risk_shipments" in results:
            high_risk = results["get_high_risk_shipments"]
            if not high_risk:
                parts.append("No HIGH or CRITICAL risk shipments found in the current dataset.")
            else:
                parts.append(f"**{len(high_risk)} high/critical risk shipments identified:**\n")
                for s in high_risk[:5]:
                    prob = s.get("disruption_probability", 0)
                    delay = s.get("expected_delay_hours", 0)
                    sid = s.get("shipment_id", "?")
                    level = s.get("risk_level", "?")
                    priority = s.get("priority", "?")
                    parts.append(
                        f"• **{sid}** — {level} risk | {priority} priority | "
                        f"Disruption probability: {prob:.0%} | Expected delay: {delay:.1f}h"
                    )
                top = high_risk[0]
                parts.append(
                    f"\n**Recommended action:** {top.get('shipment_id')} requires immediate "
                    f"attention. Disruption probability is {top.get('disruption_probability', 0):.0%}."
                )

        # Root cause / analysis response
        if "analyze_root_cause" in results:
            analysis = results["analyze_root_cause"]
            if analysis.get("top_factors"):
                sid = analysis.get("shipment_id", shipment_id or "selected shipment")
                prob = analysis.get("disruption_probability", 0)
                delay = analysis.get("expected_delay_hours", 0)
                factors = analysis.get("top_factors", [])
                parts.append(
                    f"\n**Root cause analysis for {sid}:**\n"
                    f"Disruption probability: {prob:.0%} | Expected delay: {delay:.1f}h\n"
                    f"\nTop contributing factors to the model's prediction:"
                )
                for i, f in enumerate(factors[:5], 1):
                    parts.append(f"  {i}. {f['label']} (value: {f['value']:.3f}, contribution: {f['contribution']:+.4f})")

        # Shipment details response
        if "get_shipment_details" in results and isinstance(results["get_shipment_details"], dict):
            details = results["get_shipment_details"]
            if details.get("shipment_id"):
                parts.append(
                    f"\n**Shipment {details.get('shipment_id')}:** "
                    f"{details.get('origin')} → {details.get('destination')}, "
                    f"{details.get('distance_km', 0):.0f} km, "
                    f"cargo {details.get('cargo_weight_kg', 0):.0f} kg, "
                    f"priority: {details.get('priority')}, "
                    f"deadline: {details.get('delivery_deadline_hours')}h"
                )

        # Fleet status response
        if "get_fleet_status" in results:
            fleet_data = results["get_fleet_status"]
            total = fleet_data.get("total", 0)
            avail = fleet_data.get("available", 0)
            parts.append(
                f"\n**Fleet status:** {avail}/{total} vehicles available."
            )

        # Optimization response
        if "optimize_fleet" in results:
            opt = results["optimize_fleet"]
            assignments = opt.get("assignments", [])
            feasible = [a for a in assignments if a.get("feasible")]
            unassigned = opt.get("unassigned_shipments", [])
            cost = opt.get("total_estimated_cost", 0)
            util_before = opt.get("utilization_before", 0)
            util_after = opt.get("utilization_after", 0)
            parts.append(
                f"\n**Fleet optimization result ({opt.get('solver_status', '?')}):**\n"
                f"• {len(feasible)} assignments made | "
                f"{len(unassigned)} unassigned shipments\n"
                f"• Total estimated cost: ${cost:,.0f}\n"
                f"• Fleet utilization: {util_before:.0%} → {util_after:.0%}\n"
                f"• High/critical risk shipments assigned: {opt.get('high_risk_reduced', 0)}"
            )
            if unassigned:
                parts.append(f"• Unassigned (constraint violations): {', '.join(unassigned[:5])}")

        # Simulation response
        if "run_simulation" in results:
            sim = results["run_simulation"]
            label = sim.get("simulation_label", "Custom scenario")
            delta = sim.get("delta", {})
            current = sim.get("current", {})
            simulated = sim.get("simulated", {})
            prob_delta = delta.get("disruption_probability_avg", 0)
            delay_delta = delta.get("expected_delay_avg_hours", 0)
            risk_delta = delta.get("high_risk_count", 0)
            parts.append(
                f"\n**Simulation result — {label}:**\n"
                f"| Metric | Current | Simulated | Change |\n"
                f"|---|---|---|---|\n"
                f"| Avg disruption probability | {current.get('disruption_probability_avg', 0):.1%} | "
                f"{simulated.get('disruption_probability_avg', 0):.1%} | {prob_delta:+.1%} |\n"
                f"| Avg expected delay | {current.get('expected_delay_avg_hours', 0):.1f}h | "
                f"{simulated.get('expected_delay_avg_hours', 0):.1f}h | {delay_delta:+.1f}h |\n"
                f"| High-risk shipments | {current.get('high_risk_count', 0)} | "
                f"{simulated.get('high_risk_count', 0)} | {int(risk_delta):+d} |"
            )

        # Policy context from RAG
        if rag_context:
            parts.append(f"\n**Relevant policy:**{rag_context[:400]}")

        # All shipments fallback
        if not parts and "get_shipments" in results:
            shipments = results["get_shipments"]
            parts.append(f"Current operational data shows {len(shipments)} active shipments.")

        if not parts:
            parts.append(
                "I couldn't find specific data to answer that question. "
                "Try asking about a specific shipment ID, risk levels, fleet status, or optimization."
            )

        return "\n".join(parts).strip()
