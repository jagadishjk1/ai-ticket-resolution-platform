import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import { submitFeedback } from "./feedbackApi";
vi.mock("axios");
describe("feedbackApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  describe("submitFeedback", () => {
    it("should submit feedback successfully", async () => {
      const mockResponse = { status: "success" };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockResponse });
      const result = await submitFeedback("T123", "Great resolution!");
      expect(result).toEqual(mockResponse);
      expect(axios.post).toHaveBeenCalledWith(
        "http://localhost:8000/api/feedback/T123",
        {
          feedback: "Great resolution!",
        },
        expect.any(Object)
      );
    });
    it("should handle different ticket IDs", async () => {
      const mockResponse = { status: "success" };
      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });
      await submitFeedback("T999888", "Feedback text");
      expect(axios.post).toHaveBeenCalledWith(
        "http://localhost:8000/api/feedback/T999888",
        {
          feedback: "Feedback text",
        },
        expect.any(Object)
      );
    });
    it("should handle long feedback text", async () => {
      const mockResponse = { status: "success" };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockResponse });
      const longFeedback = "A".repeat(1000);
      await submitFeedback("T123", longFeedback);
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ feedback: longFeedback }),
        expect.any(Object)
      );
    });
    it("should handle empty feedback", async () => {
      const mockResponse = { status: "success" };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockResponse });
      await submitFeedback("T123", "");
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ feedback: "" }),
        expect.any(Object)
      );
    });
    it("should handle feedback with special characters", async () => {
      const mockResponse = { status: "success" };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockResponse });
      const specialFeedback = "Great! 👍 Works @100%";
      await submitFeedback("T123", specialFeedback);
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ feedback: specialFeedback }),
        expect.any(Object)
      );
    });
    it("should send the helpful rating when given", async () => {
      vi.mocked(axios.post).mockResolvedValueOnce({ data: { status: "success" } });
      await submitFeedback("T123", "Worked", true);
      expect(axios.post).toHaveBeenCalledWith(
        "http://localhost:8000/api/feedback/T123",
        { feedback: "Worked", helpful: true },
        expect.any(Object)
      );
    });
    it("should handle network errors", async () => {
      vi.mocked(axios.post).mockRejectedValueOnce(new Error("Network error"));
      await expect(submitFeedback("T123", "feedback")).rejects.toThrow(
        "Network error"
      );
    });
    it("should handle server errors", async () => {
      const errorResponse = {
        response: { status: 500, data: { message: "Server error" } },
      };
      vi.mocked(axios.post).mockRejectedValueOnce(errorResponse);
      await expect(submitFeedback("T123", "feedback")).rejects.toEqual(
        errorResponse
      );
    });
    it("should handle 404 errors for non-existent tickets", async () => {
      const errorResponse = {
        response: { status: 404, data: { message: "Ticket not found" } },
      };
      vi.mocked(axios.post).mockRejectedValueOnce(errorResponse);
      await expect(submitFeedback("T999999", "feedback")).rejects.toEqual(
        errorResponse
      );
    });
  });
});
