import axios from "axios";

// Vite proxies /v1 -> api.localhost in dev; in prod the portal is served from
// the same Traefik so /v1/* is routed at the edge.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  withCredentials: true,
});

export interface User {
  id: string;
  email: string;
  name: string | null;
}

export interface Site {
  id: string;
  name: string;
  allowed_origins: string;
  public_key: string;
  widget_config: Record<string, unknown>;
  created_at: string;
}

export interface DataSource {
  id: string;
  site_id: string;
  type: "url" | "upload";
  config: Record<string, unknown>;
  status: "pending" | "running" | "ready" | "failed";
  error_message: string | null;
  stats: Record<string, number>;
  last_synced_at: string | null;
  created_at: string;
}

export interface Citation {
  index: number;
  chunk_id: string;
  document_id: string;
  source_uri: string;
  title: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  site_id: string;
  visitor_id: string | null;
  created_at: string;
  messages: Message[];
}

export const Auth = {
  me: () => api.get<User>("/v1/auth/me").then((r) => r.data),
  login: (email: string, password: string) =>
    api.post<User>("/v1/auth/login", { email, password }).then((r) => r.data),
  signup: (email: string, password: string, name?: string) =>
    api.post<User>("/v1/auth/signup", { email, password, name }).then((r) => r.data),
  logout: () => api.post("/v1/auth/logout"),
};

export const Sites = {
  list: () => api.get<Site[]>("/v1/sites").then((r) => r.data),
  get: (id: string) => api.get<Site>(`/v1/sites/${id}`).then((r) => r.data),
  create: (payload: { name: string; allowed_origins?: string }) =>
    api.post<Site>("/v1/sites", payload).then((r) => r.data),
  update: (id: string, payload: Partial<Site>) =>
    api.patch<Site>(`/v1/sites/${id}`, payload).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/sites/${id}`),
};

export const Sources = {
  list: (siteId: string) =>
    api.get<DataSource[]>(`/v1/sources/sites/${siteId}`).then((r) => r.data),
  get: (id: string) => api.get<DataSource>(`/v1/sources/${id}`).then((r) => r.data),
  createUrl: (
    siteId: string,
    payload: { url: string; max_pages?: number; max_depth?: number },
  ) =>
    api
      .post<DataSource>(`/v1/sources/sites/${siteId}/url`, { type: "url", ...payload })
      .then((r) => r.data),
  createUpload: (
    siteId: string,
    payload: { s3_keys: string[]; original_names: string[] },
  ) =>
    api
      .post<DataSource>(`/v1/sources/sites/${siteId}/upload`, { type: "upload", ...payload })
      .then((r) => r.data),
  presign: (siteId: string, filename: string, contentType: string) =>
    api
      .post<{ upload_url: string; s3_key: string; expires_in: number }>(
        `/v1/sources/sites/${siteId}/presign`,
        { filename, content_type: contentType },
      )
      .then((r) => r.data),
  resync: (id: string) => api.post<DataSource>(`/v1/sources/${id}/resync`).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/sources/${id}`),
};

export const Conversations = {
  list: (siteId: string) =>
    api.get<Conversation[]>(`/v1/conversations/sites/${siteId}`).then((r) => r.data),
  get: (id: string) =>
    api.get<Conversation>(`/v1/conversations/${id}`).then((r) => r.data),
};
