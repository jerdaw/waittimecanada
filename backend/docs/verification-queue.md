# Hospital Verification Queue

## Overview

The Verification Queue UI allows administrators to review and approve hospitals discovered by scrapers before they appear on the public-facing site. This implements the critical requirement that **NEVER auto-publishes new hospitals**.

## Why This Matters

From AGENTS.md:
> "**NEVER auto-publish new hospitals.** All discovered facilities must go through verification"

This verification gate prevents:
- Incorrect hospital data from appearing on the site
- Duplicate entries with different IDs
- Test data or scraper artifacts from reaching production
- Unverified geographic coordinates from being displayed

## Architecture

### Backend Verification Method

The backend already has verification logic in `DatabaseService.verify_hospital()`:

```python
def verify_hospital(self, hospital_id: str, make_visible: bool = True) -> Hospital:
    """Mark a hospital as verified (admin action)."""
    # Updates is_verified=true and optionally is_visible=true
```

Located at: `/home/jer/localsync/waittimecanada/backend/src/waittime/services/database.py:155`

### Frontend API Endpoints

#### 1. GET `/api/admin/hospitals/unverified`

Lists all hospitals with `is_verified=false`.

**Response:**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "id": "ca-qc-montreal-chum",
      "name": "CHUM",
      "province": "QC",
      "city": "Montreal",
      "latitude": 45.5017,
      "longitude": -73.5673,
      "source_id": "qc-index-sante",
      "created_at": "2026-02-01T12:00:00Z",
      "is_visible": false,
      "is_verified": false
    }
  ]
}
```

#### 2. POST `/api/admin/hospitals/[id]/verify`

Approves a hospital and optionally makes it visible.

**Body:**
```json
{
  "makeVisible": true  // default: true
}
```

**Use Cases:**
- `makeVisible: true` - Approve and immediately publish
- `makeVisible: false` - Approve but keep hidden (useful for testing)

#### 3. DELETE `/api/admin/hospitals/[id]/verify`

Rejects and permanently deletes a hospital from the database.

**When to use:** Hospital is incorrect, duplicate, or should not exist in the system.

### Admin UI

**Location:** `/admin/verify`

**Features:**
- Displays all unverified hospitals with key metadata
- Three action buttons per hospital:
  - ✓ Approve & Publish (verify + make visible)
  - ✓ Approve (Keep Hidden) (verify but don't show publicly)
  - ✗ Reject & Delete (remove from database)
- Confirmation dialog before deletion
- Optimistic UI updates (removes from list after action)
- Error handling with user-friendly messages

**Empty State:**
When no hospitals need verification:
```
✓
All Caught Up!
No hospitals pending verification at this time.
```

## Workflow

### 1. Scraper Discovers New Hospital

When a scraper finds a new facility:

```python
hospital = Hospital(
    id="ca-on-ottawa-civic",
    name="Ottawa Civic Hospital",
    is_verified=False,  # ← Not verified yet
    is_visible=False,   # ← Not visible to public
    # ... other fields
)
db.insert_hospital(hospital)
```

### 2. Admin Reviews in Verification Queue

Admin visits `/admin/verify` and sees:

```
Ottawa Civic Hospital
Location: Ottawa, ON
Coordinates: 45.3968, -75.7124
Source: on-erwatch
Discovered: 2026-02-01

[✓ Approve & Publish] [✓ Approve (Keep Hidden)] [✗ Reject & Delete]
```

### 3. Admin Takes Action

**If hospital looks correct:**
- Click "Approve & Publish"
- Hospital becomes `is_verified=true, is_visible=true`
- Appears on public map immediately

**If hospital needs manual review first:**
- Click "Approve (Keep Hidden)"
- Hospital becomes `is_verified=true, is_visible=false`
- Can be made visible later via separate admin action

**If hospital is incorrect:**
- Click "Reject & Delete"
- Confirms deletion
- Hospital is permanently removed from database

## Database Behavior

### Public Queries

All public-facing hospital queries filter to:

```sql
WHERE is_visible = true AND is_verified = true
```

This means unverified or hidden hospitals never appear on:
- `/api/hospitals` (map markers)
- Hospital detail pages
- Comparison tools

### Admin Queries

Admin endpoints query:

```sql
WHERE is_verified = false
```

To show only hospitals awaiting verification.

## Testing

### Frontend Tests (18 tests)

**API Tests:** `/home/jer/localsync/waittimecanada/frontend/tests/api/admin/`
- `unverified.test.ts` - Tests fetching unverified hospitals
- `verify.test.ts` - Tests POST (approve) and DELETE (reject) operations

**UI Tests:** `/home/jer/localsync/waittimecanada/frontend/tests/pages/admin/verify.test.tsx`
- Loading states
- Empty states
- Hospital listing
- Approval actions
- Rejection with confirmation
- Error handling

All tests use mocked postgres with `vi.hoisted()` to handle the tagged template literal syntax.

### Backend Tests

The existing `DatabaseService` tests already cover:
- `verify_hospital()` functionality
- Hospital queries with `is_verified` filtering

## Security Considerations

### Access Control

**⚠️ IMPORTANT:** The `/admin/verify` page currently has NO authentication.

Before production deployment, implement:
1. Authentication middleware (e.g., Auth0, Clerk, or custom JWT)
2. Role-based access control (only admins can verify)
3. Audit logging (track who approved/rejected what and when)

### Example Authentication

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/admin')) {
    const session = await getSession(request);
    if (!session || !session.isAdmin) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
}
```

## Operational Checklist

When deploying verification queue:

- [ ] Set up admin authentication
- [ ] Create initial admin user accounts
- [ ] Configure audit logging
- [ ] Set up Slack/email notifications for new hospitals
- [ ] Document verification criteria (what makes a hospital "correct"?)
- [ ] Train admin staff on verification workflow
- [ ] Schedule regular checks (daily? weekly?) for pending hospitals

## Future Enhancements

Potential v2 improvements:

- **Batch operations:** Select multiple hospitals and approve/reject all at once
- **Verification criteria checklist:** Admin must check off validation items
- **Preview mode:** View how hospital will appear on map before publishing
- **Revision history:** Track all verification actions with timestamps
- **Automatic validation:** Flag suspicious entries (duplicate names, wrong coordinates)
- **Notification system:** Email admin when new hospitals need review
- **Search/filter:** Find specific hospitals in long verification queue

## Related Documentation

- **Main project requirements:** `/home/jer/localsync/waittimecanada/AGENTS.md`
- **Database schema:** `/home/jer/localsync/waittimecanada/backend/docs/data-retention.md`
- **Ontario methodology:** `/home/jer/localsync/waittimecanada/backend/docs/methodologies/ontario-methodology.md`

---

*Last Updated: February 1, 2026*
*Implemented in: Task #3 - Verification Queue UI*
