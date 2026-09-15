#!/usr/bin/env bash
# SupplyChainAI — Quick start script
# Usage: bash start.sh

set -e

echo "=== SupplyChainAI Quick Start ==="

# Generate data if not present
if [ ! -f src/ml/data/shipments.csv ]; then
  echo "Generating synthetic dataset..."
  python src/ml/data/generate_dataset.py
fi

# Train model if not present
if [ ! -f src/ml/models/classifier.pkl ]; then
  echo "Training ML model..."
  python src/ml/training/train_model.py
fi

# Start backend in background
echo "Starting backend on http://localhost:8000 ..."
cd src/backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# Wait for backend to be ready
echo "Waiting for backend..."
for i in {1..10}; do
  if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  sleep 1
done

# Start frontend
echo "Starting frontend on http://localhost:3000 ..."
cd src/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

echo ""
echo "=== SupplyChainAI is running ==="
echo "  Dashboard:  http://localhost:3000"
echo "  API docs:   http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

wait $FRONTEND_PID
kill $BACKEND_PID 2>/dev/null || true
