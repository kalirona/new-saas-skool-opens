import { vi } from "vitest";

export const mockSession = {
  user: {
    id: 1,
    username: "testuser",
    email: "test@learnhouse.com",
    first_name: "Test",
    last_name: "User",
    avatar_url: null,
  },
  expires: new Date(Date.now() + 86400000).toISOString(),
  accessToken: "mock-access-token",
  org: {
    id: 1,
    name: "Test Org",
    slug: "test-org",
  },
};

export function mockUseSession(overrides = {}) {
  return {
    data: { ...mockSession, ...overrides },
    status: "authenticated" as const,
    update: vi.fn(),
  };
}

export function createMockRouter(overrides = {}) {
  return {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
    query: {},
    asPath: "/",
    pathname: "/",
    ...overrides,
  };
}

export function createMatchMedia(matches = false) {
  return vi.fn((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

export function mockFetchResponse<T>(data: T, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers({ "content-type": "application/json" }),
  });
}

export function mockIntersectionObserver() {
  return vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));
}

export function mockResizeObserver() {
  return vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));
}
