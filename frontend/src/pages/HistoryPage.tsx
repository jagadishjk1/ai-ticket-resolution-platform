import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { clearTickets, getAllTickets } from "../api/ticketApi";
import type { Ticket } from "../types/ticketTypes";
import "./HistoryPage.css";

/** Lists the tickets submitted from this browser with their suggested resolution. */
const HistoryPage: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAllTickets()
      .then(setTickets)
      .finally(() => setLoading(false));
  }, []);

  const handleClear = async () => {
    if (!window.confirm("Delete all tickets from the history?")) return;
    await clearTickets();
    setTickets([]);
  };

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>Ticket History</h1>
        {tickets.length > 0 && (
          <button type="button" className="history-clear" onClick={handleClear}>
            Clear history
          </button>
        )}
      </div>
      <p className="history-subtitle">
        Tickets submitted from this browser (stored locally).
      </p>

      {loading ? (
        <p>Loading...</p>
      ) : tickets.length === 0 ? (
        <div className="history-empty">
          <p>No tickets yet.</p>
          <Link to="/">Submit your first ticket →</Link>
        </div>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Created</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Description</th>
              <th>Match</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.ticketId}>
                <td>
                  <Link to={`/ticket/${ticket.ticketId}`}>{ticket.ticketId}</Link>
                </td>
                <td>{new Date(ticket.createdDate).toLocaleString()}</td>
                <td>{ticket.category}</td>
                <td>
                  <span className={`priority-tag ${ticket.priority.toLowerCase()}`}>
                    {ticket.priority}
                  </span>
                </td>
                <td className="history-description">{ticket.description}</td>
                <td>
                  {ticket.similarTickets && ticket.similarTickets.length > 0
                    ? `${Math.round((ticket.confidence ?? 0) * 100)}%`
                    : ticket.suggestedResolution
                      ? "No match"
                      : "Pending"}
                </td>
                <td>
                  {ticket.feedback?.helpful === true
                    ? "👍"
                    : ticket.feedback?.helpful === false
                      ? "👎"
                      : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default HistoryPage;
