import { describe, it, expect, vi, beforeEach } from "vitest";

const API_URL = "https://api.learnhouse.dev";

vi.mock("@services/config/config", () => ({
  getAPIUrl: () => API_URL,
}));

const mockToken = "mock_token";

function mockOkResponse(data: any) {
  return { ok: true, status: 200, json: () => Promise.resolve(data) };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Events Service", () => {
  describe("createEvent", () => {
    it("sends POST to /events/ with org_id", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, title: "Webinar" }));
      vi.stubGlobal("fetch", mockFetch);

      const { createEvent } = await import("@services/events/events");
      const data = { title: "Webinar", start_date: "2026-07-10T14:00:00Z", type: "live" };
      const result = await createEvent(1, data, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}events/?org_id=1`);
      expect(opts.method).toBe("POST");
      const body = JSON.parse(opts.body);
      expect(body.title).toBe("Webinar");
      expect(body.type).toBe("live");
      expect(result.title).toBe("Webinar");
    });
  });

  describe("updateEvent", () => {
    it("sends PUT to /events/{eventUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, title: "Webinar Updated" }));
      vi.stubGlobal("fetch", mockFetch);

      const { updateEvent } = await import("@services/events/events");
      const result = await updateEvent("evt_uuid", { title: "Webinar Updated" }, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}events/evt_uuid`);
      expect(opts.method).toBe("PUT");
    });
  });

  describe("deleteEvent", () => {
    it("sends DELETE to /events/{eventUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({}));
      vi.stubGlobal("fetch", mockFetch);

      const { deleteEvent } = await import("@services/events/events");
      await deleteEvent("evt_uuid", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}events/evt_uuid`);
      expect(opts.method).toBe("DELETE");
    });
  });

  describe("registerForEvent", () => {
    it("sends POST to /events/{eventUuid}/register", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ status: "registered" }));
      vi.stubGlobal("fetch", mockFetch);

      const { registerForEvent } = await import("@services/events/events");
      const result = await registerForEvent("evt_uuid", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}events/evt_uuid/register`);
      expect(opts.method).toBe("POST");
      expect(result.status).toBe("registered");
    });
  });

  describe("cancelRegistration", () => {
    it("sends DELETE to /events/{eventUuid}/register", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({}));
      vi.stubGlobal("fetch", mockFetch);

      const { cancelRegistration } = await import("@services/events/events");
      await cancelRegistration("evt_uuid", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}events/evt_uuid/register`);
      expect(opts.method).toBe("DELETE");
    });
  });

  describe("getEventAttendees", () => {
    it("sends GET to /events/{eventUuid}/attendees", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse([{ user: { email: "a@b.com" } }]));
      vi.stubGlobal("fetch", mockFetch);

      const { getEventAttendees } = await import("@services/events/events");
      const result = await getEventAttendees("evt_uuid", mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}events/evt_uuid/attendees`);
      expect(result).toHaveLength(1);
    });
  });
});

describe("Resources Service", () => {
  describe("uploadResource", () => {
    it("sends POST to /resources/ with form data", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, filename: "doc.pdf" }));
      vi.stubGlobal("fetch", mockFetch);

      const { uploadResource } = await import("@services/resources/resources");
      const file = new File(["content"], "doc.pdf", { type: "application/pdf" });
      const formData = new FormData();
      formData.append("file", file);
      const result = await uploadResource("space_uuid", formData, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toContain("resources");
      expect(opts.method).toBe("POST");
      expect(opts.headers.get("Authorization")).toBe(`Bearer ${mockToken}`);
      expect(result.filename).toBe("doc.pdf");
    });
  });

  describe("deleteResource", () => {
    it("sends DELETE to /resources/{resourceUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({}));
      vi.stubGlobal("fetch", mockFetch);

      const { deleteResource } = await import("@services/resources/resources");
      await deleteResource("res_uuid", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}resources/res_uuid`);
      expect(opts.method).toBe("DELETE");
    });
  });
});
