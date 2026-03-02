const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface ApiOptions extends RequestInit {
  tenantId?: string;
}

class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

async function apiFetch<T = unknown>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const { tenantId, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (tenantId) {
    headers["X-Tenant-ID"] = tenantId;
  }

  const method = (fetchOptions.method || "GET").toUpperCase();
  if (UNSAFE_METHODS.has(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    let message = data.detail;
    if (!message && typeof data === "object" && data !== null) {
      const fieldErrors = Object.entries(data)
        .filter(([, v]) => Array.isArray(v))
        .map(([, v]) => (v as string[]).join(" "))
        .join(" ");
      if (fieldErrors) message = fieldErrors;
    }
    throw new ApiError(
      message || `Request failed with status ${response.status}`,
      response.status,
      data
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export { apiFetch, ApiError };
export type { ApiOptions };
