import { describe, it, expect, vi, beforeEach } from "vitest";

const API_URL = "https://api.learnhouse.dev";

vi.mock("@services/config/config", () => ({
  getAPIUrl: () => API_URL,
}));

const mockToken = "mock_access_token";

function mockOkResponse(data: any) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Organizations Service", () => {
  describe("createNewOrganization", () => {
    it("sends POST to /orgs/ with auth header", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, name: "New Org" }));
      vi.stubGlobal("fetch", mockFetch);

      const { createNewOrganization } = await import("@services/organizations/orgs");
      const body = { name: "New Org", slug: "new-org" };
      const result = await createNewOrganization(body, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}orgs/`);
      expect(opts.method).toBe("POST");
      expect(opts.headers.get("Authorization")).toBe(`Bearer ${mockToken}`);
      expect(result).toEqual({ id: 1, name: "New Org" });
    });

    it("throws on error response", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: () => Promise.resolve({ detail: "Validation error" }),
      });
      vi.stubGlobal("fetch", mockFetch);

      const { createNewOrganization } = await import("@services/organizations/orgs");
      await expect(createNewOrganization({ name: "" }, mockToken)).rejects.toThrow();
    });
  });

  describe("getOrganizationContextInfo", () => {
    it("sends GET to /orgs/slug/{slug}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, slug: "test-org" }));
      vi.stubGlobal("fetch", mockFetch);

      const { getOrganizationContextInfo } = await import("@services/organizations/orgs");
      const result = await getOrganizationContextInfo("test-org", null, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}orgs/slug/test-org`);
      expect(opts.headers.get("Authorization")).toBe(`Bearer ${mockToken}`);
      expect(result.slug).toBe("test-org");
    });
  });

  describe("getOrganizationContextInfoWithUUID", () => {
    it("sends GET to /orgs/uuid/{uuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, org_uuid: "org_abc" }));
      vi.stubGlobal("fetch", mockFetch);

      const { getOrganizationContextInfoWithUUID } = await import("@services/organizations/orgs");
      const result = await getOrganizationContextInfoWithUUID("org_abc", null, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}orgs/uuid/org_abc`);
    });
  });

  describe("deleteOrganizationFromBackend", () => {
    it("sends DELETE to /orgs/{id}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ detail: "Deleted" }));
      vi.stubGlobal("fetch", mockFetch);

      const { deleteOrganizationFromBackend } = await import("@services/organizations/orgs");
      const result = await deleteOrganizationFromBackend(1, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}orgs/1`);
      expect(opts.method).toBe("DELETE");
    });
  });
});
