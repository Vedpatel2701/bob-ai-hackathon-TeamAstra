# Shipment Priority Rules

## Priority Levels

### CRITICAL Priority
- Definition: Shipments whose delay causes immediate financial loss, production stoppage, or contractual penalty
- SLA: Deliver within contracted deadline with zero tolerance for delay
- Escalation: Automatic escalation to operations supervisor if disruption probability > 60%
- Action: Immediate vehicle reassignment if current assignment is at risk
- Customer notification: Required within 1 hour of identified risk

### HIGH Priority
- Definition: Time-sensitive shipments with defined delivery windows
- SLA: Deliver within 2 hours of contracted deadline
- Escalation: Notify team lead if disruption probability > 70%
- Action: Evaluate alternative routing if expected delay > 3 hours
- Customer notification: Required if delay expected to exceed 4 hours

### MEDIUM Priority
- Definition: Standard commercial shipments with standard delivery expectations
- SLA: Deliver within contracted window ± 4 hours
- Escalation: Flag in daily operations review if delay > 6 hours
- Action: Standard monitoring; reroute only if cost-effective
- Customer notification: Proactive notification if delay expected > 8 hours

### LOW Priority
- Definition: Non-urgent shipments with flexible delivery windows
- SLA: Deliver within contracted window ± 24 hours
- Escalation: Weekly review of recurring delays
- Action: No emergency action; optimize for cost efficiency
- Customer notification: Standard tracking updates

## Priority Escalation Triggers

A shipment should be escalated to the next priority level when:
1. Weather severity increases to > 0.7 after dispatch
2. Port congestion causes expected delay > 50% of remaining deadline time
3. Assigned vehicle becomes unavailable mid-route
4. Disruption probability exceeds 80% for any reason

## Priority Downgrade

Shipments may be downgraded only with explicit customer or supervisor approval.
