import { z } from "zod";

export const ProvinceEnum = z.enum([
  "ON",
  "QC",
  "AB",
  "BC",
  "MB",
  "SK",
  "NS",
  "NB",
  "NL",
  "PE",
  "NT",
  "NU",
  "YT",
]);

export const PeriodEnum = z.enum(["weekly", "monthly"]);

export const LookbackEnum = z.enum(["3m", "6m", "1y"]);

// Common parameter schemas
export const ProvinceSchema = ProvinceEnum;
export const OptionalProvinceSchema = ProvinceEnum.optional();

export const PeriodSchema = PeriodEnum.default("monthly");
export const OptionalPeriodSchema = PeriodEnum.optional();

export const LookbackSchema = LookbackEnum.default("6m");
export const OptionalLookbackSchema = LookbackEnum.optional();

export const PaginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
});

// Specific Enums (Must be defined before use)
export const BenchmarkPeriodSchema = z.enum(["24h", "7d", "30d"]);
export const HospitalTrendPeriodSchema = z.enum([
  "24h",
  "7d",
  "30d",
  "90d",
  "6m",
  "1y",
]);

// Query schemas for specific routes
export const TrendsQuerySchema = z.object({
  province: ProvinceSchema,
  period: PeriodSchema,
  lookback: LookbackSchema,
  metric_family: z.string().default("TIME_TO_PROVIDER"),
});

export const HospitalQuerySchema = z.object({
  province: OptionalProvinceSchema,
  ...PaginationSchema.shape,
});

export const RegionQuerySchema = z.object({
  province: ProvinceSchema,
  period: BenchmarkPeriodSchema.default("7d"),
});

export const OccupancyQuerySchema = z.object({
  province: ProvinceSchema,
});

export const PatternsQuerySchema = z.object({
  hospital_id: z.string(),
  type: z
    .enum(["hour_of_day", "day_of_week", "monthly"])
    .default("hour_of_day"),
  lookback_days: z.coerce.number().int().positive().optional(),
  lookback_months: z.coerce.number().int().positive().optional(),
});

export const HospitalTrendQuerySchema = z.object({
  period: HospitalTrendPeriodSchema.default("24h"),
});

export const BenchmarkQuerySchema = z.object({
  province: ProvinceSchema,
  period: BenchmarkPeriodSchema.default("7d"),
  hospital_id: z.string().optional(),
});

export const CompareQuerySchema = z.object({
  a: z.string(),
  b: z.string(),
});

export const GeolocationQuerySchema = z.object({
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
  radius: z.coerce.number().positive().max(500).default(50), // km
  limit: z.coerce.number().int().positive().max(50).default(10),
});

export const AnomaliesQuerySchema = z.object({
  source_id: z.string().optional(),
  days: z.coerce.number().int().positive().max(30).default(7),
});

export const DataQualityQuerySchema = z
  .object({
    view: z.enum(["system", "hospital", "trend", "diff"]).optional(),
    hospital_id: z.string().optional(),
    source_id: z.string().optional(),
    days: z.coerce.number().int().positive().max(90).default(30),
    compare_days: z.coerce.number().int().positive().max(90).default(7),
  })
  .superRefine((data, ctx) => {
    const hasHospitalId = data.hospital_id !== undefined;
    const hasSourceId = data.source_id !== undefined;

    if (hasHospitalId && hasSourceId) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "hospital_id and source_id cannot be provided together",
        path: ["source_id"],
      });
    }

    if (data.view === "hospital" && !hasHospitalId) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "hospital_id is required when view=hospital",
        path: ["hospital_id"],
      });
    }

    if ((data.view === "trend" || data.view === "diff") && !hasSourceId) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "source_id is required when view=trend or view=diff",
        path: ["source_id"],
      });
    }

    if (hasSourceId && data.view !== "trend" && data.view !== "diff") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "source_id is only valid when view=trend or view=diff",
        path: ["source_id"],
      });
    }

    if (data.view === "system" && (hasHospitalId || hasSourceId)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "view=system cannot be combined with hospital_id or source_id",
        path: ["view"],
      });
    }
  });

export const ExportQuerySchema = z.object({
  province: ProvinceSchema.optional(),
  start_date: z.string().datetime().optional(), // ISO string
  end_date: z.string().datetime().optional(),
  format: z.enum(["csv", "json"]).default("csv"),
  include_methodology: z
    .enum(["true", "false"])
    .transform((val) => val !== "false")
    .default("true"),
  granularity: z
    .enum(["raw", "hourly", "daily", "weekly", "monthly"])
    .default("raw"),
});

export const ResourceKindSchema = z.enum(["facility", "aed"]);

export const ResourcesQuerySchema = z
  .object({
    kind: ResourceKindSchema,
    q: z.string().trim().min(1).max(200).optional(),
    province: OptionalProvinceSchema,
    latitude: z.coerce.number().min(-90).max(90).optional(),
    longitude: z.coerce.number().min(-180).max(180).optional(),
    radius: z.coerce.number().positive().max(500).default(50),
    limit: z.coerce.number().int().positive().max(50).default(20),
  })
  .superRefine((data, ctx) => {
    const hasLatitude = data.latitude !== undefined;
    const hasLongitude = data.longitude !== undefined;

    if (hasLatitude !== hasLongitude) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "latitude and longitude must be provided together",
        path: hasLatitude ? ["longitude"] : ["latitude"],
      });
    }
  });

export const ResourceAlertsQuerySchema = z.object({
  limit: z.coerce.number().int().positive().max(50).default(20),
});

export const ResourceAQHIQuerySchema = z.object({
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
});

export const ResourceSystemContextQuerySchema = z.object({
  province: ProvinceEnum,
  q: z.string().trim().min(1).max(200).optional(),
  limit: z.coerce.number().int().positive().max(20).default(8),
});
