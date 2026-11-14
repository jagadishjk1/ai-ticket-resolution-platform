import axios from "axios";
import { API_CONFIG } from "../config/apiConfig";
// Types matching the RAG service response
export interface SimilarTicket {
  ticket_id?: string;
  category: string;
  description: string;
  resolution: string;
  priority?: string;
  similarity_score: number;
}
export interface ResolutionTiming {
  search_time_ms: number;
  generation_time_ms: number;
  total_time_ms: number;
}
/**
 * method values returned by the backend:
 * - "ai-refined":  AI wrote the answer using similar tickets
 * - "retrieval":   best matching past resolution (AI not configured or failed)
 * - "ai-fallback": no similar ticket, AI wrote general guidance
 * - "no-match":    no similar ticket and no AI - generic next steps
 */
export interface ResolutionResponse {
  suggested_resolution: string;
  confidence: number;
  similar_tickets: SimilarTicket[];
  method: string;
  timing?: ResolutionTiming;
  metadata?: {
    processing_time?: number;
    model_used?: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    [key: string]: any;
  };
}
export interface TicketResolutionRequest {
  category: string;
  priority: string;
  description: string;
}
/**
 * Get resolution suggestion from RAG service
 * Uses the Python FastAPI backend with Hugging Face
 */
export async function getResolutionSuggestion(
  category: string,
  priority: string,
  description: string
): Promise<ResolutionResponse> {
  try {
    console.log(
      "%c🤖 RAG Resolution Request",
      "background: #8b5cf6; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold"
    );
    console.log("Request:", { category, priority, description });
    const endpoint = `${API_CONFIG.RAG_SERVICE_URL}${API_CONFIG.ENDPOINTS.SUGGEST_RESOLUTION}`;
    const response = await axios.post<ResolutionResponse>(
      endpoint,
      {
        category,
        priority,
        description,
      } as TicketResolutionRequest,
      {
        headers: {
          "Content-Type": "application/json",
        },
        timeout: API_CONFIG.TIMEOUT,
      }
    );
    console.log(
      "%c✅ RAG Resolution Received",
      "background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold"
    );
    console.log("Response:", response.data);
    return response.data;
  } catch (error) {
    console.log(
      "%c❌ RAG Resolution Failed",
      "background: #ef4444; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold"
    );
    console.error("Error Details:", error);
    if (axios.isAxiosError(error)) {
      console.error("Response Status:", error.response?.status);
      console.error("Response Data:", error.response?.data);
      const detail = error.response?.data?.detail;
      // FastAPI validation errors (422) arrive as a list of { msg, loc } objects
      const detailText = Array.isArray(detail)
        ? detail
            .map((d: { msg?: string; loc?: string[] }) =>
              d?.loc ? `${d.loc[d.loc.length - 1]}: ${d.msg}` : d?.msg
            )
            .join("; ")
        : detail;
      const errorMessage =
        detailText ||
        error.response?.data?.message ||
        error.message ||
        "Failed to get resolution suggestion";
      throw new Error(errorMessage);
    }
    throw error;
  }
}
/**
 * Check RAG service health
 */
export async function checkRAGHealth(): Promise<{
  status: string;
  knowledge_base_size: number;
  ai_available: boolean;
}> {
  try {
    const endpoint = `${API_CONFIG.RAG_SERVICE_URL}${API_CONFIG.ENDPOINTS.RAG_HEALTH}`;
    const response = await axios.get(endpoint, { timeout: 5000 });
    return response.data;
  } catch (error) {
    console.error("RAG health check failed:", error);
    throw new Error("RAG service is not available");
  }
}
export interface RAGStats {
  total_tickets: number;
  top_categories: Record<string, number>;
  ai_available: boolean;
  dataset: string | null;
  service_status: string;
}
/**
 * Get knowledge base statistics
 */
export async function getRAGStats(): Promise<RAGStats> {
  const endpoint = `${API_CONFIG.RAG_SERVICE_URL}${API_CONFIG.ENDPOINTS.RAG_STATS}`;
  const response = await axios.get<RAGStats>(endpoint, { timeout: 5000 });
  return response.data;
}
export interface RAGMetrics {
  total_queries: number;
  success_rate: number;
  response_times?: { avg: number; min: number; max: number; median: number };
  confidence_scores?: { avg: number; min: number; max: number };
  feedback?: {
    total: number;
    helpful: number;
    not_helpful: number;
    helpful_rate: number | null;
  };
}
/**
 * Get live performance metrics (since the service started)
 */
export async function getRAGMetrics(): Promise<RAGMetrics> {
  const endpoint = `${API_CONFIG.RAG_SERVICE_URL}${API_CONFIG.ENDPOINTS.RAG_METRICS}`;
  const response = await axios.get<RAGMetrics>(endpoint, { timeout: 5000 });
  return response.data;
}
/**
 * Get ticket categories known to the knowledge base
 */
export async function getCategories(): Promise<string[]> {
  const endpoint = `${API_CONFIG.RAG_SERVICE_URL}${API_CONFIG.ENDPOINTS.CATEGORIES}`;
  const response = await axios.get<{ categories: string[] }>(endpoint, {
    timeout: 5000,
  });
  return Array.isArray(response.data?.categories) ? response.data.categories : [];
}
