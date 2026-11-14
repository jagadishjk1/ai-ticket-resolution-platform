import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useUploadTicket } from "../../hooks/useUploadTicket";
import { useResolutionSuggestion } from "../../hooks/useResolutionSuggestion";
import { getCategories } from "../../api/resolutionApi";
import { saveTicket } from "../../api/ticketApi";
import type { Ticket } from "../../types/ticketTypes";
import LoadingSpinner from "../Common/LoadingSpinner";
import ResolutionResult from "../ResolutionSuggestion/ResolutionResult";
import "./TicketUploadForm.css";

// Used until the backend's /api/categories responds (matches the demo dataset).
const DEFAULT_CATEGORIES = [
  "Application Bug",
  "Email Issues",
  "Hardware Request",
  "Network Connectivity",
  "Password Reset",
  "Printer Issues",
  "System Crash",
  "VPN Access",
];
const PRIORITIES = ["Low", "Medium", "High", "Critical"];
const MIN_DESCRIPTION_LENGTH = 5;
const MAX_DESCRIPTION_LENGTH = 2000;

/**
 * TicketUploadForm - collects ticket details, asks the RAG service for a
 * resolution and stores the result in the ticket history.
 */
const TicketUploadForm: React.FC = () => {
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [submitted, setSubmitted] = useState<Ticket | null>(null);

  const { uploadTicket, loading, error } = useUploadTicket();
  const {
    suggestion,
    confidence,
    method,
    similarTickets,
    loading: resolutionLoading,
    error: resolutionError,
    fetchResolution,
  } = useResolutionSuggestion();

  // Load the categories that actually exist in the knowledge base.
  useEffect(() => {
    let active = true;
    getCategories()
      .then((list) => {
        if (active && list.length > 0) setCategories(list);
      })
      .catch(() => {
        /* backend offline - keep the default list */
      });
    return () => {
      active = false;
    };
  }, []);

  const trimmed = description.trim();
  const isValid =
    !!category && !!priority && trimmed.length >= MIN_DESCRIPTION_LENGTH;
  const busy = loading || resolutionLoading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || busy) return;

    const ticket = await uploadTicket({
      file: null,
      description: trimmed,
      category,
      priority,
    });
    if (!ticket) return;
    setSubmitted(ticket);

    try {
      const response = await fetchResolution(category, priority, trimmed);
      await saveTicket({
        ...ticket,
        suggestedResolution: response.suggested_resolution,
        confidence: response.confidence,
        method: response.method,
        similarTickets: response.similar_tickets,
      });
      // Clear the form only after a successful answer, so input is not lost on errors.
      setDescription("");
      setCategory("");
      setPriority("");
    } catch {
      // The error is shown from the hook's `resolutionError` state.
    }
  };

  return (
    <form className="ticket-upload-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="ticket-category">
          <span className="label-text">Category</span>
          <span className="label-required">*</span>
        </label>
        <select
          id="ticket-category"
          className="form-select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          required
        >
          <option value="">Select a category...</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="ticket-priority">
          <span className="label-text">Priority</span>
          <span className="label-required">*</span>
        </label>
        <select
          id="ticket-priority"
          className="form-select"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          required
        >
          <option value="">Select a priority...</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="ticket-description">
          <span className="label-text">Description</span>
          <span className="label-required">*</span>
        </label>
        <textarea
          id="ticket-description"
          className="form-textarea"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          minLength={MIN_DESCRIPTION_LENGTH}
          maxLength={MAX_DESCRIPTION_LENGTH}
          placeholder="Describe the issue, e.g. 'VPN keeps disconnecting every few minutes when working from home'"
          rows={5}
        />
        <div className="char-counter">
          {description.length}/{MAX_DESCRIPTION_LENGTH} characters
          {trimmed.length > 0 && trimmed.length < MIN_DESCRIPTION_LENGTH &&
            ` (minimum ${MIN_DESCRIPTION_LENGTH})`}
        </div>
      </div>

      <button type="submit" className="btn-submit" disabled={busy || !isValid}>
        {busy ? (
          <span className="btn-loading">
            <LoadingSpinner />
            <span>{loading ? "Submitting..." : "Finding resolution..."}</span>
          </span>
        ) : (
          <>
            <span className="btn-icon">🚀</span>
            <span>Submit Ticket</span>
          </>
        )}
      </button>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {resolutionLoading && (
        <div className="resolution-loading">
          <LoadingSpinner />
          <span>Searching similar tickets and generating a resolution...</span>
        </div>
      )}

      {submitted && !busy && (suggestion || resolutionError) && (
        <div className="resolution-container">
          <div className="ticket-summary-section">
            <div className="summary-header">
              <span className="summary-icon">📋</span>
              <h4 className="summary-title">Ticket Summary</h4>
            </div>
            <div className="summary-content">
              <div className="summary-item">
                <span className="summary-label">Ticket ID:</span>
                <span className="summary-value">
                  <Link to={`/ticket/${submitted.ticketId}`}>
                    {submitted.ticketId}
                  </Link>
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Category:</span>
                <span className="summary-value">{submitted.category}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Priority:</span>
                <span className="summary-value">{submitted.priority}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Description:</span>
                <p className="summary-description">{submitted.description}</p>
              </div>
            </div>
          </div>

          <div className="resolution-divider"></div>

          {suggestion ? (
            <ResolutionResult
              suggestion={suggestion}
              confidence={confidence}
              method={method}
              similarTickets={similarTickets}
            />
          ) : (
            <div
              className="error-message"
              style={{
                background: "#fef3c7",
                color: "#92400e",
                border: "1px solid #fbbf24",
              }}
            >
              <span className="error-icon">ℹ️</span>
              <span>
                Could not get a resolution: {resolutionError}. Make sure the
                backend is running on port 8000 (see README → How to Run).
              </span>
            </div>
          )}
        </div>
      )}
    </form>
  );
};

export default TicketUploadForm;
