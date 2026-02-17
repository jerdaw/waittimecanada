import "@testing-library/jest-dom";
import { vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock next-intl
vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => key,
  useLocale: () => 'en',
  useTimeZone: () => 'America/Toronto',
}));

// Mock Next.js router
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
  useParams: () => ({}),
}));

// Mock Mapbox GL (doesn't work in jsdom)
const mockMap = {
  on: vi.fn(),
  off: vi.fn(),
  remove: vi.fn(),
  addControl: vi.fn(),
  removeControl: vi.fn(),
  addSource: vi.fn(),
  removeSource: vi.fn(),
  addLayer: vi.fn(),
  removeLayer: vi.fn(),
  setStyle: vi.fn(),
  setCenter: vi.fn(),
  setZoom: vi.fn(),
  flyTo: vi.fn(),
  easeTo: vi.fn(),
  jumpTo: vi.fn(),
  resize: vi.fn(),
  getCanvas: vi.fn(() => ({
    style: { cursor: "" },
  })),
};

const mockMarker = {
  setLngLat: vi.fn().mockReturnThis(),
  addTo: vi.fn().mockReturnThis(),
  remove: vi.fn().mockReturnThis(),
  setPopup: vi.fn().mockReturnThis(),
  getElement: vi.fn(() => document.createElement("div")),
};

const mockPopup = {
  setLngLat: vi.fn().mockReturnThis(),
  setHTML: vi.fn().mockReturnThis(),
  setDOMContent: vi.fn().mockReturnThis(),
  addTo: vi.fn().mockReturnThis(),
  remove: vi.fn().mockReturnThis(),
  isOpen: vi.fn(() => false),
  on: vi.fn().mockReturnThis(),
};

vi.mock("mapbox-gl", () => ({
  default: {
    Map: vi.fn(() => mockMap),
    Marker: vi.fn(() => mockMarker),
    Popup: vi.fn(() => mockPopup),
    NavigationControl: vi.fn(() => ({
      onAdd: vi.fn(),
      onRemove: vi.fn(),
    })),
  },
}));

// Mock react-map-gl
vi.mock("react-map-gl", () => ({
  __esModule: true,
  default: vi.fn(({ children }) => children),
  Marker: vi.fn(({ children }) => children),
  Popup: vi.fn(({ children }) => children),
  NavigationControl: vi.fn(() => null),
}));

// Mock fetch globally
global.fetch = vi.fn();

// Mock environment variables
process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.test.mock-token";
process.env.DATABASE_URL = "postgresql://test:test@localhost:5432/test"; // pragma: allowlist secret

// Suppress console errors in tests (optional)
// global.console = {
//   ...console,
//   error: vi.fn(),
// };
