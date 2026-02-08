import { NextRequest, NextResponse } from 'next/server';
import { getDb } from '@/utils/db';
import { NO_STORE_HEADERS } from '@/utils/cache';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const province = searchParams.get('province');
  const startDate = searchParams.get('start_date');
  const endDate = searchParams.get('end_date');
  const format = searchParams.get('format') || 'csv';
  const includeMethodology = searchParams.get('include_methodology') !== 'false';
  const granularity = searchParams.get('granularity') || 'raw';

  try {
    const sql = getDb();

    if (granularity !== 'raw') {
      // Serve aggregated data from measurement_aggregates table
      const results = await sql`
        SELECT
          ma.period_start,
          ma.period_end,
          ma.hospital_id,
          h.name as hospital_name,
          h.province,
          h.city,
          h.latitude,
          h.longitude,
          ma.mean_value as mean_wait_minutes,
          ma.median_value as median_wait_minutes,
          ma.p90_value as p90_wait_minutes,
          ma.min_value as min_wait_minutes,
          ma.max_value as max_wait_minutes,
          ma.sample_count,
          ma.std_dev,
          ma.metric_family,
          ma.start_event,
          ma.end_event,
          ma.statistic_type,
          ma.source_id,
          s.methodology_url
        FROM measurement_aggregates ma
        JOIN hospitals h ON ma.hospital_id = h.id
        JOIN sources s ON ma.source_id = s.id
        WHERE h.is_verified = true
        AND ma.period_type = ${granularity}
        ${province ? sql`AND h.province = ${province}` : sql``}
        ${startDate ? sql`AND ma.period_start >= ${startDate}::timestamptz` : sql``}
        ${endDate ? sql`AND ma.period_start <= ${endDate}::timestamptz` : sql``}
        ORDER BY ma.period_start DESC
        LIMIT 10000
      `;

      if (format === 'json') {
        return NextResponse.json(
          {
            data: results,
            metadata: {
              exported_at: new Date().toISOString(),
              record_count: results.length,
              data_type: 'aggregated',
              granularity,
              filters: { province, startDate, endDate },
              license: 'CC-BY-4.0',
              citation:
                'WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca',
            },
          },
          { headers: NO_STORE_HEADERS }
        );
      }

      // CSV for aggregated data
      const aggHeaders = [
        'period_start',
        'period_end',
        'hospital_id',
        'hospital_name',
        'province',
        'city',
        'latitude',
        'longitude',
        'mean_wait_minutes',
        'median_wait_minutes',
        'p90_wait_minutes',
        'min_wait_minutes',
        'max_wait_minutes',
        'sample_count',
        'std_dev',
        ...(includeMethodology
          ? ['metric_family', 'start_event', 'end_event', 'statistic_type']
          : []),
        'source_id',
        'methodology_url',
      ];

      const csvRows = [
        aggHeaders.join(','),
        ...results.map((row: any) =>
          aggHeaders
            .map((h) => {
              const val = row[h];
              if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
                return `"${val.replace(/"/g, '""')}"`;
              }
              return val ?? '';
            })
            .join(',')
        ),
      ];

      const csv = csvRows.join('\n');
      const filename = `waittime-canada-${granularity}-export-${new Date().toISOString().split('T')[0]}.csv`;

      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="${filename}"`,
          'X-Data-License': 'CC-BY-4.0',
          'X-Data-Type': 'aggregated',
          'X-Granularity': granularity,
          ...NO_STORE_HEADERS,
        },
      });
    }

    // Raw data export (existing behavior)
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
      return NextResponse.json(
        {
          data: results,
          metadata: {
            exported_at: new Date().toISOString(),
            record_count: results.length,
            data_type: 'raw',
            granularity: 'raw',
            filters: { province, startDate, endDate },
            license: 'CC-BY-4.0',
            citation:
              'WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca',
          },
        },
        { headers: NO_STORE_HEADERS }
      );
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
        'X-Data-Type': 'raw',
        ...NO_STORE_HEADERS,
      },
    });
  } catch (error) {
    console.error('Export API error:', error);
    return NextResponse.json(
      {
        error: 'Failed to export data',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500, headers: NO_STORE_HEADERS }
    );
  }
}
