import { describe, it, expect } from "vitest";
import {
  ProvinceSchema,
  TrendsQuerySchema,
  HospitalQuerySchema,
  CompareQuerySchema,
  GeolocationQuerySchema,
  HospitalTrendQuerySchema,
  BenchmarkQuerySchema,
  PatternsQuerySchema,
  ExportQuerySchema,
  DataQualityQuerySchema,
} from "./validations";

describe("Validation Schemas", () => {
  describe("ProvinceSchema", () => {
    it("accepts valid provinces", () => {
      expect(ProvinceSchema.safeParse("ON").success).toBe(true);
      expect(ProvinceSchema.safeParse("BC").success).toBe(true);
    });

    it("rejects invalid provinces", () => {
      expect(ProvinceSchema.safeParse("XX").success).toBe(false);
      expect(ProvinceSchema.safeParse("Ontario").success).toBe(false);
    });
  });

  describe("TrendsQuerySchema", () => {
    it("validates required province", () => {
      const result = TrendsQuerySchema.safeParse({ province: "ON" });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.province).toBe("ON");
        expect(result.data.period).toBe("monthly"); // default
        expect(result.data.lookback).toBe("6m"); // default
      }
    });

    it("validates optional parameters", () => {
      const result = TrendsQuerySchema.safeParse({
        province: "BC",
        period: "weekly",
        lookback: "1y",
      });
      expect(result.success).toBe(true);
    });

    it("rejects missing province", () => {
      const result = TrendsQuerySchema.safeParse({ period: "weekly" });
      expect(result.success).toBe(false);
    });

    it("rejects invalid period", () => {
      const result = TrendsQuerySchema.safeParse({
        province: "ON",
        period: "daily",
      });
      expect(result.success).toBe(false);
    });
  });

  describe("HospitalQuerySchema", () => {
    it("applies pagination defaults", () => {
      const result = HospitalQuerySchema.safeParse({});
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.page).toBe(1);
        expect(result.data.limit).toBe(20);
      }
    });

    it("validates pagination limits", () => {
      const result = HospitalQuerySchema.safeParse({ limit: 999 });
      expect(result.success).toBe(false);
    });
  });

  describe("CompareQuerySchema", () => {
    it("validates required hospital IDs", () => {
      const result = CompareQuerySchema.safeParse({ a: "hosp1", b: "hosp2" });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.a).toBe("hosp1");
        expect(result.data.b).toBe("hosp2");
      }
    });

    it("rejects missing IDs", () => {
      const result = CompareQuerySchema.safeParse({ a: "hosp1" });
      expect(result.success).toBe(false);
    });
  });

  describe("GeolocationQuerySchema", () => {
    it("validates coordinates", () => {
      expect(
        GeolocationQuerySchema.safeParse({ latitude: 45, longitude: -75 })
          .success,
      ).toBe(true);
    });

    it("coerces string coordinates", () => {
      const result = GeolocationQuerySchema.safeParse({
        latitude: "45.5",
        longitude: "-75.5",
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.latitude).toBe(45.5);
      }
    });

    it("rejects out of bounds coordinates", () => {
      expect(
        GeolocationQuerySchema.safeParse({ latitude: 91, longitude: 0 })
          .success,
      ).toBe(false);
    });
  });

  describe("HospitalTrendQuerySchema", () => {
    it("defaults to 24h", () => {
      const result = HospitalTrendQuerySchema.safeParse({});
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.period).toBe("24h");
      }
    });
  });

  describe("BenchmarkQuerySchema", () => {
    it("validates valid periods", () => {
      expect(
        BenchmarkQuerySchema.safeParse({ province: "ON", period: "7d" })
          .success,
      ).toBe(true);
    });

    it("rejects invalid periods", () => {
      expect(
        BenchmarkQuerySchema.safeParse({ province: "ON", period: "1y" })
          .success,
      ).toBe(false);
    });
  });

  describe("PatternsQuerySchema", () => {
    it("accepts valid types", () => {
      expect(
        PatternsQuerySchema.safeParse({ hospital_id: "1", type: "day_of_week" })
          .success,
      ).toBe(true);
    });
  });

  describe("ExportQuerySchema", () => {
    it("transforms boolean strings", () => {
      const result = ExportQuerySchema.safeParse({
        include_methodology: "false",
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.include_methodology).toBe(false);
      }
    });

    it("validates dates", () => {
      expect(
        ExportQuerySchema.safeParse({ start_date: "invalid" }).success,
      ).toBe(false);
      expect(
        ExportQuerySchema.safeParse({ start_date: "2023-01-01T00:00:00Z" })
          .success,
      ).toBe(true);
    });
  });

  describe("DataQualityQuerySchema", () => {
    it("accepts hospital shorthand without view", () => {
      const result = DataQualityQuerySchema.safeParse({
        hospital_id: "ca-on-test",
      });
      expect(result.success).toBe(true);
    });

    it("requires source_id for trend and diff views", () => {
      expect(DataQualityQuerySchema.safeParse({ view: "trend" }).success).toBe(
        false,
      );
      expect(DataQualityQuerySchema.safeParse({ view: "diff" }).success).toBe(
        false,
      );
    });

    it("requires hospital_id for hospital view", () => {
      expect(
        DataQualityQuerySchema.safeParse({ view: "hospital" }).success,
      ).toBe(false);
    });

    it("rejects source_id without a source-based view", () => {
      expect(
        DataQualityQuerySchema.safeParse({ source_id: "ontario-health" })
          .success,
      ).toBe(false);
    });

    it("rejects hospital_id and source_id together", () => {
      expect(
        DataQualityQuerySchema.safeParse({
          hospital_id: "ca-on-test",
          source_id: "ontario-health",
          view: "trend",
        }).success,
      ).toBe(false);
    });
  });
});
