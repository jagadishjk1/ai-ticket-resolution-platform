import axios from "axios";
import { API_CONFIG } from "../config/apiConfig";

/** Send feedback on a suggested resolution to the RAG service. */
export async function submitFeedback(
  ticketId: string,
  feedback: string,
  helpful?: boolean
): Promise<{ status: string }> {
  const url = `${API_CONFIG.RAG_SERVICE_URL}${API_CONFIG.ENDPOINTS.FEEDBACK}/${encodeURIComponent(ticketId)}`;
  const body = helpful === undefined ? { feedback } : { feedback, helpful };
  const response = await axios.post(url, body, { timeout: API_CONFIG.TIMEOUT });
  return response.data;
}
