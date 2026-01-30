-- 003_create_rls_policies.sql
-- Row Level Security policies for Supabase
-- Depends on: 002_create_tables.sql

-- Enable RLS on all tables
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraper_status ENABLE ROW LEVEL SECURITY;

-- Public read access to sources (no sensitive data)
CREATE POLICY "Public can view sources"
    ON sources FOR SELECT
    TO anon, authenticated
    USING (true);

-- Public can only view verified, visible hospitals
CREATE POLICY "Public can view verified hospitals"
    ON hospitals FOR SELECT
    TO anon, authenticated
    USING (is_visible = true AND is_verified = true);

-- Authenticated users can view all hospitals (for admin UI)
CREATE POLICY "Authenticated can view all hospitals"
    ON hospitals FOR SELECT
    TO authenticated
    USING (true);

-- Public can view recent measurements for visible hospitals
CREATE POLICY "Public can view measurements for visible hospitals"
    ON measurements FOR SELECT
    TO anon, authenticated
    USING (
        EXISTS (
            SELECT 1 FROM hospitals
            WHERE hospitals.id = measurements.hospital_id
            AND hospitals.is_visible = true
            AND hospitals.is_verified = true
        )
    );

-- Public can view scraper status (transparency)
CREATE POLICY "Public can view scraper status"
    ON scraper_status FOR SELECT
    TO anon, authenticated
    USING (true);

-- Service role can do everything (for scrapers via API key)
-- Note: service_role bypasses RLS by default in Supabase

-- Rollback:
-- DROP POLICY IF EXISTS "Public can view sources" ON sources;
-- DROP POLICY IF EXISTS "Public can view verified hospitals" ON hospitals;
-- DROP POLICY IF EXISTS "Authenticated can view all hospitals" ON hospitals;
-- DROP POLICY IF EXISTS "Public can view measurements for visible hospitals" ON measurements;
-- DROP POLICY IF EXISTS "Public can view scraper status" ON scraper_status;
-- ALTER TABLE sources DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE hospitals DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE measurements DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE scraper_status DISABLE ROW LEVEL SECURITY;
