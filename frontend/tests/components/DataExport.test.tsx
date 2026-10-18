import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { DataExport } from "@/components/DataExport";

describe("DataExport", () => {
  // Store original window.location
  const originalLocation = window.location;
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;
  let downloadClick: ReturnType<typeof vi.spyOn>;

  function makeResponse({
    hasMore = false,
    link,
    count = 2,
    ok = true,
  }: { hasMore?: boolean; link?: string; count?: number; ok?: boolean } = {}) {
    const headerValues: Record<string, string> = {
      "x-export-has-more": String(hasMore),
      "x-export-record-count": String(count),
    };
    if (link) headerValues.link = link;

    return {
      ok,
      url: "",
      headers: {
        get(name: string) {
          return headerValues[name.toLowerCase()] ?? null;
        },
      },
      blob: vi.fn().mockResolvedValue(new Blob(["page data"])),
    } as unknown as Response;
  }

  beforeEach(() => {
    // Mock window.location.href
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...originalLocation,
        origin: originalLocation.origin,
        href: "",
      },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(makeResponse()));
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn().mockReturnValue("blob:http://localhost/export"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    downloadClick = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore original window.location
    Object.defineProperty(window, "location", {
      configurable: true,
      value: originalLocation,
    });
    downloadClick.mockRestore();
    vi.unstubAllGlobals();
    if (originalCreateObjectURL) {
      Object.defineProperty(URL, "createObjectURL", {
        configurable: true,
        value: originalCreateObjectURL,
      });
    } else {
      Reflect.deleteProperty(URL, "createObjectURL");
    }
    if (originalRevokeObjectURL) {
      Object.defineProperty(URL, "revokeObjectURL", {
        configurable: true,
        value: originalRevokeObjectURL,
      });
    } else {
      Reflect.deleteProperty(URL, "revokeObjectURL");
    }
  });

  it("renders with default state", () => {
    render(<DataExport />);

    expect(
      screen.getByRole("heading", { name: "Download Data" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Export wait time data with full methodology tags/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Download Data/i }),
    ).toBeInTheDocument();
  });

  it("displays citation information", () => {
    render(<DataExport />);

    expect(screen.getByText("Suggested Citation:")).toBeInTheDocument();
    expect(
      screen.getByText(/Wait Time Canada.*2026.*Canadian ER Wait Time Data/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/License: CC-BY-4.0/i)).toBeInTheDocument();
  });

  describe("province filter", () => {
    it('starts with "All Provinces" selected', () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Province") as HTMLSelectElement;
      expect(select.value).toBe("");
    });

    it("allows selecting specific province", () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Province") as HTMLSelectElement;
      fireEvent.change(select, { target: { value: "ON" } });

      expect(select.value).toBe("ON");
    });

    it("has Ontario, Quebec, and Alberta options", () => {
      render(<DataExport />);

      const options = screen.getAllByRole("option");
      const labels = options.map((opt) => opt.textContent);

      expect(labels).toContain("Ontario");
      expect(labels).toContain("Quebec");
      expect(labels).toContain("Alberta");
    });
  });

  describe("date range filter", () => {
    it('starts with "Last 7 Days" selected', () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Date Range") as HTMLSelectElement;
      expect(select.value).toBe("7d");
    });

    it("allows selecting different date ranges", () => {
      render(<DataExport />);

      const select = screen.getByLabelText("Date Range") as HTMLSelectElement;
      fireEvent.change(select, { target: { value: "30d" } });

      expect(select.value).toBe("30d");
    });

    it("has all date range options including extended ranges", () => {
      render(<DataExport />);

      const options = screen.getAllByRole("option");
      const labels = options.map((opt) => opt.textContent);

      expect(labels).toContain("Last 24 Hours");
      expect(labels).toContain("Last 7 Days");
      expect(labels).toContain("Last 30 Days");
      expect(labels).toContain("Last 90 Days");
      expect(labels).toContain("Last 6 Months");
      expect(labels).toContain("Last Year");
      expect(labels).toContain("All Data");
    });
  });

  describe("granularity selector", () => {
    it("renders the granularity selector", () => {
      render(<DataExport />);

      expect(screen.getByLabelText("Data Granularity")).toBeInTheDocument();
    });

    it("starts with raw granularity selected", () => {
      render(<DataExport />);

      const select = screen.getByLabelText(
        "Data Granularity",
      ) as HTMLSelectElement;
      expect(select.value).toBe("raw");
    });

    it("has all granularity options", () => {
      render(<DataExport />);

      const options = screen.getAllByRole("option");
      const labels = options.map((opt) => opt.textContent);

      expect(labels).toContain("Raw Measurements");
      expect(labels).toContain("Hourly Averages");
      expect(labels).toContain("Daily Averages");
      expect(labels).toContain("Weekly Averages");
      expect(labels).toContain("Monthly Averages");
    });

    it("shows raw data help text by default", () => {
      render(<DataExport />);

      expect(
        screen.getByText(/Raw data is available for the last 30 days/i),
      ).toBeInTheDocument();
    });

    it("shows aggregated help text when aggregate selected", () => {
      render(<DataExport />);

      const select = screen.getByLabelText(
        "Data Granularity",
      ) as HTMLSelectElement;
      fireEvent.change(select, { target: { value: "daily" } });

      expect(
        screen.getByText(/Aggregated data includes mean, median, P90/i),
      ).toBeInTheDocument();
    });

    it("granularity is passed as query parameter in download URL", () => {
      render(<DataExport />);

      const granularitySelect = screen.getByLabelText(
        "Data Granularity",
      ) as HTMLSelectElement;
      fireEvent.change(granularitySelect, { target: { value: "weekly" } });

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      expect(window.location.href).toContain("granularity=weekly");
    });
  });

  describe("raw data warning", () => {
    it("shows warning when raw data selected with >30 day range", () => {
      render(<DataExport />);

      const dateRangeSelect = screen.getByLabelText("Date Range");
      fireEvent.change(dateRangeSelect, { target: { value: "90d" } });

      expect(
        screen.getByText(/Raw measurements are retained for 30 days/i),
      ).toBeInTheDocument();
    });

    it("does not show warning for raw data within 30 days", () => {
      render(<DataExport />);

      // Default is 7d + raw, no warning
      expect(
        screen.queryByText(/Raw measurements are retained for 30 days/i),
      ).not.toBeInTheDocument();
    });

    it("does not show warning for aggregated data with long range", () => {
      render(<DataExport />);

      const granularitySelect = screen.getByLabelText("Data Granularity");
      fireEvent.change(granularitySelect, { target: { value: "daily" } });

      const dateRangeSelect = screen.getByLabelText("Date Range");
      fireEvent.change(dateRangeSelect, { target: { value: "90d" } });

      expect(
        screen.queryByText(/Raw measurements are retained for 30 days/i),
      ).not.toBeInTheDocument();
    });
  });

  describe("format toggle", () => {
    it("starts with CSV format selected", () => {
      render(<DataExport />);

      const csvButton = screen.getByRole("button", { name: /CSV/i });
      expect(csvButton).toHaveClass("bg-blue-100");
    });

    it("allows switching to JSON format", () => {
      render(<DataExport />);

      const jsonButton = screen.getByRole("button", { name: /JSON/i });
      fireEvent.click(jsonButton);

      expect(jsonButton).toHaveClass("bg-blue-100");
    });

    it("highlights only selected format", () => {
      render(<DataExport />);

      const csvButton = screen.getByRole("button", { name: /CSV/i });
      const jsonButton = screen.getByRole("button", { name: /JSON/i });

      // Initially CSV is selected
      expect(csvButton).toHaveClass("bg-blue-100");
      expect(jsonButton).not.toHaveClass("bg-blue-100");

      // Click JSON
      fireEvent.click(jsonButton);
      expect(jsonButton).toHaveClass("bg-blue-100");
      expect(csvButton).not.toHaveClass("bg-blue-100");
    });
  });

  describe("download functionality", () => {
    it("fetches the first raw page with correct URL for default options", async () => {
      render(<DataExport />);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
      const requestUrl = new URL(
        String(vi.mocked(fetch).mock.calls[0][0]),
        window.location.origin,
      );
      expect(requestUrl.pathname).toBe("/api/export");
      expect(requestUrl.searchParams.get("format")).toBe("csv");
      expect(requestUrl.searchParams.get("granularity")).toBe("raw");
      expect(requestUrl.searchParams.get("start_date")).toBeTruthy();
      expect(requestUrl.searchParams.get("page_size")).toBe("10000");
    });

    it("includes province parameter when selected", async () => {
      render(<DataExport />);

      const provinceSelect = screen.getByLabelText("Province");
      fireEvent.change(provinceSelect, { target: { value: "ON" } });

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
      const requestUrl = new URL(
        String(vi.mocked(fetch).mock.calls[0][0]),
        window.location.origin,
      );
      expect(requestUrl.searchParams.get("province")).toBe("ON");
    });

    it("uses JSON format when selected", async () => {
      render(<DataExport />);

      const jsonButton = screen.getByRole("button", { name: /JSON/i });
      fireEvent.click(jsonButton);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
      const requestUrl = new URL(
        String(vi.mocked(fetch).mock.calls[0][0]),
        window.location.origin,
      );
      expect(requestUrl.searchParams.get("format")).toBe("json");
    });

    it('does not include start_date for "All Data" range', async () => {
      render(<DataExport />);

      const dateRangeSelect = screen.getByLabelText("Date Range");
      fireEvent.change(dateRangeSelect, { target: { value: "all" } });

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
      const requestUrl = new URL(
        String(vi.mocked(fetch).mock.calls[0][0]),
        window.location.origin,
      );
      expect(requestUrl.searchParams.has("start_date")).toBe(false);
    });

    it("shows loading state while a raw page request is in flight", async () => {
      let resolveFetch!: (response: Response) => void;
      vi.mocked(fetch).mockReturnValueOnce(
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        }),
      );
      render(<DataExport />);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      fireEvent.click(downloadButton);

      expect(
        screen.getByRole("button", { name: /Downloading page/i }),
      ).toBeInTheDocument();
      expect(downloadButton).toBeDisabled();

      await act(async () => resolveFetch(makeResponse()));
      await waitFor(() => expect(downloadButton).not.toBeDisabled());

      expect(
        screen.getByRole("button", { name: /Download Data/i }),
      ).toBeInTheDocument();
    });

    it("downloads pages only after user clicks and allows retrying the same next page", async () => {
      const requests: string[] = [];
      const downloadedNames: string[] = [];
      downloadClick.mockImplementation(function (this: HTMLAnchorElement) {
        downloadedNames.push(this.download);
      });
      vi.mocked(fetch).mockImplementation(async (input) => {
        const requestUrl = new URL(String(input), window.location.origin);
        requests.push(requestUrl.href);
        const cursor = requestUrl.searchParams.get("cursor");
        if (!cursor) {
          const next = new URL(requestUrl);
          next.searchParams.set("cursor", "page-two-cursor");
          return makeResponse({
            hasMore: true,
            link: `<${next.pathname}${next.search}>; rel="next"`,
            count: 10000,
          });
        }
        if (
          requests.filter((url) => new URL(url).searchParams.has("cursor"))
            .length === 1
        ) {
          return makeResponse({ ok: false });
        }
        return makeResponse({ count: 23 });
      });

      render(<DataExport />);
      fireEvent.click(screen.getByRole("button", { name: /Download Data/i }));

      expect(await screen.findByRole("status")).toHaveTextContent(
        "Page 1 downloaded (10,000 rows). More data is available",
      );
      expect(
        screen.getByRole("button", { name: /Download next page \(2\)/i }),
      ).toBeInTheDocument();
      expect(fetch).toHaveBeenCalledTimes(1);

      fireEvent.click(
        screen.getByRole("button", { name: /Download next page \(2\)/i }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "Your current filters are unchanged; retry the export",
      );
      expect(
        screen.getByRole("button", { name: /Download next page \(2\)/i }),
      ).toBeInTheDocument();
      expect(fetch).toHaveBeenCalledTimes(2);

      fireEvent.click(
        screen.getByRole("button", { name: /Download next page \(2\)/i }),
      );
      expect(await screen.findByRole("status")).toHaveTextContent(
        "Page 2 downloaded (23 rows). No additional matching rows were reported",
      );
      expect(fetch).toHaveBeenCalledTimes(3);
      expect(downloadedNames).toEqual([
        expect.stringMatching(/page-001\.csv$/),
        expect.stringMatching(/page-002\.csv$/),
      ]);

      const cursorUrls = requests
        .map((url) => new URL(url))
        .filter((url) => url.searchParams.has("cursor"));
      expect(cursorUrls).toHaveLength(2);
      expect(cursorUrls[0].href).toBe(cursorUrls[1].href);
      expect(requests).toHaveLength(3);
    });

    it("resets pagination when filters change and keeps aggregates on the existing download path", async () => {
      vi.mocked(fetch).mockImplementationOnce(async (input) => {
        const requestUrl = new URL(String(input), window.location.origin);
        const next = new URL(requestUrl);
        next.searchParams.set("cursor", "page-two-cursor");
        return makeResponse({
          hasMore: true,
          link: `<${next.pathname}${next.search}>; rel="next"`,
        });
      });
      render(<DataExport />);
      fireEvent.click(screen.getByRole("button", { name: /Download Data/i }));
      expect(await screen.findByRole("status")).toHaveTextContent(
        "More data is available",
      );

      fireEvent.change(screen.getByLabelText("Province"), {
        target: { value: "ON" },
      });
      expect(
        screen.queryByRole("button", { name: /Download next page/i }),
      ).not.toBeInTheDocument();
      expect(screen.queryByRole("status")).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: /Download Data/i }));
      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
      const restartedUrl = new URL(
        String(vi.mocked(fetch).mock.calls[1][0]),
        window.location.origin,
      );
      expect(restartedUrl.searchParams.get("province")).toBe("ON");
      expect(restartedUrl.searchParams.has("cursor")).toBe(false);

      fireEvent.change(screen.getByLabelText("Data Granularity"), {
        target: { value: "daily" },
      });
      fireEvent.click(screen.getByRole("button", { name: /Download Data/i }));

      expect(window.location.href).toContain("granularity=daily");
      expect(fetch).toHaveBeenCalledTimes(2);
      expect(window.location.href).not.toContain("page_size=");
    });

    it("does not download a page when the server returns an unsafe next link", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        makeResponse({
          hasMore: true,
          link: "<https://example.invalid/api/export?cursor=external>; rel=next",
        }),
      );
      render(<DataExport />);
      fireEvent.click(screen.getByRole("button", { name: /Download Data/i }));

      expect(await screen.findByRole("alert")).toHaveTextContent(
        "could not be downloaded safely",
      );
      expect(downloadClick).not.toHaveBeenCalled();
      expect(
        screen.queryByRole("button", { name: /Download next page/i }),
      ).not.toBeInTheDocument();
    });

    it("uses JSON page filenames when JSON is selected", async () => {
      const downloadedNames: string[] = [];
      downloadClick.mockImplementation(function (this: HTMLAnchorElement) {
        downloadedNames.push(this.download);
      });
      render(<DataExport />);
      fireEvent.click(screen.getByRole("button", { name: /JSON/i }));
      fireEvent.click(screen.getByRole("button", { name: /Download Data/i }));

      expect(await screen.findByRole("status")).toHaveTextContent(
        "Page 1 downloaded",
      );
      expect(downloadedNames).toHaveLength(1);
      expect(downloadedNames[0]).toMatch(/page-001\.json$/);
    });
  });

  describe("accessibility", () => {
    it("has proper labels for form controls", () => {
      render(<DataExport />);

      expect(screen.getByLabelText("Province")).toBeInTheDocument();
      expect(screen.getByLabelText("Date Range")).toBeInTheDocument();
      expect(screen.getByLabelText("Data Granularity")).toBeInTheDocument();
    });

    it("download button is keyboard accessible", () => {
      render(<DataExport />);

      const downloadButton = screen.getByRole("button", {
        name: /Download Data/i,
      });
      expect(downloadButton).toBeEnabled();
      expect(downloadButton.tagName).toBe("BUTTON");
    });

    it("format toggle buttons are keyboard accessible", () => {
      render(<DataExport />);

      const csvButton = screen.getByRole("button", { name: /CSV/i });
      const jsonButton = screen.getByRole("button", { name: /JSON/i });

      expect(csvButton).toBeEnabled();
      expect(jsonButton).toBeEnabled();
    });
  });
});
