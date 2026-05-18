const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDatasets() {
  return request<import("./types").DatasetItem[]>("/api/datasets");
}

export async function createTask(data: {
  task_type: string;
  data_source: string;
  requirements: Record<string, string>;
  api_key?: string;
}) {
  return request<{ task_id: string; status: string }>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getTasks() {
  return request<import("./types").Task[]>("/api/tasks");
}

export async function getTaskDetail(taskId: string) {
  return request<import("./types").Task>(`/api/tasks/${taskId}`);
}

export async function getTaskProgress(taskId: string) {
  return request<import("./types").TaskProgress>(`/api/tasks/${taskId}/progress`);
}

export async function getTaskReport(taskId: string) {
  return request<import("./types").AnalysisResults>(`/api/tasks/${taskId}/report`);
}

export async function stopTask(taskId: string) {
  return request<{ ok: boolean }>(`/api/tasks/${taskId}/stop`, { method: "POST" });
}

export async function deleteTask(taskId: string) {
  return request<{ ok: boolean }>(`/api/tasks/${taskId}`, { method: "DELETE" });
}

export async function testApiKey(apiKey: string) {
  return request<{ ok: boolean; message: string }>("/api/test-api-key", {
    method: "POST",
    body: JSON.stringify({ api_key: apiKey }),
  });
}

export function downloadUrl(taskId: string, format: "html" | "excel") {
  return `${BASE}/api/tasks/${taskId}/download/${format}`;
}

export function chartUrl(taskId: string, name: string) {
  return `${BASE}/api/charts/${taskId}/${name}`;
}
