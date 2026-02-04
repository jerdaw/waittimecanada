# Planning Documentation

This directory contains project planning documents following best practices for software project management.

## Document Structure

### Strategic Planning
- **[strategic-plan.md](strategic-plan.md)** - Original comprehensive project specification
- **[expansion-roadmap.md](expansion-roadmap.md)** - Provincial expansion strategy (one province at a time)

### Tactical Planning
- **[roadmap.md](../../ROADMAP.md)** - Master project roadmap (located in repo root)
  - 5 milestones with clear success criteria
  - Task-level breakdown
  - Current: Milestone 2 (Ontario End-to-End)

### Implementation Planning
- **[implementation-plan-m2-ontario.md](archive/implementation-plan-m2-ontario.md)** - [COMPLETE] Milestone 2 implementation plan
- **[Archive](archive/)** - Historical planning summaries and completed milestones

## Document Hierarchy

```
Strategic (Long-term)
└─ expansion-roadmap.md - Which provinces, in what order?

Tactical (Medium-term)
└─ ROADMAP.md - What milestones, what order?

Implementation (Short-term)
└─ [New Milestone Plan] - How do we build the next milestone?

Archive (Historical)
├─ implementation-plan-m2-ontario.md
├─ IMPLEMENTATION_PLAN_SUMMARY.md
└─ REPO_MODERNIZATION_SUMMARY.md
```

## How to Use These Documents

### For Planning
1. **Start with strategic-plan.md** - Understand the "why"
2. **Review expansion-roadmap.md** - Understand provincial strategy
3. **Check ROADMAP.md** - See where we are in the project
4. **Read implementation plan** - Understand how to build the current milestone

### For Implementation
1. **Open current implementation plan** (currently: m2-ontario)
2. **Follow phases sequentially** (Phase 0 → 1 → 2 → 3 → 4 → 5)
3. **Check off tasks** as completed
4. **Update status** when phase complete
5. **Create new implementation plan** when starting next milestone

## Implementation Plan Versioning

Implementation plans follow semantic versioning:

- **Major version** (X.0.0) - New implementation plan for new milestone
- **Minor version** (1.X.0) - Significant scope changes within milestone
- **Patch version** (1.0.X) - Clarifications, minor updates

Example:
- v1.0.0 - Initial M2 Ontario plan
- v1.0.1 - Fixed typo in Phase 3
- v1.1.0 - Added Phase 2.6 for integration tests
- v2.0.0 - New plan for Milestone 3

## Document Lifecycle

### Draft
- Status: "Draft - Awaiting Approval"
- Purpose: Review and feedback
- Action: Review plan, approve or request changes

### Approved
- Status: "Approved - Ready for Implementation"
- Purpose: Active implementation guide
- Action: Follow phases, check off tasks

### In Progress
- Status: "In Progress - Phase X"
- Purpose: Track current work
- Action: Update as tasks complete

### Complete
- Status: "Complete - Milestone Delivered"
- Purpose: Historical record
- Action: Archive, create lessons learned document

## Best Practices

1. **Read before coding** - Understand the full plan before implementing
2. **Follow sequentially** - Don't skip phases
3. **Update as you go** - Check off tasks, note deviations
4. **Document learnings** - Add quirks, gotchas to appendices
5. **Revise if needed** - If plan doesn't match reality, update it (increment version)

**Active Plan:** [None - Milestone 2 Complete]

**Next Steps:**
1. Define scope for Milestone 3 (Production Deployment)
2. Create new implementation plan for M3
3. Begin Phase 0 (Production Infrastructure Research)

---

Last Updated: 2026-01-30
