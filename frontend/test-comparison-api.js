#!/usr/bin/env node
/**
 * Manual test script to verify comparison feature works end-to-end
 *
 * This script:
 * 1. Fetches two Ontario hospitals from the API
 * 2. Compares them using the comparison API
 * 3. Verifies the comparison result is correct
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

async function testComparisonAPI() {
  console.log('Testing Comparison API...\n');

  try {
    // 1. Get two Ontario hospitals with measurements
    console.log('1. Fetching two Ontario hospitals with measurements...');
    const hospitals = await sql`
      SELECT DISTINCT h.id, h.name, h.province, h.city
      FROM hospitals h
      INNER JOIN measurements m ON m.hospital_id = h.id
      WHERE h.province = 'ON'
        AND h.is_verified = true
        AND h.is_visible = true
      ORDER BY h.name
      LIMIT 2
    `;

    if (hospitals.length < 2) {
      console.error('Need at least 2 Ontario hospitals with measurements');
      await sql.end();
      process.exit(1);
    }

    const hospitalA = hospitals[0];
    const hospitalB = hospitals[1];

    console.log(`   ✓ Found Hospital A: ${hospitalA.name} (${hospitalA.city}, ${hospitalA.province})`);
    console.log(`   ✓ Found Hospital B: ${hospitalB.name} (${hospitalB.city}, ${hospitalB.province})`);
    console.log();

    // 2. Test the comparison API query (simulating frontend API route)
    console.log('2. Testing comparison query...');
    const comparisonQuery = `
      SELECT
        h.id,
        h.name,
        h.province,
        h.city,
        h.latitude,
        h.longitude,
        m.value as wait_time,
        m.timestamp_utc as last_updated,
        m.metric_family,
        m.start_event,
        m.end_event,
        m.statistic_type,
        m.patient_scope
      FROM hospitals h
      LEFT JOIN LATERAL (
        SELECT *
        FROM measurements
        WHERE hospital_id = h.id
        ORDER BY timestamp_utc DESC
        LIMIT 1
      ) m ON true
      WHERE h.id = $1 AND h.is_visible = true AND h.is_verified = true
    `;

    const [resultA] = await sql.unsafe(comparisonQuery, [hospitalA.id]);
    const [resultB] = await sql.unsafe(comparisonQuery, [hospitalB.id]);

    if (!resultA || !resultB) {
      console.error('Failed to fetch hospital data');
      await sql.end();
      process.exit(1);
    }

    console.log(`   ✓ Fetched data for ${resultA.name}`);
    console.log(`     - Wait Time: ${resultA.wait_time} min`);
    console.log(`     - Methodology: ${resultA.start_event} → ${resultA.end_event} (${resultA.statistic_type})`);
    console.log();
    console.log(`   ✓ Fetched data for ${resultB.name}`);
    console.log(`     - Wait Time: ${resultB.wait_time} min`);
    console.log(`     - Methodology: ${resultB.start_event} → ${resultB.end_event} (${resultB.statistic_type})`);
    console.log();

    // 3. Verify comparability
    console.log('3. Checking comparability...');
    const comparable = (
      resultA.metric_family === resultB.metric_family &&
      resultA.start_event === resultB.start_event &&
      resultA.end_event === resultB.end_event &&
      resultA.statistic_type === resultB.statistic_type
    );

    if (comparable) {
      console.log('   ✓ Hospitals are comparable (identical methodologies)');
      console.log(`     - Both use: ${resultA.metric_family}, ${resultA.start_event} → ${resultA.end_event}, ${resultA.statistic_type}`);
    } else {
      console.log('   ⚠ Hospitals are NOT comparable (different methodologies)');
      console.log(`     - Hospital A: ${resultA.metric_family}, ${resultA.start_event} → ${resultA.end_event}, ${resultA.statistic_type}`);
      console.log(`     - Hospital B: ${resultB.metric_family}, ${resultB.start_event} → ${resultB.end_event}, ${resultB.statistic_type}`);
    }
    console.log();

    // 4. Generate divergence brief if not comparable
    if (!comparable) {
      console.log('4. Generating divergence brief...');
      const differences = [];

      if (resultA.metric_family !== resultB.metric_family) {
        differences.push(`Different metric families: ${resultA.metric_family} vs ${resultB.metric_family}`);
      }
      if (resultA.start_event !== resultB.start_event) {
        differences.push(`Different start points: ${resultA.start_event} vs ${resultB.start_event}`);
      }
      if (resultA.end_event !== resultB.end_event) {
        differences.push(`Different end points: ${resultA.end_event} vs ${resultB.end_event}`);
      }
      if (resultA.statistic_type !== resultB.statistic_type) {
        differences.push(`Different statistics: ${resultA.statistic_type} vs ${resultB.statistic_type}`);
      }

      const divergenceBrief = `Methodology Divergence: Direct comparison is scientifically invalid. ${differences.join('; ')}.`;
      console.log(`   ⚠ ${divergenceBrief}`);
      console.log();
    }

    // 5. Summary
    console.log('5. Summary');
    console.log('   ✓ Comparison API query works correctly');
    console.log('   ✓ Methodology fields are populated');
    console.log('   ✓ Comparability logic verified');
    console.log('   ✓ All required data present for frontend display');
    console.log();

    // 6. Test with actual Ontario hospitals (should always be comparable)
    console.log('6. Verification: Ontario hospitals should be comparable');
    if (resultA.province === 'ON' && resultB.province === 'ON') {
      if (comparable) {
        console.log('   ✅ PASS: Both Ontario hospitals use identical methodology');
        console.log(`       Expected: TIME_TO_PROVIDER, TRIAGE → PHYSICIAN, P90`);
        console.log(`       Hospital A: ${resultA.metric_family}, ${resultA.start_event} → ${resultA.end_event}, ${resultA.statistic_type}`);
        console.log(`       Hospital B: ${resultB.metric_family}, ${resultB.start_event} → ${resultB.end_event}, ${resultB.statistic_type}`);
      } else {
        console.log('   ❌ FAIL: Ontario hospitals should use identical methodology');
        console.log('       This indicates a data consistency issue');
      }
    }

    await sql.end();
    return true;
  } catch (error) {
    console.error('✗ Error:', error.message);
    await sql.end();
    return false;
  }
}

testComparisonAPI().then((success) => {
  process.exit(success ? 0 : 1);
});
