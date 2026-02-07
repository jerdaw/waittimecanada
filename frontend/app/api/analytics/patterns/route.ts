import { NextResponse } from "next/server";
import { getDb } from "@/utils/db";

type PatternType = "hour_of_day" | "day_of_week" | "monthly";

interface HourPattern {
  hour: number;
  mean: number | null;
  median: number | null;
  sample_count: number;
}

interface DayPattern {
  day: string;
  day_index: number;
  mean: number | null;
  median: number | null;
  sample_count: number;
}

interface MonthPattern {
  month: string;
  mean: number | null;
  median: number | null;
  sample_count: number;
}

const VALID_TYPES: PatternType[] = ["hour_of_day", "day_of_week", "monthly"];
const DAYS_OF_WEEK = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

function mean(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function toNumber(value: unknown): number {
  if (value === null || value === undefined) return 0;
  return Number(value);
}

function parseType(value: string | null): PatternType {
  if (!value) return "hour_of_day";
  if (VALID_TYPES.includes(value as PatternType)) {
    return value as PatternType;
  }
  throw new Error("Invalid type");
}

function parsePositiveInt(value: string | null, fallback: number, max: number): number {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed <= 0 || parsed > max) {
    throw new Error("Invalid lookback value");
  }
  return parsed;
}

function formatDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export async function GET(request: Request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);

    const hospitalId = searchParams.get("hospital_id");
    if (!hospitalId) {
      return NextResponse.json(
        {
          success: false,
          error: "Missing required parameter",
          message: "Query parameter 'hospital_id' is required",
        },
        { status: 400 }
      );
    }

    let patternType: PatternType;
    try {
      patternType = parseType(searchParams.get("type"));
    } catch {
      return NextResponse.json(
        {
          success: false,
          error: "Invalid pattern type",
          message: "Supported type values: hour_of_day, day_of_week, monthly",
        },
        { status: 400 }
      );
    }

    const hospitalRows = await sql`
      SELECT id, name
      FROM hospitals
      WHERE id = ${hospitalId}
        AND is_visible = true
        AND is_verified = true
      LIMIT 1
    `;

    if (hospitalRows.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: "Hospital not found",
          message: "Hospital not found or not visible",
        },
        { status: 404 }
      );
    }

    const hospitalName = String(hospitalRows[0].name);
    const now = new Date();

    if (patternType === "hour_of_day") {
      const lookbackDays = parsePositiveInt(searchParams.get("lookback_days"), 30, 365);
      const start = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000);

      const rows = await sql`
        SELECT
          EXTRACT(HOUR FROM period_start)::int AS hour,
          AVG(mean_value)::float AS mean,
          AVG(median_value)::float AS median,
          SUM(sample_count)::int AS sample_count
        FROM measurement_aggregates
        WHERE hospital_id = ${hospitalId}
          AND period_type = 'hourly'
          AND period_start >= ${start.toISOString()}::timestamptz
        GROUP BY EXTRACT(HOUR FROM period_start)
        ORDER BY hour
      `;

      const byHour = new Map<number, HourPattern>();
      for (const row of rows) {
        byHour.set(Number(row.hour), {
          hour: Number(row.hour),
          mean: row.mean === null ? null : Number(Number(row.mean).toFixed(1)),
          median: row.median === null ? null : Number(Number(row.median).toFixed(1)),
          sample_count: toNumber(row.sample_count),
        });
      }

      const patterns: HourPattern[] = Array.from({ length: 24 }, (_, hour) => {
        return (
          byHour.get(hour) ?? {
            hour,
            mean: null,
            median: null,
            sample_count: 0,
          }
        );
      });

      const populated = patterns.filter((row) => row.mean !== null);
      const peak = populated.length
        ? populated.reduce((best, row) => ((row.mean ?? 0) > (best.mean ?? 0) ? row : best))
        : null;
      const quiet = populated.length
        ? populated.reduce((best, row) => ((row.mean ?? 0) < (best.mean ?? 0) ? row : best))
        : null;

      const peakMean = peak?.mean ?? null;
      const quietMean = quiet?.mean ?? null;

      return NextResponse.json({
        success: true,
        data: {
          hospital_id: hospitalId,
          hospital_name: hospitalName,
          pattern_type: "hour_of_day",
          data_period: {
            start: formatDate(start),
            end: formatDate(now),
          },
          sample_count: patterns.reduce((sum, row) => sum + row.sample_count, 0),
          patterns,
          insights: {
            peak_hour: peak?.hour ?? null,
            quietest_hour: quiet?.hour ?? null,
            peak_mean: peakMean,
            quietest_mean: quietMean,
            peak_vs_quiet_ratio:
              peakMean !== null && quietMean !== null && quietMean > 0
                ? Number((peakMean / quietMean).toFixed(2))
                : null,
          },
        },
      });
    }

    if (patternType === "day_of_week") {
      const lookbackDays = parsePositiveInt(searchParams.get("lookback_days"), 90, 365);
      const start = new Date(now.getTime() - lookbackDays * 24 * 60 * 60 * 1000);

      const rows = await sql`
        SELECT
          EXTRACT(ISODOW FROM period_start)::int - 1 AS day_index,
          AVG(mean_value)::float AS mean,
          AVG(median_value)::float AS median,
          SUM(sample_count)::int AS sample_count
        FROM measurement_aggregates
        WHERE hospital_id = ${hospitalId}
          AND period_type = 'daily'
          AND period_start >= ${start.toISOString()}::timestamptz
        GROUP BY EXTRACT(ISODOW FROM period_start)
        ORDER BY day_index
      `;

      const byDay = new Map<number, DayPattern>();
      for (const row of rows) {
        const dayIndex = Number(row.day_index);
        byDay.set(dayIndex, {
          day: DAYS_OF_WEEK[dayIndex],
          day_index: dayIndex,
          mean: row.mean === null ? null : Number(Number(row.mean).toFixed(1)),
          median: row.median === null ? null : Number(Number(row.median).toFixed(1)),
          sample_count: toNumber(row.sample_count),
        });
      }

      const patterns: DayPattern[] = DAYS_OF_WEEK.map((day, dayIndex) => {
        return (
          byDay.get(dayIndex) ?? {
            day,
            day_index: dayIndex,
            mean: null,
            median: null,
            sample_count: 0,
          }
        );
      });

      const populated = patterns.filter((row) => row.mean !== null);
      const worst = populated.length
        ? populated.reduce((best, row) => ((row.mean ?? 0) > (best.mean ?? 0) ? row : best))
        : null;
      const best = populated.length
        ? populated.reduce((best, row) => ((row.mean ?? 0) < (best.mean ?? 0) ? row : best))
        : null;

      const weekendMean = mean(
        patterns
          .filter((row) => row.day_index >= 5 && row.mean !== null)
          .map((row) => Number(row.mean))
      );
      const weekdayMean = mean(
        patterns
          .filter((row) => row.day_index <= 4 && row.mean !== null)
          .map((row) => Number(row.mean))
      );

      return NextResponse.json({
        success: true,
        data: {
          hospital_id: hospitalId,
          hospital_name: hospitalName,
          pattern_type: "day_of_week",
          data_period: {
            start: formatDate(start),
            end: formatDate(now),
          },
          sample_count: patterns.reduce((sum, row) => sum + row.sample_count, 0),
          patterns,
          insights: {
            worst_day: worst?.day ?? null,
            best_day: best?.day ?? null,
            weekend_vs_weekday_ratio:
              weekendMean !== null && weekdayMean !== null && weekdayMean > 0
                ? Number((weekendMean / weekdayMean).toFixed(2))
                : null,
          },
        },
      });
    }

    const lookbackMonths = parsePositiveInt(searchParams.get("lookback_months"), 12, 36);
    const start = new Date(now.getTime() - lookbackMonths * 31 * 24 * 60 * 60 * 1000);

    const rows = await sql`
      SELECT
        date_trunc('month', period_start) AS month_start,
        AVG(mean_value)::float AS mean,
        AVG(median_value)::float AS median,
        SUM(sample_count)::int AS sample_count
      FROM measurement_aggregates
      WHERE hospital_id = ${hospitalId}
        AND period_type = 'monthly'
        AND period_start >= ${start.toISOString()}::timestamptz
      GROUP BY date_trunc('month', period_start)
      ORDER BY month_start
    `;

    const patterns: MonthPattern[] = rows.map((row) => {
      const monthDate = new Date(String(row.month_start));
      return {
        month: `${monthDate.getUTCFullYear()}-${String(monthDate.getUTCMonth() + 1).padStart(2, "0")}`,
        mean: row.mean === null ? null : Number(Number(row.mean).toFixed(1)),
        median: row.median === null ? null : Number(Number(row.median).toFixed(1)),
        sample_count: toNumber(row.sample_count),
      };
    });

    const populated = patterns.filter((row) => row.mean !== null);
    const startMean = populated.length ? Number(populated[0].mean) : null;
    const endMean = populated.length ? Number(populated[populated.length - 1].mean) : null;

    let direction: "improving" | "stable" | "worsening" = "stable";
    let changePercent = 0;

    if (startMean !== null && endMean !== null && startMean > 0) {
      changePercent = Number((((endMean - startMean) / startMean) * 100).toFixed(1));
      if (changePercent < -5) {
        direction = "improving";
      } else if (changePercent > 5) {
        direction = "worsening";
      }
    }

    return NextResponse.json({
      success: true,
      data: {
        hospital_id: hospitalId,
        hospital_name: hospitalName,
        pattern_type: "monthly",
        data_period: {
          start: formatDate(start),
          end: formatDate(now),
        },
        sample_count: patterns.reduce((sum, row) => sum + row.sample_count, 0),
        patterns,
        insights: {
          direction,
          change_percent: changePercent,
          start_mean: startMean,
          end_mean: endMean,
        },
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    if (message.includes("Invalid lookback value")) {
      return NextResponse.json(
        {
          success: false,
          error: "Invalid lookback",
          message: "Lookback values must be positive integers within allowed limits",
        },
        { status: 400 }
      );
    }

    console.error("Failed to compute temporal patterns:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to compute temporal patterns",
        message,
      },
      { status: 500 }
    );
  }
}
