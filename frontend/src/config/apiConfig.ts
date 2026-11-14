// API Configuration

export const API_CONFIG = {
  // RAG Service (Python FastAPI).
  // In production the frontend is served by the same backend, so a relative URL is used.
  RAG_SERVICE_URL:
    import.meta.env.VITE_API_URL ||
    (import.meta.env.PROD ? "" : "http://localhost:8000"),

  ENDPOINTS: {
    SUGGEST_RESOLUTION: "/api/suggest-resolution",
    CATEGORIES: "/api/categories",
    FEEDBACK: "/api/feedback",
    RAG_HEALTH: "/health",
    RAG_STATS: "/api/stats",
    RAG_METRICS: "/api/metrics",
  },

  TIMEOUT: 30000, // 30 seconds (AI generation can be slow)
};

export default API_CONFIG;
