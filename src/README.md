# SupplyChainAI — Source Code

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Generate data and train the ML model

```bash
python ml/data/generate_dataset.py
python ml/training/train_model.py
```

### 2. Start the backend (from this directory)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

### 3. Start the frontend (new terminal)

```bash
cd frontend
npm install   # first time only
npm run dev
```

Dashboard: http://localhost:3000

## Structure

| Directory | Contents |
|---|---|
| `backend/` | FastAPI application, services, agents, optimization |
| `ml/` | Synthetic data generation, model training, inference, SHAP |
| `rag/` | Operational policy documents, TF-IDF retrieval |
| `frontend/` | Next.js dashboard, all UI pages |

## Key APIs

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/shipments` | GET | All shipments with ML risk scores |
| `/api/shipments/high-risk` | GET | High/critical risk shipments |
| `/api/fleet` | GET | Fleet vehicles with availability |
| `/api/predict` | POST | ML disruption prediction + SHAP factors |
| `/api/optimize` | POST | OR-Tools fleet optimization |
| `/api/simulate` | POST | What-if scenario recalculation |
| `/api/copilot` | POST | Agentic AI tool orchestration |
| `/api/metrics` | GET | Executive KPIs and charts data |
