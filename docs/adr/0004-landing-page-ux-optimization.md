# ADR 0004: Landing Page UX & Sorting Optimization

## Status
Accepted

## Context
Originally, the application followed a "Fixed Dashboard" pattern where the map and list occupied the full viewport immediately. While functional, this lacked "marketing" impact and clear value proposition for new users. Additionally, the default sorting was alphabetical, which required user interaction (clicking "Near Me") to access the most relevant physiological data.

## Decision
1. **Landing Page Transition**: Implement a hybrid "Scrolling Landing Page" model. A full-height (v1) then refined (v2) Hero section provides immediate context. Users can scroll down to reveal the interactive dashboard.
2. **Automatic Geolocation Default**: The application now defaults to distance-based sorting immediately upon location acquisition.
3. **Removal of Manual Sorting Override**: The alphabetical "Default" sort was deemed of low utility in an emergency context. We removed the UI toggle to reduce cognitive load and enforce the most relevant data presentation (proximity).
4. **Visual Depth**: Introduced subtle dot-grid textures and background gradients to the Hero section to improve modern aesthetics and reduce "flatness."

## Consequences
- **Pros**: 
  - Improved first-time user engagement via clearer value proposition in the Hero.
  - Reduced "Time to Insight" by automating the most logical sort order (Distance).
  - Cleaner interface via removal of redundant UI controls.
- **Cons**:
  - Users who specifically want an alphabetical list must now use the Search filter.
  - Slightly more complex scroll logic in `page.tsx` to handle the transition between "scrolling landing page" and "fixed app view."

## Alternatives Considered
- **Keep Fixed Layout**: Rejected as it felt "cold" and lacked narrative flow for a portfolio project.
- **Keep Sorting Toggle**: Rejected to align with the principle of "Opinionated UX" for emergency data.
