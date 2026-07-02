import { describe, it, expect, vi, beforeEach } from "vitest";
import { mockFetchResponse } from "../utils/mocks";

const API_URL = "https://api.learnhouse.dev";

vi.mock("@services/config/config", () => ({
  getAPIUrl: () => API_URL,
}));

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Auth Service - loginAndGetToken", () => {
  it("sends POST to auth/login with form data", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse({ access_token: "tok_abc" }));
    vi.stubGlobal("fetch", mockFetch);

    const { loginAndGetToken } = await import("@services/auth/auth");
    const res = await loginAndGetToken("admin@test.com", "password123");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe(`${API_URL}auth/login`);
    expect(opts.method).toBe("POST");
    expect(opts.body.get("username")).toBe("admin@test.com");
    expect(opts.body.get("password")).toBe("password123");
    expect(opts.credentials).toBe("include");
  });

  it("propagates fetch errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));
    const { loginAndGetToken } = await import("@services/auth/auth");
    await expect(loginAndGetToken("u", "p")).rejects.toThrow("Network error");
  });
});

describe("Auth Service - loginWithOAuthToken", () => {
  it("sends POST to auth/oauth with JSON body", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse({ access_token: "tok_abc" }));
    vi.stubGlobal("fetch", mockFetch);

    const { loginWithOAuthToken } = await import("@services/auth/auth");
    const res = await loginWithOAuthToken("user@test.com", "google", "google_at_123", 1);

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe(`${API_URL}auth/oauth?org_id=1`);
    const body = JSON.parse(opts.body);
    expect(body.email).toBe("user@test.com");
    expect(body.provider).toBe("google");
    expect(body.access_token).toBe("google_at_123");
  });

  it("works without orgId", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse({}));
    vi.stubGlobal("fetch", mockFetch);

    const { loginWithOAuthToken } = await import("@services/auth/auth");
    await loginWithOAuthToken("user@test.com", "google", "tok");

    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe(`${API_URL}auth/oauth`);
  });
});

describe("Auth Service - logout", () => {
  it("sends DELETE to auth/logout", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse({}));
    vi.stubGlobal("fetch", mockFetch);

    const { logout } = await import("@services/auth/auth");
    await logout();

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe(`${API_URL}auth/logout`);
    expect(opts.method).toBe("DELETE");
  });
});

describe("Auth Service - sendResetLink", () => {
  it("sends POST to reset password endpoint", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse({ status: 200 }));
    vi.stubGlobal("fetch", mockFetch);

    const { sendResetLink } = await import("@services/auth/auth");
    await sendResetLink("user@test.com", 1);

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("reset_password/send_reset_code");
    expect(url).toContain("org_id=1");
  });
});

describe("Auth Service - resetPassword", () => {
  it("sends POST with new password and reset code", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse({ status: 200 }));
    vi.stubGlobal("fetch", mockFetch);

    const { resetPassword } = await import("@services/auth/auth");
    await resetPassword("user@test.com", "newPass123", 1, "reset_code_abc");

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain("reset_password/change_password/user@test.com");
    const body = JSON.parse(opts.body);
    expect(body.new_password).toBe("newPass123");
    expect(body.reset_code).toBe("reset_code_abc");
  });
});
