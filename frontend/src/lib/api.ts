const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

export type Account = {
  id: number;
  email: string;
  is_active: boolean;
  email_verified_at: string | null;
};

export type Profile = {
  full_name: string | null; phone: string | null; location: string | null;
  linkedin_url: string | null; github_url: string | null; portfolio_url: string | null; summary: string | null;
  preferred_titles: string[]; preferred_locations: string[]; work_modes: string[]; employment_types: string[];
  skills: { name: string; category: string }[];
  educations: { degree: string; institution: string; specialization: string | null; graduation_year: number | null; score: string | null }[];
  experiences: { company: string; position: string; start_date: string | null; end_date: string | null; is_current: boolean; description: string | null }[];
  projects: { name: string; description: string | null; technologies: string[]; url: string | null }[];
};

export type Job = {
  id: number; title: string; company: string; location: string | null; work_mode: string | null;
  employment_type: string | null; salary: string | null; description: string; url: string | null;
  source: string; status: string; is_saved: boolean; match_score: number | null; created_at: string;
};

export type ApplicationEvent = { id: number; previous_status: string | null; new_status: string; note: string | null; source: string; created_at: string };
export type Application = { id: number; status: string; applied_at: string | null; notes: string | null; resume_version_id: number | null; resume_version: {id:number;version:number;matched_keywords:string[];created_at:string}|null; created_at: string; job: Job; events: ApplicationEvent[] };
export type DashboardMetrics = { jobs_added: number; saved_jobs: number; applications: number; submitted: number; interviews: number; response_rate: number | null; has_master_resume: boolean; profile_complete: boolean; upcoming_actions: unknown[] };
export type Integration = { id: string; name: string; status: string; connected: boolean; account?: string|null; last_synced_at?: string|null; message: string };
export type MailEvent={id:number;sender:string|null;subject:string|null;received_at:string|null;classification:string;reviewed:boolean};
export type CalendarEntry={id:number;summary:string;organizer:string|null;starts_at:string;ends_at:string|null};

export const applicationStatuses = [
  "Discovered", "Saved", "Viewed", "Application Started", "Resume Prepared", "Ready for Review",
  "Submitted", "Submission Confirmed", "Submission Unverified", "Under Review", "Assessment Invited",
  "Assessment Completed", "Interview Scheduled", "Interview Completed", "Rejected", "Offer Received",
  "Offer Accepted", "Offer Declined", "Withdrawn", "Closed",
];

type SessionResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
};

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        ...(typeof init.body === "string" ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new Error("Can’t reach the ApplyTrack API. Check that the backend is running and its URL is configured.");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${response.status}). Please try again.`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function register(email: string, password: string) {
  return request<SessionResponse>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
}

export async function login(email: string, password: string) {
  return request<SessionResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export async function getAccount(token: string) {
  return request<Account>("/auth/me", {}, token);
}

export async function logout(token: string) {
  return request<void>("/auth/logout", { method: "POST" }, token);
}

export async function getProfile(token: string) { return request<Profile>("/profile", {}, token); }
export async function saveProfile(token: string, profile: Profile) { return request<Profile>("/profile", { method: "PUT", body: JSON.stringify(profile) }, token); }
export async function getDashboard(token: string) { return request<DashboardMetrics>("/dashboard", {}, token); }
export async function getJobs(token: string, query = "") { return request<Job[]>(`/jobs${query ? `?q=${encodeURIComponent(query)}` : ""}`, {}, token); }
export async function createJob(token: string, job: Partial<Job>) { return request<Job>("/jobs", { method: "POST", body: JSON.stringify(job) }, token); }
export async function setJobSaved(token: string, id: number, saved: boolean) { return request<Job>(`/jobs/${id}/saved?saved=${saved}`, { method: "PATCH" }, token); }
export async function getApplications(token: string) { return request<Application[]>("/applications", {}, token); }
export async function createApplication(token: string, job_id: number, resume_version_id?: number) { return request<Application>("/applications", { method: "POST", body: JSON.stringify({ job_id, status: "Discovered", resume_version_id }) }, token); }
export async function updateApplication(token: string, id: number, body: { status?: string; notes?: string | null }) { return request<Application>(`/applications/${id}`, { method: "PATCH", body: JSON.stringify(body) }, token); }
export async function addApplicationNote(token: string, id: number, note: string) { return request<Application>(`/applications/${id}/events`, { method: "POST", body: JSON.stringify({ note }) }, token); }
export async function getIntegrations(token: string) { return request<{ items: Integration[] }>("/integrations/status", {}, token); }
export async function getResume(token: string) { return request<{ file_name: string; file_type: string; uploaded_at: string; text_extracted: boolean }>("/resume", {}, token); }
export async function getResumeText(token: string) { return request<{ text: string }>("/resume/extracted-text", {}, token); }
export async function uploadResume(token: string, file: File) {
  const body = new FormData(); body.append("file", file);
  return request<{ file_name: string; file_type: string; uploaded_at: string; text_extracted: boolean }>("/resume", { method: "POST", body }, token);
}
export async function downloadResume(token: string) {
  let response: Response;
  try { response = await fetch(`${API_BASE}/resume/download`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" }); }
  catch { throw new Error("Can’t reach the ApplyTrack API. Check that the backend is running and its URL is configured."); }
  if (!response.ok) throw new Error(`Resume download failed (${response.status})`);
  return response.blob();
}
export async function deleteResume(token: string) { return request<void>("/resume", { method: "DELETE" }, token); }
export type MatchResult={match_score:number|null;category:string;matched_skills:string[];missing_skills:string[];mandatory_skill_gaps:string[];recommendation:string;components:Record<string,number>};
export type GeneratedResume={id:number;version:number;job_id:number;job_title:string;company:string;matched_keywords:string[];match_score_at_creation:number|null;created_at:string};
export async function matchJob(token:string,id:number){return request<MatchResult>(`/jobs/${id}/match`,{},token)}
export async function generateResume(token:string,id:number){return request<GeneratedResume>(`/jobs/${id}/resume-versions`,{method:"POST"},token)}
export async function getResumeVersions(token:string,id:number){return request<GeneratedResume[]>(`/jobs/${id}/resume-versions`,{},token)}
export async function downloadGeneratedResume(token:string,id:number,format:"pdf"|"docx"){
  let response:Response;
  try{response=await fetch(`${API_BASE}/resume-versions/${id}/download?format=${format}`,{headers:{Authorization:`Bearer ${token}`},cache:"no-store"})}
  catch{throw new Error("Can’t reach the ApplyTrack API. Check that the backend is running and its URL is configured.")}
  if(!response.ok)throw new Error(`Resume download failed (${response.status})`);
  return response.blob();
}
export async function startGoogleConnection(token:string,service:"gmail"|"calendar"){return request<{authorization_url:string}>(`/integrations/google/start?service=${service}`,{method:"POST"},token)}
export async function syncGoogleService(token:string,service:"gmail"|"calendar"){return request<{checked:number;new_events:number}>(`/integrations/${service}/sync`,{method:"POST"},token)}
export async function disconnectGoogleService(token:string,service:"gmail"|"calendar"){return request<{disconnected:boolean}>(`/integrations/${service}`,{method:"DELETE"},token)}
export async function getMailEvents(token:string){return request<MailEvent[]>("/integrations/gmail/events",{},token)}
export async function confirmMailEvent(token:string,eventId:number,applicationId:number,status:string){return request<{status:string;reviewed:boolean}>(`/integrations/gmail/events/${eventId}/confirm?application_id=${applicationId}&new_status=${encodeURIComponent(status)}`,{method:"POST"},token)}
export async function getCalendarEvents(token:string){return request<CalendarEntry[]>("/integrations/calendar/events",{},token)}
