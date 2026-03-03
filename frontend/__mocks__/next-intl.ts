import { vi } from "vitest";
import React from "react";

const t = (key: string) => key;
t.rich = (key: string, chunks?: any) => key;
t.raw = (key: string) => key;

export const useTranslations = vi.fn(() => t);
export const useLocale = vi.fn(() => "en");
export const useTimeZone = vi.fn(() => "America/Toronto");
export const NextIntlClientProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => children;
