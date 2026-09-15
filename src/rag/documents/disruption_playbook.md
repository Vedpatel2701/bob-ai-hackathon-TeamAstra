# Disruption Response Playbook

## When a Critical Shipment Is Predicted to Be Delayed

**Immediate Actions (within 15 minutes of alert):**
1. Confirm the disruption prediction by checking current weather, traffic, and port status
2. Identify the primary risk factor driving the prediction (weather, congestion, warehouse, supplier)
3. Check vehicle availability for immediate reassignment
4. Notify the customer of potential delay and revised ETA

**Short-term Actions (within 1 hour):**
1. If weather-related: check alternative routing that avoids the affected corridor
2. If port congestion: contact port operations for estimated clearance time; consider holding at warehouse
3. If vehicle issue: run fleet optimizer to find next best available vehicle
4. If supplier delay: escalate to supplier account manager; consider partial shipment if feasible

**Documentation:**
- Log disruption event with timestamp, root cause, and actions taken
- Update shipment status to DELAYED or AT_RISK in the system
- Record actual vs. predicted delay for model feedback

## Severe Weather Response Protocol

**Weather Severity > 0.7:**
1. Halt dispatch of LOW and MEDIUM priority shipments in affected region
2. Re-route HIGH and CRITICAL shipments around weather zone if route alternatives exist
3. Check vehicle safety — dispatch trucks only if road conditions are safe
4. Notify customers of proactive delays (better to notify early than late)

**Weather Severity > 0.9 (Extreme):**
1. Suspend all non-CRITICAL dispatches in affected region
2. CRITICAL shipments: supervisor approval required before dispatch
3. Activate emergency partner carrier contacts
4. Issue customer communications with updated ETAs

## Port Congestion Response

**Port Congestion > 0.6:**
- Notify consignees of potential port clearance delays
- Consider rerouting to alternative entry port if cost differential < 15%
- Prioritize CRITICAL shipments for expedited port processing

**Port Congestion > 0.85:**
- Hold inbound shipments at origin warehouse until congestion clears
- Escalate to port liaison contact for clearance priority

## Multi-Factor Disruption

When 3 or more risk factors are simultaneously elevated:
- The combined risk score is often non-linear; trust the ML risk model
- Escalate immediately to operations manager
- Run what-if simulation to evaluate whether rerouting or holding is better
- Do not manually override model predictions without documented justification
