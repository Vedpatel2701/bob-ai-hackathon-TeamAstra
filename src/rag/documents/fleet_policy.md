# Fleet Operations Policy

## Vehicle Assignment Policy

### Standard Assignment Rules

1. **Priority-first assignment:** CRITICAL shipments are assigned first, followed by HIGH, MEDIUM, then LOW priority.
2. **Capacity matching:** A vehicle must have capacity >= cargo weight. Overloading is prohibited.
3. **Availability requirement:** Only vehicles with `availability = true` may be assigned to new shipments.
4. **Reliability threshold:** Vehicles with reliability_score < 0.70 should not be assigned to CRITICAL or HIGH priority shipments.
5. **Utilization ceiling:** Vehicles currently at >= 90% utilization should not be assigned additional shipments unless no alternative exists.

### Vehicle Type Guidelines

- **SEMI trucks:** Best for cargo > 10,000 kg and distances > 500 km
- **Standard TRUCK:** General purpose for cargo 3,000–15,000 kg
- **VAN:** Light cargo < 3,000 kg, urban routes, short distances
- **REFRIGERATED:** Required for temperature-sensitive cargo

### Cost Optimization

The fleet optimizer minimizes total operating cost (operating_cost_per_km × distance_km) subject to the above constraints. Cost optimization is secondary to priority fulfillment.

## Vehicle Maintenance Policy

- Vehicles with reliability_score < 0.75 must be scheduled for maintenance within 72 hours
- Vehicles that have completed > 5 consecutive assignments should be rested
- Vehicle utilization > 95% triggers mandatory maintenance review

## Emergency Vehicle Deployment

When fewer than 3 vehicles are available and CRITICAL shipments are unassigned:
1. Immediately notify fleet supervisor
2. Check vehicle utilization — consider reassigning from LOW priority shipments
3. Contact partner carriers for emergency capacity
4. Activate mutual-aid agreement with nearest depot
