"""Agentic copilot API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from schemas.models import CopilotRequest, CopilotResponse, ToolCall
from services.data_service import DataService
from services.ml_service import MLService
from services.risk_engine import compute_risk_score
from services.simulation_service import run_simulation
from optimization.fleet_optimizer import optimize_fleet
from agents.copilot_agent import SupplyChainAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-initialised singleton agent
_agent: SupplyChainAgent | None = None


def _get_agent() -> SupplyChainAgent:
    global _agent
    if _agent is None:
        _agent = SupplyChainAgent(
            data_service=DataService,
            ml_service=MLService,
            risk_engine_fn=compute_risk_score,
            optimizer_fn=optimize_fleet,
            sim_fn=run_simulation,
        )
    return _agent


@router.post("/copilot", response_model=CopilotResponse)
async def copilot(request: CopilotRequest) -> CopilotResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        agent = _get_agent()
        result = agent.answer(request.message, context=request.context)
    except Exception as e:
        logger.error(f"Copilot error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Copilot error: {str(e)}")

    tools_used = [
        ToolCall(
            tool_name=t["tool_name"],
            arguments=t.get("arguments", {}),
            result_summary=t.get("result_summary", ""),
        )
        for t in result.get("tools_used", [])
    ]

    return CopilotResponse(
        answer=result["answer"],
        tools_used=tools_used,
        sources=result.get("sources", []),
        confidence=result.get("confidence", 0.8),
    )
