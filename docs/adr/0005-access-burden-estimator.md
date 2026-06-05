# ADR 0005: Access Burden Estimator Design

## Status
Accepted

## Date
February 4, 2026

## Context

Healthcare access involves more than just clinical wait times. Financial barriers—including transportation costs and parking fees—can significantly impact patients' ability to access emergency care, particularly for lower-income populations. However, these costs are typically invisible in wait time applications.

### Problem Statement

1. **Hidden Costs:** Patients comparing hospital options rarely consider the financial burden of accessing care
2. **Access Disparities:** Lower-income patients may face significant financial barriers that influence their healthcare decisions
3. **Policy Blindness:** Healthcare policymakers lack visible data on logistical access barriers
4. **Risk of Misuse:** Displaying costs could discourage patients from seeking necessary emergency care

### User Stories

- As a patient, I want to understand the financial burden of traveling to different hospitals so I can plan accordingly
- As a policymaker, I want to see logistical access costs made visible so I can address systemic barriers
- As a healthcare advocate, I want to highlight hidden financial barriers without discouraging emergency care

---

## Decision

We will implement an **Access Burden Estimator** component that:

### 1. Calculates Total Access Cost

**Formula:**
```
Total Access Burden = (Round Trip Distance × Fuel Consumption × Gas Price) + Parking Estimate
```

**Components:**
- **Distance:** Already calculated from user location to hospital (Haversine formula)
- **Fuel Cost:** Based on provincial gas prices and 10L/100km average consumption
- **Parking:** Estimated range by hospital type (urban/suburban/rural)

### 2. Displays Cost as a Range

Show `$min - $max` to acknowledge uncertainty in parking costs, not a false-precision single number.

### 3. Remains Collapsed by Default

The component starts collapsed to avoid overwhelming users or creating decision paralysis. Users must actively choose to view the estimate.

### 4. Includes Prominent Disclaimers

**Always-visible banner:**
> "Planning tool only. Never delay emergency care for cost. Call 911 for emergencies."

**Expanded view includes:**
- Methodology explanation (fuel consumption rate, gas price)
- Hospital type clarification (urban/suburban/rural)
- Rationale statement: "Why show this?"

---

## Implementation Details

### Provincial Gas Prices (CAD/L)

Based on Natural Resources Canada data (updated periodically):

| Province | Price/L | Notes |
|----------|---------|-------|
| ON | $1.55 | Default fallback |
| QC | $1.60 | |
| AB | $1.45 | Lowest (oil producing) |
| BC | $1.75 | Highest (carbon tax) |
| MB | $1.50 | |
| Other | See code | |

### Parking Estimates (CAD)

| Hospital Type | Min | Max | Rationale |
|---------------|-----|-----|-----------|
| Urban | $15 | $25 | Toronto, Montreal, Vancouver rates |
| Suburban | $10 | $15 | Medium-density areas |
| Rural | $0 | $5 | Often free or minimal |

### Fuel Consumption

- **Rate:** 10L/100km (industry standard for average passenger vehicle)
- **Sources:** Natural Resources Canada, Canadian Automobile Association

### Calculation Example

**Scenario:** 20km to urban hospital in Ontario
```
Round trip: 20km × 2 = 40km
Fuel: 40km × (10L/100km) × $1.55/L = $6.20
Parking: $15-$25
Total: $21-$31
```

---

## Consequences

### Positive

1. **Transparency:** Makes invisible financial barriers visible
2. **Access transparency:** Shows how logistical burdens can affect interpretation of public wait-time data
3. **Differentiation:** No other ER wait time app includes this feature
4. **Policy Impact:** Provides data for access barrier discussions
5. **Trust:** Shows awareness that healthcare access involves more than clinical factors

### Negative (Risks)

1. **Misuse:** Could discourage patients from seeking necessary care
2. **Oversimplification:** Doesn't account for public transit, insurance, lost wages
3. **Maintenance:** Gas prices need periodic updates
4. **Liability:** Could be seen as providing financial advice

### Mitigations

| Risk | Mitigation Strategy |
|------|---------------------|
| Delayed care | Prominent "Never delay care" disclaimer, always visible |
| Oversimplification | Methodology notes explain limitations clearly |
| Outdated data | Gas prices sourced from government data, update quarterly |
| Liability | Framed as "planning tool only," not decision-making tool |

---

## Alternatives Considered

### Alternative 1: Don't Show Costs At All

**Pros:**
- No risk of discouraging care
- Simpler implementation

**Cons:**
- Misses opportunity to highlight access barriers
- Misses an opportunity to surface access-barrier context
- Perpetuates invisibility of financial barriers

**Verdict:** Rejected. The educational and advocacy value outweighs the risks when properly disclaimed.

---

### Alternative 2: Include Lost Wages / Time Cost

**Calculation:**
```
Time Cost = (Travel Time + Wait Time) × Hourly Wage
```

