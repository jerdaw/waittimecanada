import postgres from "postgres";

let sql: ReturnType<typeof postgres> | null = null;

/**
 * Get database connection (lazy initialization)
 * This prevents database connection attempts during Next.js build time
 */
export function getDb() {
  if (!sql) {
    const databaseUrl = process.env.DATABASE_URL;

    if (!databaseUrl) {
      throw new Error("DATABASE_URL environment variable is not set");
    }

    sql = postgres(databaseUrl, {
      ssl: "require",
    });
  }

  return sql;
}
