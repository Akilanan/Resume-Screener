/**
 * API Service for Resume Screener Backend
 */

export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
export const API_BASE = import.meta.env.VITE_API_URL?.replace("/api/v1", "") || "http://localhost:8000";

console.log("API Base URL:", BASE_URL);

// Helper to decode JWT payload and check expiry
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp) {
      return Date.now() >= payload.exp * 1000;
    }
    return false;
  } catch {
    return true;
  }
}

// Clear expired tokens on load
const token = localStorage.getItem("access_token");
if (token && isTokenExpired(token)) {
  console.log("Token expired, clearing...");
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("role");
}

const getHeaders = () => {
  const token = localStorage.getItem("access_token");
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

export interface ScreeningResult {
  filename: string;
  name?: string;
  match_score: number;         // 0-100
  matched_skills: string[];
  missing_skills: string[];
  summary?: string;
  email?: string;
  phone?: string;
  experience?: number;
  education?: string;
}

export interface ScreeningResponse {
  results: ScreeningResult[];
  job_description: string;
  total: number;
}

/**
 * Login user and store tokens
 */
export async function login(email: string, password: string): Promise<any> {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Login failed");
  }

  const data = await response.json();
  if (!data.mfa_required) {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("role", data.role);
  }
  return data;
}

/**
 * Verify OTP and store tokens
 */
export async function verifyOtp(email: string, otp: string): Promise<any> {
  const response = await fetch(`${BASE_URL}/auth/verify-otp`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, otp }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Invalid OTP");
  }

  const data = await response.json();
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  localStorage.setItem("role", data.role);
  return data;
}

/**
 * Logout user
 */
export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("role");
  window.location.href = "/login";
}

/**
 * Screen resumes against a job description.
 * Submits to backend, then polls for real AI results until worker finishes.
 */
export async function screenResumes(
  jobDescription: string,
  files: File[],
  onProgress?: (completed: number, total: number) => void
): Promise<ScreeningResponse> {
  const formData = new FormData();
  formData.append("job_description", jobDescription);
  files.forEach((file) => {
    formData.append("resumes", file, file.name);
  });

  try {
    // Step 1: Submit resumes to backend (queues them for worker processing)
    const response = await fetch(`${BASE_URL}/resumes/screen`, {
      method: "POST",
      headers: getHeaders(),
      body: formData,
    });

    if (response.status === 401) {
      logout();
      throw new Error("Session expired. Please login again.");
    }

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Screening failed: ${error}`);
    }

    const queueResponse = await response.json();
    const jobId = queueResponse.job_id;
    const total = queueResponse.total;

    if (!jobId) {
      // No job_id means something unexpected — return raw response
      return queueResponse;
    }

    // Step 2: Poll for real results until all resumes are processed
    const maxAttempts = 60; // 60 * 2s = 2 minutes max wait
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 2000)); // Wait 2 seconds

      const pollResponse = await fetch(`${BASE_URL}/resumes/results/${jobId}`, {
        headers: getHeaders(),
      });

      if (!pollResponse.ok) continue;

      const results: any[] = await pollResponse.json();
      const completed = results.filter(
        (r: any) => r.status === "completed" || r.status === "failed"
      ).length;

      if (onProgress) onProgress(completed, total);

      if (completed >= total) {
        // All done — map to ScreeningResponse format
        return {
          job_description: jobDescription,
          total: results.length,
          results: results.map((r: any) => ({
            filename: r.filename,
            match_score: r.score || 0,
            matched_skills: parseJsonField(r.skills_matched),
            missing_skills: parseJsonField(r.skills_missing),
            summary: r.match_summary || "",
          })),
        };
      }
    }

    // Timed out — return whatever we have
    throw new Error("Screening timed out. Results may still be processing. Check the Results page.");
  } catch (err: any) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error("Cannot connect to backend. Please check if the server is running.");
    }
    throw err;
  }
}

/** Parse a JSON string field or pass through arrays */
function parseJsonField(val: any): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === "string") {
    try { return JSON.parse(val); } catch { return []; }
  }
  return [];
}

/**
 * Fetch all past screening results from the backend.
 */
export async function fetchResults(jobId?: string): Promise<any> {
  const url = jobId ? `${BASE_URL}/resumes/results/${jobId}` : `${BASE_URL}/admin/resumes`;
  const response = await fetch(url, {
    headers: getHeaders(),
  });
  
  if (response.status === 401) {
    logout();
    throw new Error("Session expired. Please login again.");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch results");
  }
  return response.json();
}

/**
 * Fetch dashboard statistics and analytics.
 */
export async function fetchDashboardStats(): Promise<any> {
  const response = await fetch(`${BASE_URL}/analytics/dashboard`, {
    headers: getHeaders(),
  });

  if (response.status === 401) {
    logout();
    throw new Error("Session expired. Please login again.");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard stats");
  }
  return response.json();
}

/**
 * Health check — ping the backend to confirm it's running.
 */
export async function pingBackend(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE_URL.replace("/api/v1", "")}/health`, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}
