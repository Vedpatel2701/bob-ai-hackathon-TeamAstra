# 🚀 SupplyChainAI — Agentic Supply Chain Risk & Fleet Optimization Platform

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | TeamAstra |
| **Track** | AI |
| **Team Lead** | Ved Patel — 24cs081@charusat.edu.in |
| **Members** | Deep Patel, Vishvesh Joshi, Dhyey Ghoniya |

---

## 🎯 Problem Statement

Supply chain operators often lack a unified system for identifying shipment disruption risks, understanding their root causes, and making fast fleet allocation decisions. Delays caused by traffic, weather, congestion, warehouse issues, supplier risk, and limited vehicle availability can increase operational costs and reduce delivery reliability.

---

## 💡 Solution

SupplyChainAI is an agentic AI decision-support platform that predicts shipment disruption and delay risk, explains the factors contributing to that risk, optimizes fleet allocation, and provides actionable recommendations through an AI copilot. Machine learning performs prediction, explainability identifies influential factors, optimization algorithms generate fleet assignments, and the AI agent orchestrates these capabilities into an operational decision workflow.

---

## ✨ Key Features

- **Shipment Disruption Prediction:** Machine-learning models estimate the probability and expected severity of shipment delays.

- **Explainable Risk Analysis:** Identifies the operational factors contributing most to a shipment's predicted risk.

- **Fleet Optimization:** Uses constraint-based optimization to recommend suitable vehicle-to-shipment assignments while considering capacity, availability, utilization, cost, and delivery requirements.

- **Agentic AI Copilot:** Allows operators to investigate shipments and ask natural-language questions while the AI agent orchestrates specialized prediction, analysis, and optimization tools.

- **What-If Simulation:** Enables operators to evaluate alternative fleet allocations and disruption scenarios before taking action.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, TypeScript, SQL |
| **Frameworks** | FastAPI, Next.js, React, Tailwind CSS, scikit-learn |
| **IBM Technologies** | IBM Bob |
| **Databases** | PostgreSQL |
| **Other** | Pandas, NumPy, XGBoost, SHAP, Google OR-Tools, Docker, GitHub Actions |

---

## 📁 Repository Structure

```text
├── src/                         # Application source code
│   ├── frontend/                # Next.js frontend
│   ├── backend/                 # FastAPI backend and services
│   ├── ml/                      # Machine-learning pipeline
│   └── rag/                     # Knowledge retrieval components
│
├── docs/                        # Project documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
│
├── demo/                        # Demo artifacts
│   ├── screenshots/
│   ├── demo-video-link.txt
│   └── live-demo-url.txt
│
├── presentation/                # Presentation materials
│
├── submission.yaml              # Hackathon submission metadata
│
└── README.md                    # Project overview