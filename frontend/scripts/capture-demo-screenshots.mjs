#!/usr/bin/env node

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const BASE_URL = process.env.BASE_URL ?? "http://127.0.0.1:3000";
const OUTPUT_DIR =
  process.env.SCREENSHOT_OUTPUT_DIR ??
  path.resolve(process.cwd(), ".artifacts", "demo-screenshots");

async function ensureOutputDir() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
}

async function captureDesktop(page, route, filename, readySelector) {
  await page.goto(`${BASE_URL}${route}`, {
    waitUntil: "domcontentloaded",
    timeout: 60_000,
  });
  if (readySelector) {
    await page.waitForSelector(readySelector, { timeout: 30_000 });
  }
  await page.waitForTimeout(800);
  await page.screenshot({
    path: path.join(OUTPUT_DIR, filename),
    fullPage: true,
  });
}

async function captureMobile(page, route, filename, readySelector) {
  await page.setViewportSize({ width: 390, height: 844 });
  await captureDesktop(page, route, filename, readySelector);
}

async function run() {
  await ensureOutputDir();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  await captureDesktop(page, "/", "01-landing-page.png", "h1");

  const expandAboutButton = page.getByRole("button", {
    name: /expand about section/i,
  });
  if (await expandAboutButton.count()) {
    await expandAboutButton.click();
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUTPUT_DIR, "02-landing-about-expanded.png"),
      fullPage: true,
    });
  }

  await captureDesktop(page, "/methods", "03-methods-page.png", "h1");
  await captureDesktop(page, "/analytics", "04-analytics-page.png", "h1");
  await captureDesktop(page, "/data-quality", "05-data-quality-page.png", "h1");
  await captureMobile(page, "/", "06-mobile-home.png", "h1");

  const manifest = {
    generated_at: new Date().toISOString(),
    base_url: BASE_URL,
    files: [
      "01-landing-page.png",
      "02-landing-about-expanded.png",
      "03-methods-page.png",
      "04-analytics-page.png",
      "05-data-quality-page.png",
      "06-mobile-home.png",
    ],
  };
  await fs.writeFile(
    path.join(OUTPUT_DIR, "manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    "utf-8",
  );

  await browser.close();
  // eslint-disable-next-line no-console
  console.log(`Demo screenshots saved to ${OUTPUT_DIR}`);
}

run().catch((error) => {
  // eslint-disable-next-line no-console
  console.error("Failed to capture screenshots:", error);
  process.exit(1);
});
