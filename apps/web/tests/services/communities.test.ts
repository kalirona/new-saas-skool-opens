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

describe("Communities Service", () => {
  describe("createCommunity", () => {
    it("sends POST to /communities/ with org_id", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, name: "Test Community" }));
      vi.stubGlobal("fetch", mockFetch);

      const { createCommunity } = await import("@services/communities/communities");
      const data = { name: "Test Community", description: "A test" };
      const result = await createCommunity(1, data, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/?org_id=1`);
      expect(opts.method).toBe("POST");
      expect(JSON.parse(opts.body).name).toBe("Test Community");
      expect(opts.headers.get("Authorization")).toBe(`Bearer ${mockToken}`);
      expect(result.name).toBe("Test Community");
    });
  });

  describe("updateCommunity", () => {
    it("sends PUT to /communities/{uuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, name: "Updated" }));
      vi.stubGlobal("fetch", mockFetch);

      const { updateCommunity } = await import("@services/communities/communities");
      const result = await updateCommunity("comm_uuid_abc", { name: "Updated", description: "new desc" }, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/comm_uuid_abc`);
      expect(opts.method).toBe("PUT");
      expect(result.name).toBe("Updated");
    });
  });

  describe("getCommunities", () => {
    it("sends GET to /communities/org/{orgId}/page/{page}/limit/{limit}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse([{ id: 1, name: "C1" }]));
      vi.stubGlobal("fetch", mockFetch);

      const { getCommunities } = await import("@services/communities/communities");
      const result = await getCommunities(1, 1, 20, null, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/org/1/page/1/limit/20`);
    });
  });
});

describe("Spaces Service", () => {
  describe("createSpace", () => {
    it("sends POST to /communities/{communityUuid}/spaces", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, name: "Test Space" }));
      vi.stubGlobal("fetch", mockFetch);

      const { createSpace } = await import("@services/communities/spaces");
      const data = { name: "Test Space", visibility: "members" };
      const result = await createSpace("comm_uuid", data, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/comm_uuid/spaces`);
      expect(opts.method).toBe("POST");
      expect(JSON.parse(opts.body).name).toBe("Test Space");
      expect(JSON.parse(opts.body).visibility).toBe("members");
      expect(result.name).toBe("Test Space");
    });
  });

  describe("getSpaces", () => {
    it("sends GET to /communities/{communityUuid}/spaces", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse([{ id: 1, name: "S1" }]));
      vi.stubGlobal("fetch", mockFetch);

      const { getSpaces } = await import("@services/communities/spaces");
      const result = await getSpaces("comm_uuid", mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/comm_uuid/spaces`);
    });
  });

  describe("deleteSpace", () => {
    it("sends DELETE to /spaces/{spaceUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ detail: "Deleted" }));
      vi.stubGlobal("fetch", mockFetch);

      const { deleteSpace } = await import("@services/communities/spaces");
      await deleteSpace("space_uuid", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}spaces/space_uuid`);
      expect(opts.method).toBe("DELETE");
    });
  });
});

describe("Membership Service", () => {
  describe("createMembershipPlan", () => {
    it("sends POST to /communities/{uuid}/plans", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ id: 1, name: "Pro Plan", price: 29.99 }));
      vi.stubGlobal("fetch", mockFetch);

      const { createMembershipPlan } = await import("@services/communities/membership");
      const data = { name: "Pro Plan", price: 29.99, interval: "monthly" };
      const result = await createMembershipPlan("comm_uuid", data, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/comm_uuid/plans`);
      expect(opts.method).toBe("POST");
      expect(JSON.parse(opts.body).price).toBe(29.99);
      expect(result.price).toBe(29.99);
    });
  });

  describe("updateMembershipPlan", () => {
    it("sends PUT to /plans/{planUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ name: "Updated Plan", price: 49.99 }));
      vi.stubGlobal("fetch", mockFetch);

      const { updateMembershipPlan } = await import("@services/communities/membership");
      const result = await updateMembershipPlan("plan_uuid", { price: 49.99 }, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}plans/plan_uuid`);
      expect(opts.method).toBe("PUT");
    });
  });

  describe("deleteMembershipPlan", () => {
    it("sends DELETE to /plans/{planUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({}));
      vi.stubGlobal("fetch", mockFetch);

      const { deleteMembershipPlan } = await import("@services/communities/membership");
      await deleteMembershipPlan("plan_uuid", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}plans/plan_uuid`);
      expect(opts.method).toBe("DELETE");
    });
  });

  describe("getAllMembershipPlansAdmin", () => {
    it("sends GET to /communities/{uuid}/plans/admin", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse([{ name: "Free", price: 0 }]));
      vi.stubGlobal("fetch", mockFetch);

      const { getAllMembershipPlansAdmin } = await import("@services/communities/membership");
      const result = await getAllMembershipPlansAdmin("comm_uuid", mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}communities/comm_uuid/plans/admin`);
    });
  });
});
