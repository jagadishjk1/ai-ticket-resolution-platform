import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getTicket, saveTicket } from "../api/ticketApi";
import { submitFeedback } from "../api/feedbackApi";
import ResolutionResult from "../components/ResolutionSuggestion/ResolutionResult";
import ResolutionFeedback from "../components/Feedback/ResolutionFeedback";
import type { Ticket } from "../types/ticketTypes";
import "./HistoryPage.css";

/** Full view of one submitted ticket, its suggested resolution, and feedback. */
const TicketDetailPage: React.FC = () => {
  const { id = "" } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("");

  useEffect(() => {
    getTicket(id)
      .then(setTicket)
      .finally(() => setLoading(false));
  }, [id]);

  async function sendFeedback(helpful: boolean | null, comment: string) {
    if (!ticket) return;
    const updated: Ticket = {
      ...ticket,
      feedback: {
        helpful: helpful ?? ticket.feedback?.helpful ?? null,
        comment: comment || ticket.feedback?.comment || "",
        submittedAt: new Date().toISOString(),
      },
    };
    setTicket(updated);
    await saveTicket(updated);
    try {
      await submitFeedback(ticket.ticketId, comment, helpful ?? undefined);
      setStatus("Thank you! Your feedback was recorded.");
    } catch {
      setStatus("Saved locally, but the backend could not be reached.");
    }
  }

  if (loading) {
    return <div className="ticket-detail-page">Loading...</div>;
  }

  if (!ticket) {
    return (
      <div className="ticket-detail-page">
        <h1>Ticket not found</h1>
        <p>
          Ticket <strong>{id}</strong> is not in this browser's history.
        </p>
        <Link to="/history">← Back to history</Link>
      </div>
    );
  }

  return (
    <div className="ticket-detail-page">
      <Link to="/history">← Back to history</Link>
      <h1>Ticket {ticket.ticketId}</h1>

      <div className="detail-card">
        <div className="detail-meta">
          <div>
            <span>Category</span>
            {ticket.category}
          </div>
          <div>
            <span>Priority</span>
            {ticket.priority}
          </div>
          <div>
            <span>Created</span>
            {new Date(ticket.createdDate).toLocaleString()}
          </div>
          <div>
            <span>Status</span>
            {ticket.status}
          </div>
        </div>
        <p>{ticket.description}</p>
      </div>

      <div className="detail-card resolution-container">
        {ticket.suggestedResolution ? (
          <ResolutionResult
            suggestion={ticket.suggestedResolution}
            confidence={ticket.confidence ?? 0}
            method={ticket.method ?? "retrieval"}
            similarTickets={ticket.similarTickets ?? []}
          />
        ) : (
          <p>No resolution was generated for this ticket (the backend was not reachable).</p>
        )}
      </div>

      {ticket.suggestedResolution && (
        <div className="detail-card">
          <h3>Was this resolution helpful?</h3>
          <div className="feedback-buttons">
            <button
              type="button"
              className={ticket.feedback?.helpful === true ? "selected" : ""}
              onClick={() => sendFeedback(true, "")}
            >
              👍 Yes
            </button>
            <button
              type="button"
              className={ticket.feedback?.helpful === false ? "selected" : ""}
              onClick={() => sendFeedback(false, "")}
            >
              👎 No
            </button>
          </div>
          <ResolutionFeedback onSubmit={(comment) => sendFeedback(null, comment)} />
          {status && (
            <p className="feedback-status" role="status">
              {status}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default TicketDetailPage;
