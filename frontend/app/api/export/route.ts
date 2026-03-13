import { NextRequest, NextResponse } from "next/server";
import { getDb } from "@/utils/db";
import { NO_STORE_HEADERS } from "@/utils/cache";

import { ExportQuerySchema } from "@/utils/validations";

const MAX_HOURLY_EXPORT_WINDOW_MS = 30 * 24 * 60 * 60 * 1000;

function computeMethodologyHomogeneity(results: Record<string, unknown>[]) {
  const groupsMap = new Map<string, any>();
  for (const row of results) {
    const key = `${row.metric_family}|${row.start_event}|${row.end_event}|${row.statistic_type}`;
    if (!groupsMap.has(key)) {
      groupsMap.set(key, {
        metric_family: String(row.metric_family),
        start_event: String(row.start_event),
        end_event: String(row.end_event),
        statistic_type: String(row.statistic_type),
        record_count: 0,
      });
    }
    groupsMap.get(key)!.record_count++;
  }

  const groups = Array.from(groupsMap.values());
  const is_homogeneous = groups.length <= 1;

  return {
    is_homogeneous,
    distinct_methodology_groups: groups.length,
    divergence_note: is_homogeneous
      ? null
      : `This export contains measurements from ${groups.length} distinct methodology groups. Direct comparison across groups is scientifically invalid. See methodology_url per record for details.`,
    groups,
  };
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const rawParams = Object.fromEntries(searchParams.entries());

  // Handle include_methodology defaulting logic manually if needed or via Zod transformer
  // Zod transformer in schema handles "true"/"false" strings -> boolean.
  // But rawParams from URLSearchParams are strings.
  // ExportQuerySchema handles this.

  const validation = ExportQuerySchema.safeParse(rawParams);

  if (!validation.success) {
    return NextResponse.json(
      {
        success: false,
        error: "Validation Error",
        details: validation.error.format(),
      },
      { status: 400 },
    );
  }

  const {
    province,
    start_date: startDate,
    end_date: endDate,
    format,
    include_methodology: includeMethodology,
    granularity,
  } = validation.data;

  try {
    const sql = getDb();

    if (granularity === "hourly") {
      const hourlyEnd = endDate ? new Date(endDate) : new Date();
      const hourlyStart = startDate
        ? new Date(startDate)
        : new Date(hourlyEnd.getTime() - MAX_HOURLY_EXPORT_WINDOW_MS);

      if (
        Number.isNaN(hourlyStart.getTime()) ||
        Number.isNaN(hourlyEnd.getTime()) ||
        hourlyStart >= hourlyEnd
      ) {
        return NextResponse.json(
          {
            success: false,
            error: "Invalid hourly export window",
            message: "Hourly exports require a valid start_date before end_date.",
          },
          { status: 400, headers: NO_STORE_HEADERS },
        );
      }

      if (hourlyEnd.getTime() - hourlyStart.getTime() > MAX_HOURLY_EXPORT_WINDOW_MS) {
        return NextResponse.json(
          {
            success: false,
            error: "Hourly export window too large",
            message:
              "Hourly exports are limited to 30 days. Use daily, weekly, or monthly granularity for longer windows.",
          },
          { status: 400, headers: NO_STORE_HEADERS },
        );
      }

      const results = await sql`
        SELECT
          date_trunc('hour', m.timestamp_utc) AS period_start,
          date_trunc('hour', m.timestamp_utc) + INTERVAL '1 hour' AS period_end,
          m.hospital_id,
          h.name as hospital_name,
          h.province,
          h.city,
          h.latitude,
          h.longitude,
          AVG(m.value)::float AS mean_wait_minutes,
          PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.value)::float AS median_wait_minutes,
          PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY m.value)::float AS p90_wait_minutes,
          MIN(m.value)::float AS min_wait_minutes,
          MAX(m.value)::float AS max_wait_minutes,
          COUNT(*)::int AS sample_count,
          STDDEV_SAMP(m.value)::float AS std_dev,
          m.metric_family,
          m.start_event,
          m.end_event,
          m.statistic_type,
          m.source_id,
          s.methodology_url
        FROM measurements m
        JOIN hospitals h ON m.hospital_id = h.id
        JOIN sources s ON m.source_id = s.id
        WHERE h.is_verified = true
          ${province ? sql`AND h.province = ${province}` : sql``}
          AND m.timestamp_utc >= ${hourlyStart.toISOString()}::timestamptz
          AND m.timestamp_utc <= ${hourlyEnd.toISOString()}::timestamptz
        GROUP BY
          date_trunc('hour', m.timestamp_utc),
          m.hospital_id,
          h.name,
          h.province,
          h.city,
          h.latitude,
          h.longitude,
          m.metric_family,
          m.start_event,
          m.end_event,
          m.statistic_type,
          m.source_id,
          s.methodology_url
        ORDER BY period_start DESC
        LIMIT 10000
      `;

      const homogeneity = computeMethodologyHomogeneity(results);

      if (format === "json") {
        return NextResponse.json(
          {
            data: results,
            metadata: {
              exported_at: new Date().toISOString(),
              record_count: results.length,
              data_type: "aggregated",
              granularity,
              filters: {
                province,
                startDate: hourlyStart.toISOString(),
                endDate: hourlyEnd.toISOString(),
              },
              methodology_homogeneity: homogeneity,
              license: "CC-BY-4.0",
              citation:
                "Wait Time Canada. (2026). Canadian ER Wait Time Data [Data set]. https://wait-time.ca",
            },
          },
          { headers: NO_STORE_HEADERS },
        );
      }

      const aggHeaders = [
        "period_start",
        "period_end",
        "hospital_id",
        "hospital_name",
        "province",
        "city",
        "latitude",
        "longitude",
        "mean_wait_minutes",
        "median_wait_minutes",
        "p90_wait_minutes",
        "min_wait_minutes",
        "max_wait_minutes",
        "sample_count",
        "std_dev",
        ...(includeMethodology
          ? ["metric_family", "start_event", "end_event", "statistic_type"]
          : []),
        "source_id",
        "methodology_url",
      ];

      const csvRows = [];
      if (!homogeneity.is_homogeneous) {
        csvRows.push(
          `# METHODOLOGY DIVERGENCE WARNING: ${homogeneity.divergence_note}`,
        );
      }
      csvRows.push(aggHeaders.join(","));
      csvRows.push(
        ...results.map((row: Record<string, unknown>) =>
          aggHeaders
            .map((header) => {
              const val = row[header] as string | number | null | undefined;
              if (
                typeof val === "string" &&
                (val.includes(",") || val.includes('"'))
              ) {
                return `"${val.replace(/"/g, '""')}"`;
              }
              return val ?? "";
            })
            .join(","),
        ),
      );

      const csv = csvRows.join("\n");
      const filename = `wait-time-ca-hourly-export-${new Date().toISOString().split("T")[0]}.csv`;

      return new NextResponse(csv, {
        headers: {
          "Content-Type": "text/csv",
          "Content-Disposition": `attachment; filename="${filename}"`,
          "X-Data-License": "CC-BY-4.0",
          "X-Data-Type": "aggregated",
          "X-Granularity": granularity,
          "X-Methodology-Divergence": String(!homogeneity.is_homogeneous),
          "X-Methodology-Groups": String(
            homogeneity.distinct_methodology_groups,
          ),
          ...NO_STORE_HEADERS,
        },
      });
    }

    if (granularity !== "raw") {
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

      const homogeneity = computeMethodologyHomogeneity(results);

      if (format === "json") {
        return NextResponse.json(
          {
            data: results,
            metadata: {
              exported_at: new Date().toISOString(),
              record_count: results.length,
              data_type: "aggregated",
              granularity,
              filters: { province, startDate, endDate },
              methodology_homogeneity: homogeneity,
              license: "CC-BY-4.0",
              citation:
                "Wait Time Canada. (2026). Canadian ER Wait Time Data [Data set]. https://wait-time.ca",
            },
          },
          { headers: NO_STORE_HEADERS },
        );
      }

      // CSV for aggregated data
      const aggHeaders = [
        "period_start",
        "period_end",
        "hospital_id",
        "hospital_name",
        "province",
        "city",
        "latitude",
        "longitude",
        "mean_wait_minutes",
        "median_wait_minutes",
        "p90_wait_minutes",
        "min_wait_minutes",
        "max_wait_minutes",
        "sample_count",
        "std_dev",
        ...(includeMethodology
          ? ["metric_family", "start_event", "end_event", "statistic_type"]
          : []),
        "source_id",
        "methodology_url",
      ];

      const csvRows = [];
      if (!homogeneity.is_homogeneous) {
        csvRows.push(
          `# METHODOLOGY DIVERGENCE WARNING: ${homogeneity.divergence_note}`,
        );
      }
      csvRows.push(aggHeaders.join(","));

      csvRows.push(
        ...results.map((row: Record<string, unknown>) =>
          aggHeaders
            .map((h) => {
              const val = row[h] as string | number | null | undefined;
              if (
                typeof val === "string" &&
                (val.includes(",") || val.includes('"'))
              ) {
                return `"${val.replace(/"/g, '""')}"`;
              }
              return val ?? "";
            })
            .join(","),
        ),
      );

      const csv = csvRows.join("\n");
      const filename = `wait-time-ca-${granularity}-export-${new Date().toISOString().split("T")[0]}.csv`;

      return new NextResponse(csv, {
        headers: {
          "Content-Type": "text/csv",
          "Content-Disposition": `attachment; filename="${filename}"`,
          "X-Data-License": "CC-BY-4.0",
          "X-Data-Type": "aggregated",
          "X-Granularity": granularity,
          "X-Methodology-Divergence": String(!homogeneity.is_homogeneous),
          "X-Methodology-Groups": String(
            homogeneity.distinct_methodology_groups,
          ),
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

    const homogeneity = computeMethodologyHomogeneity(results);

    // Format response as JSON
    if (format === "json") {
      return NextResponse.json(
        {
          data: results,
          metadata: {
            exported_at: new Date().toISOString(),
            record_count: results.length,
            data_type: "raw",
            granularity: "raw",
            filters: { province, startDate, endDate },
            methodology_homogeneity: homogeneity,
            license: "CC-BY-4.0",
            citation:
              "Wait Time Canada. (2026). Canadian ER Wait Time Data [Data set]. https://wait-time.ca",
          },
        },
        { headers: NO_STORE_HEADERS },
      );
    }

    // Format response as CSV
    const headers = [
      "timestamp_utc",
      "hospital_id",
      "hospital_name",
      "province",
      "city",
      "latitude",
      "longitude",
      "wait_time_minutes",
      ...(includeMethodology
        ? [
            "metric_family",
            "start_event",
            "end_event",
            "statistic_type",
            "patient_scope",
          ]
        : []),
      "source_id",
      "source_name",
      "methodology_url",
    ];

    const csvRows = [];
    if (!homogeneity.is_homogeneous) {
      csvRows.push(
        `# METHODOLOGY DIVERGENCE WARNING: ${homogeneity.divergence_note}`,
      );
    }
    csvRows.push(headers.join(","));

    csvRows.push(
      ...results.map((row: Record<string, unknown>) =>
        headers
          .map((h) => {
            const val = row[h] as string | number | null | undefined;
            // Escape commas and quotes
            if (
              typeof val === "string" &&
              (val.includes(",") || val.includes('"'))
            ) {
              return `"${val.replace(/"/g, '""')}"`;
            }
            return val ?? "";
          })
          .join(","),
      ),
    );

    const csv = csvRows.join("\n");
    const filename = `wait-time-ca-export-${new Date().toISOString().split("T")[0]}.csv`;

    return new NextResponse(csv, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="${filename}"`,
        "X-Data-License": "CC-BY-4.0",
        "X-Data-Type": "raw",
        "X-Methodology-Divergence": String(!homogeneity.is_homogeneous),
        "X-Methodology-Groups": String(homogeneity.distinct_methodology_groups),
        ...NO_STORE_HEADERS,
      },
    });
  } catch (error) {
    console.error("Export API error:", error);
    return NextResponse.json(
      {
        error: "Failed to export data",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500, headers: NO_STORE_HEADERS },
    );
  }
}