**Pros:**
- More comprehensive cost estimate
- Highlights opportunity cost

**Cons:**
- **Highly sensitive:** Implies dollar value on time
- **Ethically problematic:** Could encourage "worth it" calculations for emergency care
- **Data limitations:** Don't have reliable wage data
- **Offensive framing:** Suggests emergencies should be financially justified

**Verdict:** Rejected. Too sensitive and ethically problematic. The component should highlight logistical barriers, not encourage cost-benefit analysis of emergency care.

---

### Alternative 3: Show Only Distance, Not Cost

**Pros:**
- No financial implications
- Still shows access burden

**Cons:**
- Misses the point: distance is already shown
- Fails to highlight financial barriers specifically

**Verdict:** Rejected. Distance alone doesn't capture the financial barrier aspect.

---

### Alternative 4: Show Transit Options

**Pros:**
- More equitable (benefits non-drivers)
- Lower cost alternative

**Cons:**
- API complexity (Google Transit API, etc.)
- Data availability varies by region
- Maintenance burden

**Verdict:** Deferred to future enhancement. Focus on driving cost first (majority use case), add transit later if demand exists.

---

## Design Principles Applied

### 1. Transparency Over Optimization

Show methodology clearly. Don't hide assumptions. This aligns with the project's core principle of "audit, don't aggregate."

### 2. Safety First

The disclaimer is **always visible**, not just in expanded state. Never encourage financial considerations to override medical judgment.

### 3. Range Over Precision

Use `$21-$31` not `$24.57`. Acknowledge uncertainty rather than creating false precision.

### 4. Collapsed by Default

Opt-in, not opt-out. Users must actively choose to see this information.

### 5. Educational, Not Prescriptive

The "Why show this?" section explains the feature's purpose: making barriers visible, not guiding decisions.

---

## Technical Implementation

### Component Structure

```tsx
<AccessBurdenEstimator
  distanceKm={20}        // From calculateDistance()
  province="ON"          // From hospital.province
  hospitalType="urban"   // Could be enhanced with DB field
/>
```

### Integration Points

1. **ExpandedCardDetails:** Shows when user has location and hospital card is expanded
2. **Map Popup:** (Future) Could show in hospital popup
3. **Comparison Modal:** (Future) Could compare access burden between hospitals

### Test Coverage

- 21 unit tests covering:
  - Collapsed/expanded states
  - Fuel cost calculation (multiple provinces)
  - Parking estimates (all hospital types)
  - Total cost ranges
  - Accessibility (ARIA attributes)
  - Edge cases (very short/long distances, unknown provinces)

---

## Success Metrics

### User Engagement

- Track expansion rate: X% of users expand the estimator
- Correlate with distance: Do users farther away expand more often?

### Advocacy Impact

- Include in public project documentation as an access-burden feature with clear safety caveats
- Use in discussions about healthcare access barriers
- Potential media coverage: "First ER app to highlight financial barriers"

### Stakeholder Feedback

- Interview question: "Is the Access Burden Estimator helpful or harmful?"
- Expected answer: Helpful for planning, if properly disclaimed

---

## Future Enhancements

### Phase 1 Enhancements (If Time Permits)

1. **Hospital-Specific Parking Data:** Replace estimates with actual parking rates
2. **Transit Options:** Add public transit cost/time comparison
3. **Comparison View:** Show access burden delta when comparing hospitals

### Phase 2 Enhancements (Post-Launch)

1. **API Integration:** Live gas prices from Natural Resources Canada
2. **Vehicle Type Selector:** Let users specify their fuel consumption rate
3. **Accessibility Mode:** Include wheelchair-accessible transit options

### Out of Scope (Intentionally Not Building)

1. **Time-value calculations:** Never include lost wages or time cost
2. **Insurance integration:** Don't factor in coverage
3. **Financial advice:** Don't suggest whether care is "worth it"

---

## Related ADRs

- [ADR 0002: Metric Ontology](./0002-metric-ontology.md) - Transparency philosophy
- [ADR 0004: Landing Page UX](./0004-landing-page-ux-optimization.md) - Collapsed-by-default pattern

---

## References

- **Gas Prices:** Natural Resources Canada Fuel Focus
- **Fuel Economy:** Natural Resources Canada Vehicle Fuel Consumption Guide
- **Parking Rates:** Informal survey of major Canadian hospitals
- **Public-interest framing:** Access-burden and health-system navigation context

---

## Approval

**Rationale:** The Access Burden Estimator demonstrates healthcare systems thinking while maintaining patient safety through prominent disclaimers. It differentiates the project from simple wait-time displays by showing non-clinical access burdens without recommending delayed care.

**Trade-offs Accepted:** We accept the maintenance burden of updating gas prices in exchange for making financial access barriers visible.

**Risk Mitigation:** The always-visible disclaimer and collapsed-by-default approach minimize the risk of discouraging necessary emergency care.

---

*Last Updated: February 4, 2026*
