# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.11+
- Node.js 18+
- npm 9+ or yarn
- Docker Desktop (optional, for containerised deployment)

## Repository Structure

```
src/
├── backend/          # FastAPI backend — Python
│   ├── api/          # Route handlers
│   ├── services/     # Business logic services
│   ├── agents/       # Agentic copilot
│   ├── optimization/ # OR-Tools fleet optimizer
│   └── main.py       # Application entry point
├── ml/               # Machine learning pipeline — Python
│   ├── data/         # Synthetic data generation
│   ├── training/     # Model training scripts
│   ├── inference/    # Inference service
│   └── explainability/ # SHAP explainability
├── rag/              # RAG knowledge retrieval — Python
│   ├── documents/    # Operational policy documents
│   └── retrieval/    # TF-IDF retrieval engine
└── frontend/         # Next.js frontend — TypeScript
    ├── app/          # Next.js App Router pages
    ├── components/   # Reusable React components
    ├── lib/          # API client and utilities
    └── types/        # TypeScript type definitions
```

## Environment Variables

Copy `.env.example` to `.env` inside `src/backend/` and fill in your values:

```bash
cd src/backend
cp .env.example .env
```

| Variable | Description | Required |
|---|---|---|
| `APP_PORT` | Backend server port (default: 8000) | No |
| `APP_ENV` | Environment: development / production | No |
| `MODEL_PATH` | Path to trained model file (default: auto) | No |
| `DATA_PATH` | Path to dataset directory (default: auto) | No |
| `WATSONX_API_KEY` | IBM watsonx.ai API key (optional for MVP) | No |
| `WATSONX_PROJECT_ID` | IBM watsonx.ai project ID (optional for MVP) | No |
| `WATSONX_URL` | IBM watsonx.ai endpoint URL | No |

The MVP runs fully without external API keys. The watsonx.ai variables are optional and only used if IBM model integration is enabled.

## Installation

### Option A: Manual Setup (Recommended for Development)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bob-ai-hackathon-TeamAstra.git
cd bob-ai-hackathon-TeamAstra

# 2. Set up Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install backend and ML dependencies
pip install -r src/backend/requirements.txt

# 4. Generate synthetic dataset and train the ML model
python src/ml/data/generate_dataset.py
python src/ml/training/train_model.py

# 5. Install frontend dependencies
cd src/frontend
npm install
cd ../..
```

### Option B: Docker Compose

```bash
# Build and start all services
docker compose -f src/docker-compose.yml up --build

# The backend will be available at http://localhost:8000
# The frontend will be available at http://localhost:3000
```

## Running the Application

### Backend

```bash
# Activate virtual environment first
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Start the FastAPI backend
cd src/backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

### Frontend

```bash
# In a separate terminal
cd src/frontend
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Running Tests

```bash
# Backend tests
source .venv/bin/activate
cd src/backend
pytest tests/ -v

# ML pipeline tests
cd src/ml
pytest tests/ -v
```

## Quick Demo

```bash
# 1. Generate data and train model (one-time setup)
python src/ml/data/generate_dataset.py
python src/ml/training/train_model.py

# 2. Start backend
cd src/backend && uvicorn main:app --port 8000 &

# 3. Start frontend
cd src/frontend && npm run dev &

# 4. Open http://localhost:3000 in your browser
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r src/backend/requirements.txt` with the venv activated |
| `Model file not found` | Run `python src/ml/training/train_model.py` to train and save the model |
| `Dataset not found` | Run `python src/ml/data/generate_dataset.py` to generate the synthetic dataset |
| Port 8000 already in use | Set `APP_PORT=8001` in `.env` and start with `uvicorn main:app --port 8001` |
| Port 3000 already in use | Set `PORT=3001` in the frontend `.env.local` and run `npm run dev` |
| OR-Tools import error | Run `pip install ortools` — ensure the venv is active |
| SHAP import error | Run `pip install shap` — ensure the venv is active |
| Next.js build error | Run `npm install` inside `src/frontend/` then retry |
