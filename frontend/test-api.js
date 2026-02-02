#!/usr/bin/env node
/**
 * Quick test script to verify API endpoints work with seeded data
 */

const postgres = require('postgres');
const fs = require('fs');
const path = require('path');

// Read DATABASE_URL from .env.local
const envPath = path.join(__dirname, '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
const dbUrlMatch = envContent.match(/DATABASE_URL=(.+)/);
const DATABASE_URL = dbUrlMatch ? dbUrlMatch[1].trim() : '';

if (!DATABASE_URL) {
  console.error('DATABASE_URL not found in .env.local');
  process.exit(1);
}

const sql = postgres(DATABASE_URL, {
  ssl: 'require',
});

async function testHospitalsAPI() {
  console.log('Testing hospitals API query...\n');

  try {
    const query = `
      SELECT
        h.id,
        h.name,
        h.province,
        h.city,
        h.latitude,
        h.longitude,
        h.is_verified,
        h.is_visible,
        h.source_id,
        m.value as current_wait_time,
        m.timestamp_utc as last_updated,
        m.metric_family,
        m.start_event,
        m.end_event,
        m.statistic_type,
        m.patient_scope
      FROM hospitals h
      LEFT JOIN LATERAL (
        SELECT
          value,
          timestamp_utc,
          metric_family,
          start_event,
          end_event,
          statistic_type,
          patient_scope
        FROM measurements
        WHERE hospital_id = h.id
        ORDER BY timestamp_utc DESC
        LIMIT 1
      ) m ON true
      WHERE h.is_visible = true AND h.is_verified = true
      ORDER BY h.name
      LIMIT 5
    `;

    const hospitals = await sql.unsafe(query);

    console.log(`✓ Found ${hospitals.length} hospitals (showing first 5)\n`);

    hospitals.forEach((h) => {
      console.log(`Hospital: ${h.name}`);
      console.log(`  Location: ${h.city}, ${h.province}`);
      console.log(`  Coordinates: ${h.latitude}, ${h.longitude}`);
      if (h.current_wait_time) {
        console.log(`  Current Wait: ${h.current_wait_time} min`);
        console.log(`  Methodology: ${h.start_event} → ${h.end_event} (${h.statistic_type})`);
        console.log(`  Updated: ${h.last_updated}`);
      } else {
        console.log(`  Current Wait: No data`);
      }
      console.log();
    });

    await sql.end();
    return true;
  } catch (error) {
    console.error('✗ Error:', error.message);
    await sql.end();
    return false;
  }
}

testHospitalsAPI().then((success) => {
  process.exit(success ? 0 : 1);
});
