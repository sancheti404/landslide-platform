/**
 * Centralized API Client
 * Targets Spring Boot API Gateway exclusively (:8080).
 * Never directly targets PostGIS or FastAPI.
 */

const getBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  if (import.meta.env.MODE === 'test') return 'http://127.0.0.1:8080';
  return '';
};

/**
 * Standard fetch wrapper with timeout, JSON parsing, and unified error handling
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${getBaseUrl()}${endpoint}`;
  const timeoutMs = options.timeout || 25000;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Parse JSON response body if present
    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }

    if (!response.ok) {
      const errorMessage =
        (data && (data.message || data.error || data.detail)) ||
        `HTTP Error ${response.status}: ${response.statusText}`;

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      error.isUnsupportedLocation =
        response.status === 400 &&
        data &&
        (data.error === 'UNSUPPORTED_LOCATION' ||
         String(errorMessage).toLowerCase().includes('envelope') ||
         String(errorMessage).toLowerCase().includes('outside'));
      throw error;
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      const timeoutError = new Error(`Request timeout after ${timeoutMs}ms connecting to backend.`);
      timeoutError.status = 408;
      throw timeoutError;
    }
    throw err;
  }
}
