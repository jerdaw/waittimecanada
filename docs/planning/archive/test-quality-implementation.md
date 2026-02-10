# Test Quality Implementation (P2)

**Completed:** 2026-02-09
**Roadmap Item:** P2 / Test quality

## Summary

Eliminated all 21 React `act(...)` warnings in frontend unit tests by properly handling async state updates in test assertions. Tests now correctly wait for component state changes before making assertions.

## Changes Made

### Problem

React Testing Library was warning about component state updates that occurred outside of `act(...)` blocks. This happens when tests don't wait for async operations (like useEffect hooks with fetch calls) to complete before the test ends.

### Solution Pattern

For each component with act warnings:
1. Import `waitFor` from `@testing-library/react`
2. Make test functions `async`
3. Wrap assertions in `waitFor()` to wait for state updates
4. Mock async operations (like fetch) in `beforeEach`

### Files Modified

**1. AccessInsightsSummary.test.tsx (16 warnings → 0)**
- Added fetch mocking in beforeEach to prevent real API calls
- Made all 8 tests async
- Wrapped all assertions in waitFor():
```typescript
beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({
      success: true,
      data: { /* equity layer placeholder */ }
    }),
  });
});

it("renders location prompt when userLocation is null", async () => {
  render(<AccessInsightsSummary ... />);
  await waitFor(() => {
    expect(screen.getByText(/enable location access/i)).toBeInTheDocument();
  });
});
```

**2. ComparisonModal.test.tsx (2 warnings → 0)**
- Fixed "renders loading state initially" test (line 74-84)
- Made test async and added waitFor for data loading:
```typescript
it("renders loading state initially", async () => {
  render(<ComparisonModal ... />);
  expect(screen.getByText("Loading comparison...")).toBeInTheDocument();

  // Wait for data to load to ensure async operation completes
  await waitFor(() => {
    expect(screen.getByText("Ottawa Civic Hospital")).toBeInTheDocument();
  });
});
```

**3. InstallPrompt.test.tsx (2 warnings → 0)**
- Added `waitFor` import
- Made "renders when beforeinstallprompt event fires" test async with waitFor
- Fixed "calls prompt() when install button clicked" to wait for button appearance:
```typescript
it("calls prompt() when install button clicked", async () => {
  render(<InstallPrompt />);
  // Fire event
  fireEvent(window, event);

  // Wait for button to appear after state update
  await waitFor(() => {
    expect(screen.getByText("Install")).toBeInTheDocument();
  });

  fireEvent.click(screen.getByText("Install"));

  await waitFor(() => {
    expect(promptSpy).toHaveBeenCalled();
  });
});
```

**4. DataExport.test.tsx (1 warning → 0)**
- Added `act` import from `@testing-library/react`
- Fixed "shows loading state during download" test with fake timers
- Wrapped timer advancement in `act()`:
```typescript
it("shows loading state during download", () => {
  vi.useFakeTimers();
  render(<DataExport />);

  fireEvent.click(downloadButton);
  expect(screen.getByRole("button", { name: /Preparing/i })).toBeInTheDocument();

  // Advance timers in act() to properly handle state update
  act(() => {
    vi.runAllTimers();
  });

  expect(screen.getByRole("button", { name: /Download Data/i })).toBeInTheDocument();
  vi.useRealTimers();
});
```

## Testing

**Before:** 21 React act(...) warnings across 4 component test files
**After:** 0 act warnings in entire test suite

Final test results:
- ✅ Test Files: 44 passed, 1 failed (45 total)
- ✅ Tests: 269 passed, 2 failed (271 total)
- ✅ Act warnings: 0

The 2 failing tests are pre-existing equity-layer tests (not related to act warnings).

## Key Patterns

1. **Async operations in useEffect**: Always mock fetch calls and wait for them to complete
2. **Event-triggered state updates**: Use waitFor() after firing events to wait for state changes
3. **Fake timers**: Wrap timer advancement (`vi.runAllTimers()`) in `act()` when using fake timers
4. **Loading states**: Even if checking loading state, wait for loading to complete so test doesn't end with pending state updates

## Impact

- All frontend unit tests now properly handle async state updates
- No more spurious act warnings cluttering test output
- Tests are more reliable and accurately reflect user behavior
- Follows React Testing Library best practices

## Next Steps

P2 / Test quality is now complete. Other P2 items remain:
- [ ] P2 / Docs integrity: Add roadmap consistency checks
- [ ] P2 / Portfolio launch completion: Stakeholder interview and launch communications
