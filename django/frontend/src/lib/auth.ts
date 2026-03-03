import { apiFetch } from "./api";
import type { User } from "@/types/user";

/**
 * Set auth cookies manually via document.cookie.
 *
 * Why: Some browsers / extensions block Set-Cookie headers from fetch()
 * responses, so HttpOnly cookies set by the API never arrive. Setting
 * JWT_AUTH_HTTPONLY=False on the backend means the tokens are returned in
 * the response body AND as (non-HttpOnly) Set-Cookie headers. We set them
 * explicitly here as a reliable fallback.
 */
function setAuthCookies(access: string, refresh?: string) {
  if (typeof document === "undefined") return;
  const secure = window.location.protocol === "https:" ? "; secure" : "";
  if (access) {
    document.cookie = `access=${access}; path=/; max-age=900; samesite=lax${secure}`;
  }
  if (refresh) {
    document.cookie = `refresh=${refresh}; path=/; max-age=604800; samesite=lax${secure}`;
  }
}

function clearAuthCookies() {
  if (typeof document === "undefined") return;
  document.cookie = "access=; path=/; max-age=0";
  document.cookie = "refresh=; path=/; max-age=0";
}

export async function login(email: string, password: string) {
  const data = await apiFetch<{ access: string; refresh: string }>("/api/v1/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setAuthCookies(data.access, data.refresh);
  return data;
}

export async function register(data: {
  email: string;
  password1: string;
  password2: string;
  first_name: string;
  last_name: string;
}) {
  return apiFetch("/api/v1/auth/registration/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logout() {
  clearAuthCookies();
  return apiFetch("/api/v1/auth/logout/", { method: "POST" });
}

export async function getMe() {
  return apiFetch<User>("/api/v1/auth/me/");
}

export async function getUserTenants() {
  return apiFetch<
    { id: string; name: string; slug: string; role: string }[]
  >("/api/v1/auth/tenants/");
}

export async function refreshToken() {
  const data = await apiFetch<{ access: string; refresh: string }>("/api/v1/auth/token/refresh/", {
    method: "POST",
  });
  setAuthCookies(data.access, data.refresh);
  return data;
}

export async function verifyEmail(key: string) {
  return apiFetch("/api/v1/auth/registration/verify-email/", {
    method: "POST",
    body: JSON.stringify({ key }),
  });
}

export async function resendVerificationEmail(email: string) {
  return apiFetch("/api/v1/auth/registration/resend-email/", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}
