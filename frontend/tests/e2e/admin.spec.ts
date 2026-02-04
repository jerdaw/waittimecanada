import { test, expect } from '@playwright/test';

test.describe('Admin Verification Queue', () => {
  test('should show empty state when no hospitals pending', async ({ page }) => {
    await page.route('**/api/admin/hospitals/unverified', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: [] })
      });
    });

    await page.goto('/admin/verify');
    await expect(page.getByText('All Caught Up!')).toBeVisible();
    await expect(page.getByText('No hospitals pending verification at this time.')).toBeVisible();
  });

  test('should show unverified hospitals in the queue', async ({ page }) => {
    const mockHospitals = [
      {
        id: 'new-hospital-1',
        name: 'New Toronto Hospital',
        province: 'ON',
        city: 'Toronto',
        latitude: 43.6532,
        longitude: -79.3832,
        source_id: 'ontario-health',
        created_at: new Date().toISOString(),
        is_visible: false,
        is_verified: false
      }
    ];

    await page.route('**/api/admin/hospitals/unverified', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, count: 1, data: mockHospitals })
      });
    });

    await page.goto('/admin/verify');
    await expect(page.getByText('New Toronto Hospital')).toBeVisible();
    await expect(page.getByText('pending verification')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Approve & Publish' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Approve (Keep Hidden)' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reject & Delete' })).toBeVisible();
  });

  test('should handle approval action', async ({ page }) => {
    const mockHospitals = [{ id: 'h1', name: 'Hosp 1', province: 'ON', city: 'T', latitude: 0, longitude: 0, source_id: 's', created_at: new Date().toISOString(), is_visible: false, is_verified: false }];

    await page.route('**/api/admin/hospitals/unverified', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, data: mockHospitals }) });
    });

    await page.route('**/api/admin/hospitals/h1/verify', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
      }
    });

    await page.goto('/admin/verify');
    await page.getByRole('button', { name: 'Approve & Publish' }).click();
    
    // Should remove from list and show empty state
    await expect(page.getByText('All Caught Up!')).toBeVisible();
  });

  test('should handle reject & delete action', async ({ page }) => {
    const mockHospitals = [{ id: 'h2', name: 'Reject Me Hosp', province: 'ON', city: 'T', latitude: 0, longitude: 0, source_id: 's', created_at: new Date().toISOString(), is_visible: false, is_verified: false }];

    await page.route('**/api/admin/hospitals/unverified', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, data: mockHospitals }) });
    });

    await page.route('**/api/admin/hospitals/h2/verify', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
      }
    });

    await page.goto('/admin/verify');
    
    // Setup dialog handler for confirmation
    page.on('dialog', dialog => dialog.accept());
    
    await page.getByRole('button', { name: 'Reject & Delete' }).click();
    
    // Should remove from list and show empty state
    await expect(page.getByText('All Caught Up!')).toBeVisible();
  });
});
