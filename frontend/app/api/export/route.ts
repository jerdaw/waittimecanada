import { NextRequest, NextResponse } from 'next/server';
import { getDb } from '@/utils/db';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const province = searchParams.get('province');
  const startDate = searchParams.get('start_date');
  const endDate = searchParams.get('end_date');
  const format = searchParams.get('format') || 'csv';
  const includeMethodology = searchParams.get('include_methodology') !== 'false';

  try {
    const sql = getDb();

    // Build the query with conditional filters
    const results = await sql`
      SELECT
        m.timestamp_utc,
        m.hospital_id,
        h.name as hospital_name,
        h.province,
        h.city,
        h.latitude,
        h.longitude,
        m.value as wait_time_minutes,
        m.metric_family,
        m.start_event,
        m.end_event,
        m.statistic_type,
        m.patient_scope,
        s.id as source_id,
        s.name as source_name,
        s.methodology_url
      FROM measurements m
      JOIN hospitals h ON m.hospital_id = h.id
      JOIN sources s ON h.source_id = s.id
      WHERE h.is_verified = true
      ${province ? sql`AND h.province = ${province}` : sql``}
      ${startDate ? sql`AND m.timestamp_utc >= ${startDate}::timestamptz` : sql``}
      ${endDate ? sql`AND m.timestamp_utc <= ${endDate}::timestamptz` : sql``}
      ORDER BY m.timestamp_utc DESC
      LIMIT 10000
    `;

    // Format response as JSON
    if (format === 'json') {
      return NextResponse.json({
        data: results,
        metadata: {
          exported_at: new Date().toISOString(),
          record_count: results.length,
          filters: { province, startDate, endDate },
          license: 'CC-BY-4.0',
          citation: 'WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca',
        },
      });
    }

    // Format response as CSV
    const headers = [
      'timestamp_utc',
      'hospital_id',
      'hospital_name',
      'province',
      'city',
      'latitude',
      'longitude',
      'wait_time_minutes',
      ...(includeMethodology
        ? ['metric_family', 'start_event', 'end_event', 'statistic_type', 'patient_scope']
        : []),
      'source_id',
      'source_name',
      'methodology_url',
    ];

    const csvRows = [
      headers.join(','),
      ...results.map((row: any) =>
        headers
          .map((h) => {
            const val = row[h];
            // Escape commas and quotes
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
              return `"${val.replace(/"/g, '""')}"`;
            }
            return val ?? '';
          })
          .join(',')
      ),
    ];

    const csv = csvRows.join('\n');
    const filename = `waittime-canada-export-${new Date().toISOString().split('T')[0]}.csv`;

    return new NextResponse(csv, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'X-Data-License': 'CC-BY-4.0',
        'X-Citation': 'WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca',
      },
    });
  } catch (error) {
    console.error('Export API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to export data',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
