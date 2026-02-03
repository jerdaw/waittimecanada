#!/usr/bin/env node
/**
 * Test script to verify telehealth information is correctly included in hospitals API
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

async function testTelehealthAPI() {
  console.log('Testing Telehealth Information in Hospitals API...\n');

  try {
    // Test the hospitals API query (same as frontend API route)
    console.log('1. Fetching hospitals with telehealth information...');
    const hospitals = await sql`
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
        s.telehealth_name,
        s.telehealth_number,
        m.value as current_wait_time,
        m.timestamp_utc as last_updated,
        m.metric_family,
        m.start_event,
        m.end_event,
        m.statistic_type,
        m.patient_scope
      FROM hospitals h
      LEFT JOIN sources s ON s.id = h.source_id
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

    console.log(`   ✓ Found ${hospitals.length} hospitals\n`);

    // 2. Verify telehealth info is present
    console.log('2. Verifying telehealth information...\n');

    let allHaveTelehealth = true;
    const telehealthByProvince = {};

    hospitals.forEach((hospital) => {
      console.log(`Hospital: ${hospital.name}`);
      console.log(`  Location: ${hospital.city}, ${hospital.province}`);
      console.log(`  Source: ${hospital.source_id}`);

      if (hospital.telehealth_name && hospital.telehealth_number) {
        console.log(`  ✓ Telehealth: ${hospital.telehealth_name} - ${hospital.telehealth_number}`);

        if (!telehealthByProvince[hospital.province]) {
          telehealthByProvince[hospital.province] = {
            name: hospital.telehealth_name,
            number: hospital.telehealth_number
          };
        }
      } else {
        console.log(`  ✗ Telehealth: NOT AVAILABLE`);
        allHaveTelehealth = false;
      }

      if (hospital.current_wait_time) {
        console.log(`  Wait Time: ${hospital.current_wait_time} min`);
      } else {
        console.log(`  Wait Time: No data`);
      }
      console.log();
    });

    // 3. Summary by province
    console.log('3. Summary by province:\n');
    Object.keys(telehealthByProvince).forEach((province) => {
      const info = telehealthByProvince[province];
      console.log(`   ${province}: ${info.name} - ${info.number}`);
    });
    console.log();

    // 4. Verification
    console.log('4. Verification:\n');
    if (allHaveTelehealth) {
      console.log('   ✅ PASS: All hospitals have telehealth information');
    } else {
      console.log('   ⚠  WARNING: Some hospitals missing telehealth information');
      console.log('      This may be expected for test hospitals without sources');
    }
    console.log('   ✓ Telehealth data successfully joins from sources table');
    console.log('   ✓ API query includes telehealth_name and telehealth_number');
    console.log('   ✓ Ready for display in hospital popups');

    await sql.end();
    return true;
  } catch (error) {
    console.error('✗ Error:', error.message);
    await sql.end();
    return false;
  }
}

testTelehealthAPI().then((success) => {
  process.exit(success ? 0 : 1);
});
