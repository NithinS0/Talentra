/**
 * Common API error response structure matching FastAPI errors.
 */
export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  detail: string | ApiErrorDetail[];
  code?: string;
  request_id?: string;
}

/**
 * Standard Paginated Response envelope.
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/**
 * Health check endpoint response.
 */
export interface HealthStatusResponse {
  status: string;
  service: string;
  environment: string;
  database?: string;
}
