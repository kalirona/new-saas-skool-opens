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

describe("AI Service", () => {
  describe("generateCourseOutline", () => {
    it("sends POST to /ai/generate-outline", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ outline: ["Module 1", "Module 2"] }));
      vi.stubGlobal("fetch", mockFetch);

      const { generateCourseOutline } = await import("@services/ai/ai");
      const result = await generateCourseOutline({ topic: "Python Basics", level: "beginner" }, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}ai/generate-outline`);
      expect(opts.method).toBe("POST");
      expect(JSON.parse(opts.body).topic).toBe("Python Basics");
      expect(result.outline).toHaveLength(2);
    });
  });

  describe("generateCourseContent", () => {
    it("sends POST to /ai/generate-content", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ content: "# Lesson 1" }));
      vi.stubGlobal("fetch", mockFetch);

      const { generateCourseContent } = await import("@services/ai/ai");
      const result = await generateCourseContent({ outline: "Module 1", format: "markdown" }, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}ai/generate-content`);
    });
  });
});

describe("AI Course Planning Service", () => {
  describe("generateCurriculum", () => {
    it("sends POST to /ai/courseplanning/curriculum", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ curriculum: [{ week: 1, topic: "Intro" }] }));
      vi.stubGlobal("fetch", mockFetch);

      const { generateCurriculum } = await import("@services/ai/courseplanning");
      const result = await generateCurriculum({ course_name: "Python 101", duration_weeks: 4 }, mockToken);

      const [url, opts] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}ai/courseplanning/curriculum`);
      expect(JSON.parse(opts.body).course_name).toBe("Python 101");
      expect(result.curriculum).toHaveLength(1);
    });
  });

  describe("generateLessonPlan", () => {
    it("sends POST to /ai/courseplanning/lesson-plan", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ objectives: ["Learn X"], activities: ["Quiz"] }));
      vi.stubGlobal("fetch", mockFetch);

      const { generateLessonPlan } = await import("@services/ai/courseplanning");
      const result = await generateLessonPlan({ topic: "Variables", duration_minutes: 60 }, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}ai/courseplanning/lesson-plan`);
      expect(result.objectives).toContain("Learn X");
    });
  });

  describe("generateAssessment", () => {
    it("sends POST to /ai/courseplanning/assessment", async () => {
      const mockFetch = vi.fn().mockResolvedValue(mockOkResponse({ questions: [{ q: "What is X?", answer: "Y" }] }));
      vi.stubGlobal("fetch", mockFetch);

      const { generateAssessment } = await import("@services/ai/courseplanning");
      const result = await generateAssessment({ topic: "Functions", num_questions: 5 }, mockToken);

      const [url] = mockFetch.mock.calls[0];
      expect(url).toBe(`${API_URL}ai/courseplanning/assessment`);
      expect(result.questions).toHaveLength(1);
    });
  });
});
