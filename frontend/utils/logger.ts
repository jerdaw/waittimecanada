/**
 * Structured logger for frontend API routes (Next.js server-side).
 * Outputs JSON logs for production observability.
 */
export const logger = {
  info: (message: string, meta?: Record<string, any>) => {
    console.log(
      JSON.stringify({
        level: "info",
        timestamp: new Date().toISOString(),
        message,
        ...meta,
      }),
    );
  },
  error: (message: string, error?: any, meta?: Record<string, any>) => {
    console.error(
      JSON.stringify({
        level: "error",
        timestamp: new Date().toISOString(),
        message,
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        ...meta,
      }),
    );
  },
  warn: (message: string, meta?: Record<string, any>) => {
    console.warn(
      JSON.stringify({
        level: "warn",
        timestamp: new Date().toISOString(),
        message,
        ...meta,
      }),
    );
  },
};
