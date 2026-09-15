# Solution Overview

## What We Built

SupplyChainAI is an agentic AI decision-support platform for logistics operations teams. It predicts shipment disruption risk, explains the operational factors driving that risk, optimizes vehicle-to-shipment assignments using mathematical programming, simulates what-if scenarios, and provides an AI copilot that orchestrates all of these capabilities in response to natural-language questions.

The core insight is: **ML prediction + explainability + optimization + AI agent = actionable recommendations** — rather than isolated analytics tools that operators must mentally integrate themselves.

## How It Works

1. **Data Layer:** A realistic synthetic dataset of shipments and fleet vehicles is generated deterministically. Each shipment record includes origin, destination, cargo weight, priority, weather severity, traffic level, port congestion, warehouse delay, supplier risk, vehicle utilization, and delivery deadline. These correlate realistically — severe weather, high congestion, and warehouse delays increase disruption probability.

2. **ML Prediction:** A trained Random Forest / XGBoost classifier ingests shipment feature vectors and outputs disruption probability and expected delay. The model is trained on the synthetic dataset with genuine train/test evaluation (accuracy, precision, recall, F1, ROC-AUC).

3. **Explainability:** SHAP (SHapley Additive exPlanations) values are computed for each individual prediction, identifying which operational factors contributed most to the model's risk assessment. Results are rendered as ranked factor lists in the UI.

4. **Risk Scoring:** A transparent risk engine combines ML disruption probability, operational conditions, shipment priority, and deadline pressure into a composite risk score with levels: LOW / MEDIUM / HIGH / CRITICAL.

5. **Fleet Optimization:** Google OR-Tools solves a vehicle-to-shipment assignment problem subject to capacity, availability, priority, deadline, and cost constraints. The optimizer returns deterministic assignments, total estimated cost, and utilization improvements.

6. **What-If Simulation:** The simulation engine modifies specified operational parameters (weather, traffic, congestion, vehicle availability) and recalculates risk predictions and fleet metrics without affecting persistent state. Operators see current vs. simulated outcomes side-by-side.

7. **Agentic Copilot:** An AI copilot receives natural-language questions and decides which backend tools to invoke — shipment lookup, risk calculation, root-cause analysis, fleet optimization, simulation. It returns structured explanations combining tool results with operational context from the knowledge base.

8. **RAG Knowledge Base:** A lightweight retrieval system provides the copilot with access to operational policy documents (fleet policy, priority rules, disruption playbook, warehouse operations) to answer policy questions accurately.

## Architecture Diagram

See [`architecture.md`](architecture.md) for the full system diagram.

```
[Browser]
    │
    ▼
[Next.js Frontend — TypeScript, Tailwind, Recharts]
    │  REST / JSON
    ▼
[FastAPI Backend]
    ├── /api/shipments      → Data service
    ├── /api/predict        → ML inference service
    ├── /api/fleet          → Fleet data service
    ├── /api/optimize       → OR-Tools optimization service
    ├── /api/simulate       → Simulation engine
    ├── /api/copilot        → Agent + tool orchestration
    └── /api/metrics        → KPI aggregation
         │
         ├── [ML Pipeline: scikit-learn / XGBoost + SHAP]
         ├── [Optimization: Google OR-Tools]
         ├── [Risk Engine: deterministic scoring]
         └── [RAG: document retrieval + policy lookup]
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Synthetic deterministic dataset | Avoids dependency on unavailable proprietary logistics data while ensuring reproducible, realistic training data |
| Random Forest / XGBoost for prediction | Robust baseline classifier with reliable feature importance; well-supported by SHAP |
| OR-Tools for fleet optimization | Deterministic, constraint-aware solver — the LLM never invents vehicle assignments |
| SHAP for explainability | Provides per-instance factor attribution rather than global feature importance, matching the "why is this shipment at risk" use case |
| FastAPI + Pydantic | Type-safe API with automatic validation and documentation |
| Agent tool orchestration | Keeps LLM responsible for language and reasoning, specialized tools responsible for all numerical computations |
| Lightweight RAG without vector database | Simple TF-IDF retrieval over a small policy document corpus is sufficient for the MVP and avoids infrastructure overhead |

## IBM Technologies Used

- **IBM Bob:** Used throughout development as the AI coding assistant for architecture design, code generation, debugging, and iterative refinement of the ML pipeline, optimization engine, and agentic copilot. IBM Bob's tool orchestration capabilities directly inspired the agent design pattern used in the copilot implementation.
