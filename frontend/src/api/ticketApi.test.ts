import { describe, it, expect, beforeEach } from "vitest";
import {
  uploadTicket,
  getTicket,
  getAllTickets,
  saveTicket,
  clearTickets,
} from "./ticketApi";

function form(fields: Record<string, string>): FormData {
  const data = new FormData();
  Object.entries(fields).forEach(([k, v]) => data.append(k, v));
  return data;
}

describe("ticketApi (localStorage history)", () => {
  beforeEach(async () => {
    localStorage.clear();
    await clearTickets();
  });

  describe("uploadTicket", () => {
    it("creates an open ticket with the submitted values", async () => {
      const result = await uploadTicket(
        form({ description: "VPN drops", category: "VPN Access", priority: "High" })
      );
      expect(result.ticketId).toMatch(/^T\d+$/);
      expect(result.category).toBe("VPN Access");
      expect(result.description).toBe("VPN drops");
      expect(result.priority).toBe("High");
      expect(result.status).toBe("Open");
      expect(result.resolution).toBe("");
      expect(result.sop).toBe("");
    });

    it("uses defaults for missing or invalid values", async () => {
      const result = await uploadTicket(form({ priority: "Urgent!!" }));
      expect(result.category).toBe("General");
      expect(result.description).toBe("No description provided");
      expect(result.priority).toBe("Medium");
    });

    it("sets createdDate to now", async () => {
      const before = Date.now();
      const result = await uploadTicket(form({ description: "Test" }));
      const created = new Date(result.createdDate).getTime();
      expect(created).toBeGreaterThanOrEqual(before - 1000);
      expect(created).toBeLessThanOrEqual(Date.now() + 1000);
    });

    it("stores the ticket so it appears in history", async () => {
      const result = await uploadTicket(form({ description: "Stored" }));
      const all = await getAllTickets();
      expect(all.map((t) => t.ticketId)).toContain(result.ticketId);
    });
  });

  describe("getTicket / saveTicket", () => {
    it("returns null for an unknown id", async () => {
      expect(await getTicket("T0")).toBeNull();
    });

    it("saves the suggested resolution on an existing ticket", async () => {
      const ticket = await uploadTicket(form({ description: "Printer offline" }));
      await saveTicket({ ...ticket, suggestedResolution: "Restart spooler", confidence: 0.8 });
      const loaded = await getTicket(ticket.ticketId);
      expect(loaded?.suggestedResolution).toBe("Restart spooler");
      expect(loaded?.confidence).toBe(0.8);
      expect(await getAllTickets()).toHaveLength(1);
    });
  });

  describe("getAllTickets", () => {
    it("returns an empty array when nothing is stored", async () => {
      expect(await getAllTickets()).toEqual([]);
    });

    it("returns newest tickets first", async () => {
      await saveTicket({
        ticketId: "T1", category: "A", description: "old", resolution: "", sop: "",
        priority: "Low", status: "Open", createdDate: "2026-01-01T00:00:00Z",
      });
      await saveTicket({
        ticketId: "T2", category: "A", description: "new", resolution: "", sop: "",
        priority: "Low", status: "Open", createdDate: "2026-02-01T00:00:00Z",
      });
      expect((await getAllTickets()).map((t) => t.ticketId)).toEqual(["T2", "T1"]);
    });

    it("ignores corrupted storage", async () => {
      localStorage.setItem("ticketgenie.tickets", "{not json");
      expect(await getAllTickets()).toEqual([]);
    });
  });
});
