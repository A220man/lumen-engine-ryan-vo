/* Typed API client for Lumen Engine backend. */

export interface Skill {
  id: string;
  name: string;
  description: string | null;
  harness: string;
  command: string;
  category: string | null;
  tags: string[];
  is_active: boolean;
  version: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSkill {
  name: string;
  description?: string | null;
  harness: string;
  command: string;
  category?: string | null;
  tags?: string[];
  is_active?: boolean;
  version?: string;
}

export interface UpdateSkill {
  name?: string;
  description?: string | null;
  harness?: string;
  command?: string;
  category?: string | null;
  tags?: string[];
  is_active?: boolean;
  version?: string;
}

export interface PaginatedSkills {
  items: Skill[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface Execution {
  id: string;
  skill_id: string;
  skill_version: string;
  status: string;
  input_data: string | null;
  output_data: string | null;
  error_message: string | null;
  exit_code: number | null;
  duration_ms: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface CreateExecution {
  input_data?: string | null;
  timeout_seconds?: number | null;
  env_vars?: Record<string, string> | null;
}

export interface PaginatedExecutions {
  items: Execution[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}


export interface HealthResponse {
  status: string;
  app: string;
  version: string;
}


const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${API_BASE}/api/v1${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new APIError(
      `HTTP ${resp.status}: ${text || resp.statusText}`,
      resp.status
    );
  }
  if (resp.status === 204) {
    return undefined as T;
  }
  return resp.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  listSkills: (params?: {
    page?: number;
    per_page?: number;
    harness?: string;
    category?: string;
    is_active?: boolean;
    search?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.per_page) q.set("per_page", String(params.per_page));
    if (params?.harness) q.set("harness", params.harness);
    if (params?.category) q.set("category", params.category);
    if (params?.is_active !== undefined) q.set("is_active", String(params.is_active));
    if (params?.search) q.set("search", params.search);
    const query = q.toString() ? `?${q.toString()}` : "";
    return request<PaginatedSkills>(`/skills${query}`);
  },

  getSkill: (id: string) => request<Skill>(`/skills/${id}`),

  createSkill: (data: CreateSkill) =>
    request<Skill>("/skills", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateSkill: (id: string, data: UpdateSkill) =>
    request<Skill>(`/skills/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteSkill: (id: string) =>
    request<void>(`/skills/${id}`, { method: "DELETE" }),

  executeSkill: (skillId: string, data: CreateExecution) =>
    request<Execution>(`/skills/${skillId}/execute`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listExecutions: (skillId: string, params?: {
    status?: string;
    page?: number;
    per_page?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.page) q.set("page", String(params.page));
    if (params?.per_page) q.set("per_page", String(params.per_page));
    const query = q.toString() ? `?${q.toString()}` : "";
    return request<PaginatedExecutions>(`/skills/${skillId}/executions${query}`);
  },

  getExecution: (id: string) => request<Execution>(`/executions/${id}`),
};