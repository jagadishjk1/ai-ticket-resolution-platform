import { type Ticket } from "../types/ticketTypes";

/**
 * Ticket storage.
 *
 * The RAG service only suggests resolutions; it does not store tickets.
 * Submitted tickets are therefore kept in the browser's localStorage so the
 * History and Ticket Detail pages can show them during a demo.
 */
const STORAGE_KEY = "ticketgenie.tickets";
const PRIORITIES: Ticket["priority"][] = ["Low", "Medium", "High", "Critical"];

function readAll(): Ticket[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? (parsed as Ticket[]) : [];
  } catch {
    return [];
  }
}

function writeAll(tickets: Ticket[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tickets));
  } catch {
    // Storage full or unavailable (e.g. private mode) - history is optional.
  }
}

export async function uploadTicket(data: FormData): Promise<Ticket> {
  const description = ((data.get("description") as string) || "").trim();
  const category = ((data.get("category") as string) || "").trim();
  const priority = data.get("priority") as Ticket["priority"];

  const ticket: Ticket = {
    ticketId: `T${Date.now()}`,
    category: category || "General",
    description: description || "No description provided",
    resolution: "",
    sop: "",
    priority: PRIORITIES.includes(priority) ? priority : "Medium",
    status: "Open",
    createdDate: new Date().toISOString(),
  };
  writeAll([ticket, ...readAll()]);
  return ticket;
}

/** Save changes to a stored ticket (e.g. the suggested resolution or feedback). */
export async function saveTicket(ticket: Ticket): Promise<Ticket> {
  const tickets = readAll();
  const index = tickets.findIndex((t) => t.ticketId === ticket.ticketId);
  if (index >= 0) {
    tickets[index] = ticket;
  } else {
    tickets.unshift(ticket);
  }
  writeAll(tickets);
  return ticket;
}

export async function getTicket(id: string): Promise<Ticket | null> {
  return readAll().find((t) => t.ticketId === id) ?? null;
}

/** All stored tickets, newest first. */
export async function getAllTickets(): Promise<Ticket[]> {
  return readAll().sort(
    (a, b) =>
      new Date(b.createdDate).getTime() - new Date(a.createdDate).getTime()
  );
}

export async function clearTickets(): Promise<void> {
  writeAll([]);
}
