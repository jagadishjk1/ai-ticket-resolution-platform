import React, { useEffect, useState } from "react";
import TicketUploadForm from "../components/TicketUpload/TicketUploadForm";
import {
  getRAGMetrics,
  getRAGStats,
  type RAGMetrics,
  type RAGStats,
} from "../api/resolutionApi";
import "./DashboardPage.css";

/** Live numbers from the backend instead of hard-coded marketing figures. */
function useServiceStats() {
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [metrics, setMetrics] = useState<RAGMetrics | null>(null);
  // "offline" = no answer at all; "not-ready" = backend answered 503 (dataset failed to load)
  const [problem, setProblem] = useState<"" | "offline" | "not-ready">("");

  useEffect(() => {
    let active = true;
    Promise.all([getRAGStats(), getRAGMetrics()])
      .then(([s, m]) => {
        if (!active) return;
        setStats(s);
        setMetrics(m);
      })
      .catch((err) => {
        if (!active) return;
        setProblem(err?.response?.status === 503 ? "not-ready" : "offline");
      });
    return () => {
      active = false;
    };
  }, []);

  return { stats, metrics, problem };
}

const DashboardPage: React.FC = () => {
  const { stats, metrics, problem } = useServiceStats();
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setStatsVisible(true), 300);
    return () => clearTimeout(timer);
  }, []);

  const avgMs = metrics?.response_times?.avg;
  const statItems = [
    {
      icon: "📚",
      value: stats ? String(stats.total_tickets) : "—",
      label: "Resolved Tickets in Knowledge Base",
    },
    {
      icon: "⏱️",
      value:
        avgMs && metrics?.total_queries
          ? avgMs < 1000
            ? `${Math.round(avgMs)} ms`
            : `${(avgMs / 1000).toFixed(1)} s`
          : "—",
      label: "Avg Response Time",
    },
    {
      icon: "🤖",
      value: stats ? (stats.ai_available ? "AI + RAG" : "Retrieval") : "—",
      label: "Resolution Mode",
    },
  ];

  return (
    <div className="dashboard-page">
      <div className="hero-section">
        <div className="hero-background">
          <div className="floating-shape shape-1"></div>
          <div className="floating-shape shape-2"></div>
          <div className="floating-shape shape-3"></div>
        </div>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">🚀</span>
            <span>Retrieval-Augmented Generation</span>
          </div>
          <h1 className="hero-title">TicketGenie Dashboard</h1>
          <p className="hero-subtitle">
            AI-Assisted IT Support Ticket Resolution System
          </p>
          <div className={`hero-stats ${statsVisible ? "visible" : ""}`}>
            {statItems.map((item) => (
              <div className="stat-item" key={item.label}>
                <div className="stat-icon">{item.icon}</div>
                <div className="stat-value">{item.value}</div>
                <div className="stat-label">{item.label}</div>
              </div>
            ))}
          </div>
          {problem === "offline" && (
            <p className="hero-subtitle" role="status">
              ⚠️ Backend not reachable - start it with{" "}
              <code>uvicorn app:app</code> in the backend folder.
            </p>
          )}
          {problem === "not-ready" && (
            <p className="hero-subtitle" role="status">
              ⚠️ Backend is running but the knowledge base failed to load - check
              the error in the backend terminal.
            </p>
          )}
        </div>
      </div>

      <div className="dashboard-container">
        <div className="dashboard-section">
          <div className="section-header">
            <div className="section-icon">📝</div>
            <h2>Submit New Ticket</h2>
          </div>
          <TicketUploadForm />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
