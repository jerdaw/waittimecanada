import postgres from "postgres";

let sql: ReturnType<typeof postgres> | null = null;

type DatabaseSslOption = false | "require";

const LOCAL_DATABASE_HOSTS = new Set([
  "localhost",
  "127.0.0.1",
  "::1",
  "[::1]",
]);

export function getDatabaseSslOption(
  databaseUrl: string,
  sslMode = process.env.DATABASE_SSL_MODE,
): DatabaseSslOption {
  const normalizedSslMode = sslMode?.toLowerCase();
  if (normalizedSslMode === "require") {
    return "require";
  }
  if (
    normalizedSslMode === "disable" ||
    normalizedSslMode === "false" ||
    normalizedSslMode === "off" ||
    normalizedSslMode === "0"
  ) {
    return false;
  }

  try {
    const hostname = new URL(databaseUrl).hostname.toLowerCase();
    return LOCAL_DATABASE_HOSTS.has(hostname) ? false : "require";
  } catch {
    return "require";
  }
}

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
      ssl: getDatabaseSslOption(databaseUrl),
    });
  }

  return sql;
}
