import { apiFetch } from "./api";
import type { User } from "@/types/user";

export async function login(email: string, password: string) {
  return apiFetch<{ access: string; refresh: string }>("/api/v1/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
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
  return apiFetch("/api/v1/auth/token/refresh/", { method: "POST" });
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
