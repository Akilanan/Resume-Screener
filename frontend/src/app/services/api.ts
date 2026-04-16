/**
 * API Service for Resume Screener Backend
 */

export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

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
  const formData = new FormData();
  formData.append("username", email);
  formData.append("password", password);

  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Login failed");
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
 */
export async function screenResumes(
  jobDescription: string,
  files: File[]
): Promise<ScreeningResponse> {
  const formData = new FormData();
  formData.append("job_description", jobDescription);
  files.forEach((file) => {
    formData.append("resumes", file, file.name);
  });

  const response = await fetch(`${BASE_URL}/screen`, {
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

  return response.json();
}

/**
 * Fetch all past screening results from the backend.
 */
export async function fetchResults(): Promise<ScreeningResponse[]> {
  const response = await fetch(`${BASE_URL}/results`, {
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
 * Health check — ping the backend to confirm it's running.
 */
export async function pingBackend(): Promise<boolean> {
  try {
    const response = await fetch(`${BASE_URL}/health`, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}
