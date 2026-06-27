// Define the Logger interface to ensure consistent usage
export interface Logger {
  info: (message: string, meta?: Record<string, any>) => void;
  error: (message: string, error?: any, meta?: Record<string, any>) => void;
  warn: (message: string, meta?: Record<string, any>) => void;
}

// Check for Edge Runtime (which doesn't support pino fully)
const isEdgeRuntime = process.env.NEXT_RUNTIME === "edge";
// Check for Browser environment
const isBrowser = typeof window !== "undefined";

/**
 * Console-based logger for Edge/Browser environments where Pino might fail.
 * Outputs JSON format similar to Pino for consistency.
 */
const consoleLogger: Logger = {
  info: (message: string, meta?: Record<string, any>) => {
    console.log(
      JSON.stringify({
        level: "info",
        target: "console",
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
        target: "console",
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
        target: "console",
        timestamp: new Date().toISOString(),
        message,
        ...meta,
      }),
    );
  },
};

/**
 * Pino logger for Node.js environments (Server Components, API Routes).
 * Lazy-loaded to avoid import errors in Edge/Browser.
 */
let pinoLogger: any = null;

if (!isEdgeRuntime && !isBrowser) {
  try {
    // Dynamic import might be tricky with Next.js bundling, so we use require
    const pino = require("pino");

    // Configure pino
    pinoLogger = pino({
      level: process.env.LOG_LEVEL || "info",
      timestamp: pino.stdTimeFunctions.isoTime,
      formatters: {
        level: (label: string) => {
          return { level: label };
        },
      },
      // In development, we can pipe to pino-pretty via CLI or transport
      // But usually just JSON in production
    });
  } catch (e) {
    console.warn(
      "Failed to initialize pino, falling back to console logger",
      e,
    );
  }
}

/**
 * Wrapper that delegates to the appropriate logger implementation.
 */
export const logger: Logger = {
  info: (message: string, meta?: Record<string, any>) => {
    if (pinoLogger) {
      pinoLogger.info(meta || {}, message);
    } else {
      consoleLogger.info(message, meta);
    }
  },
  error: (message: string, error?: any, meta?: Record<string, any>) => {
    if (pinoLogger) {
      let errorObj: any = { err: error };
      if (error instanceof Error) {
        // reconstruct to avoid TS issues with spread
        const { message, stack, ...rest } = error as any;
        errorObj = { err: { message, stack, ...rest } };
      }
      // Cast to any to avoid TS gripes about message property conflict
      pinoLogger.error({ ...errorObj, ...(meta || {}) } as any, message);
    } else {
      consoleLogger.error(message, error, meta);
    }
  },
  warn: (message: string, meta?: Record<string, any>) => {
    if (pinoLogger) {
      pinoLogger.warn(meta || {}, message);
    } else {
      consoleLogger.warn(message, meta);
    }
  },
};
