export interface SimilarTicketSummary {
  ticket_id?: string;
  category: string;
  description: string;
  resolution: string;
  priority?: string;
  similarity_score: number;
}

export interface TicketFeedback {
  helpful: boolean | null;
  comment: string;
  submittedAt: string;
}

export interface Ticket {
  ticketId: string;
  category: string;
  description: string;
  resolution: string;
  sop: string;
  priority: "High" | "Medium" | "Low" | "Critical";
  status: "Open" | "Resolved" | "Closed";
  createdDate: string;
  resolvedDate?: string;
  // Filled in after the RAG service answers (stored for the History page)
  suggestedResolution?: string;
  confidence?: number;
  method?: string;
  similarTickets?: SimilarTicketSummary[];
  feedback?: TicketFeedback;
}
