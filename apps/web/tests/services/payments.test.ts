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

describe("Offers Service", () => {
  describe("createCheckoutSession", () => {
    it("sends POST to /offers/{planUuid}/checkout", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ session_url: "https://checkout.stripe.com/abc" }));
      vi.stubGlobal("fetch", mockFetch);

      const { createCheckoutSession } = await import("@services/payments/offers");
      const result = await createCheckoutSession("plan_uuid", 1, "http://localhost:3000/success", mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}offers/plan_uuid/checkout`);
      expect(opts.method).toBe("POST");
      const body = JSON.parse(opts.body);
      expect(body.org_id).toBe(1);
      expect(body.success_url).toBe("http://localhost:3000/success");
      expect(result.session_url).toBe("https://checkout.stripe.com/abc");
    });
  });
});

describe("Payments Service", () => {
  describe("getUserPaymentHistory", () => {
    it("sends GET to /payments/user", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse([{ id: "pi_abc", amount: 2999 }]));
      vi.stubGlobal("fetch", mockFetch);

      const { getUserPaymentHistory } = await import("@services/payments/payments");
      const result = await getUserPaymentHistory(mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}payments/user`);
      expect(opts.headers.get("Authorization")).toBe(`Bearer ${mockToken}`);
    });
  });

  describe("getCommunityPaymentHistory", () => {
    it("sends GET to /payments/community/{communityUuid}", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse([{ amount: 5000 }]));
      vi.stubGlobal("fetch", mockFetch);

      const { getCommunityPaymentHistory } = await import("@services/payments/payments");
      const result = await getCommunityPaymentHistory("comm_uuid", mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}payments/community/comm_uuid`);
    });
  });
});
