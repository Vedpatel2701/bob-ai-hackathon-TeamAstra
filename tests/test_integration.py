"""Backend integration tests — verifies all endpoints with lifespan."""
import sys
import os
from pathlib import Path

# Ensure src/backend is on pythonpath
backend_path = Path(__file__).resolve().parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_path))
os.chdir(str(backend_path))

from main import app
from fastapi.testclient import TestClient


def test_backend_integration():
    """Test all backend endpoints end-to-end."""
    with TestClient(app) as client:
        # Health
        r = client.get('/api/health')
        assert r.status_code == 200 and r.json()['status'] == 'ok', f"health failed: {r.text}"

        # Fleet
        r = client.get('/api/fleet')
        assert r.status_code == 200
        fleet = r.json()
        assert fleet['total'] == 40

        # Shipments (cached)
        r = client.get('/api/shipments?limit=10')
        assert r.status_code == 200
        ships = r.json()
        assert ships['total'] == 300
        assert ships['shipments'][0]['risk_level'] is not None

        # High-risk (cached, must come before /{id} route)
        r = client.get('/api/shipments/high-risk')
        assert r.status_code == 200
        hr = r.json()
        assert hr['total'] > 0

        # Single shipment (not matching high-risk route)
        first_id = ships['shipments'][0]['shipment_id']
        r = client.get(f'/api/shipments/{first_id}')
        assert r.status_code == 200

        # Metrics (cached)
        r = client.get('/api/metrics')
        assert r.status_code == 200
        kpis = r.json()['kpis']
        assert kpis['high_risk_count'] > 0

        # Predict (SHAP enabled for single shipment)
        r = client.post('/api/predict', json={
            'weather_severity': 0.8, 'traffic_level': 0.7, 'port_congestion': 0.6,
            'warehouse_delay_hours': 4.0, 'supplier_risk': 0.5, 'vehicle_utilization': 0.8,
            'historical_delay_hours': 5.0, 'delivery_deadline_hours': 24.0,
            'distance_km': 800.0, 'cargo_weight_kg': 5000.0, 'priority': 'HIGH',
        })
        assert r.status_code == 200
        p = r.json()
        assert p['risk_level'] in ('HIGH', 'CRITICAL', 'MEDIUM', 'LOW')
        assert len(p['risk_factors']) > 0

        # Optimize (OR-Tools)
        r = client.post('/api/optimize', json={})
        assert r.status_code == 200
        opt = r.json()
        feasible = [a for a in opt['assignments'] if a['feasible']]
        assert len(feasible) > 0

        # Simulate (batch prediction)
        r = client.post('/api/simulate', json={
            'weather_severity_delta': 0.3, 'traffic_level_delta': 0.2,
            'port_congestion_delta': 0.0, 'vehicle_unavailable_ids': [],
        })
        assert r.status_code == 200
        sim = r.json()
        assert sim['delta']['disruption_probability_avg'] > 0

        # Copilot question-specific validations
        questions = [
            "Which shipments need immediate attention?",
            "Why is SH-1001 at risk?",
            "Optimize the fleet",
            "What if traffic increases?",
            "What is the fleet policy?",
            "Which region is most risky?",
        ]
        for q in questions:
            r = client.post('/api/copilot', json={'message': q})
            assert r.status_code == 200, f"Copilot failed for question: {q}"
            cop = r.json()
            assert len(cop['answer']) > 40
            assert 'Operational Recommendation:' in cop['answer']
            assert len(cop.get('tools_used', [])) > 0 or len(cop.get('sources', [])) > 0



if __name__ == '__main__':
    test_backend_integration()
    print("\nAll integration tests PASSED")

