import type {
  AdminApplicationDetail,
  AdminApplicationFilters,
  AdminApplicationListResponse,
  AdminMetrics,
  Application,
  ApplicationPayload,
  ApplicationStatus,
  AuditLog,
  DocumentMetadata,
  Lead,
  LeadStatus,
  Notification,
  Pricing,
  User,
  AdminAnalytics,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type RequestOptions = RequestInit & {
  token?: string | null;
  isFormData?: boolean;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!options.isFormData) {
    headers.set("Content-Type", "application/json");
  }
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const authApi = {
  async register(payload: { email: string; password: string; full_name?: string }): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!response.ok) {
      throw new Error("Incorrect email or password");
    }
    return response.json();
  },

  async me(token: string): Promise<User> {
    return request<User>("/users/me", { token });
  },

  async logout(token: string): Promise<void> {
    return request<void>("/auth/logout", {
      method: "POST",
      token,
    });
  },
};

export const applicationApi = {
  async mine(token: string): Promise<Application[]> {
    return request<Application[]>("/applications/my", { token });
  },

  async create(token: string, payload: ApplicationPayload): Promise<Application> {
    return request<Application>("/applications", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    });
  },

  async detail(token: string, id: string): Promise<Application> {
    return request<Application>(`/applications/${id}`, { token });
  },

  async documents(token: string, id: string): Promise<DocumentMetadata[]> {
    return request<DocumentMetadata[]>(`/applications/${id}/documents`, { token });
  },
};

export const documentApi = {
  async upload(
    token: string,
    applicationId: string,
    documentType: string,
    file: File,
  ): Promise<DocumentMetadata> {
    const body = new FormData();
    body.set("document_type", documentType);
    body.set("file", file);
    return request<DocumentMetadata>(`/applications/${applicationId}/documents/upload`, {
      method: "POST",
      token,
      isFormData: true,
      body,
    });
  },
};

function buildQuery(filters: AdminApplicationFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const adminApi = {
  async metrics(token: string): Promise<AdminMetrics> {
    return request<AdminMetrics>("/admin/applications/metrics", { token });
  },

  async listApplications(
    token: string,
    filters: AdminApplicationFilters = {},
  ): Promise<AdminApplicationListResponse> {
    return request<AdminApplicationListResponse>(`/admin/applications${buildQuery(filters)}`, { token });
  },

  async applicationDetail(token: string, id: string): Promise<AdminApplicationDetail> {
    return request<AdminApplicationDetail>(`/admin/applications/${id}`, { token });
  },

  async updateStatus(
    token: string,
    id: string,
    payload: {
      status: Exclude<ApplicationStatus, "draft">;
      customer_clarification_message?: string | null;
      note?: string | null;
    },
  ): Promise<AdminApplicationDetail> {
    return request<AdminApplicationDetail>(`/admin/applications/${id}/status`, {
      method: "PATCH",
      token,
      body: JSON.stringify(payload),
    });
  },

  async updateNotes(
    token: string,
    id: string,
    payload: {
      internal_admin_notes?: string | null;
      customer_clarification_message?: string | null;
    },
  ): Promise<AdminApplicationDetail> {
    return request<AdminApplicationDetail>(`/admin/applications/${id}/notes`, {
      method: "PATCH",
      token,
      body: JSON.stringify(payload),
    });
  },

  async auditLogs(token: string, id: string): Promise<AuditLog[]> {
    const detail = await this.applicationDetail(token, id);
    return detail.audit_logs;
  },

  async downloadDocument(token: string, documentId: number): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error("Could not download document");
    }
    return response.blob();
  },

  async notifications(token: string): Promise<Notification[]> {
    return request<Notification[]>("/admin/notifications", { token });
  },

  async analytics(token: string): Promise<AdminAnalytics> {
    return request<AdminAnalytics>("/admin/analytics", { token });
  },

  async leads(token: string): Promise<Lead[]> {
    return request<Lead[]>("/admin/leads", { token });
  },

  async lead(token: string, id: string): Promise<Lead> {
    return request<Lead>(`/admin/leads/${id}`, { token });
  },

  async updateLeadStatus(token: string, id: string, status: LeadStatus): Promise<Lead> {
    return request<Lead>(`/admin/leads/${id}/status`, {
      method: "PATCH",
      token,
      body: JSON.stringify({ status }),
    });
  },
};

export const notificationApi = {
  async mine(token: string): Promise<Notification[]> {
    return request<Notification[]>("/notifications/my", { token });
  },

  async markRead(token: string, notificationId: number): Promise<Notification> {
    return request<Notification>(`/notifications/${notificationId}/read`, {
      method: "PATCH",
      token,
      body: JSON.stringify({}),
    });
  },
};

export const publicApi = {
  async pricing(): Promise<Pricing> {
    return request<Pricing>("/pricing");
  },

  async createLead(payload: {
    name: string;
    mobile: string;
    email?: string;
    service_interest: string;
    message?: string;
  }): Promise<Lead> {
    return request<Lead>("/leads", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

export { API_BASE_URL };
