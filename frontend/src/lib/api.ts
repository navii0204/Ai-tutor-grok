import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL: `${BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// ── Types ──────────────────────────────────────────────────────────────────────

export interface StudentSummary {
  id: string;
  name: string;
  grade: string;
  segment: string;
  external_id: string;
}

export interface ConceptSummary {
  id: string;
  name: string;
  subject: string;
  grade: string;
}

// ── Student ────────────────────────────────────────────────────────────────────

export async function getStudentProfile(studentId: string) {
  const { data } = await api.get(`/student/profile/${studentId}`);
  return data;
}

export async function getDailyPlan(studentId: string) {
  const { data } = await api.get(`/student/daily-plan/${studentId}`);
  return data;
}

export async function sendChatMessage(payload: {
  student_id: string;
  concept_id: string;
  message: string;
  history: Array<{ role: string; content: string }>;
  session_id?: string;
}) {
  const { data } = await api.post("/student/chat", payload);
  return data as {
    response: string;
    is_question: boolean;
    focus_cue: string | null;
    reflection_prompt: string | null;
    mastery_delta: number;
  };
}

export async function simulatorCommand(payload: {
  student_id: string;
  simulator_id: string;
  command: string;
  params?: Record<string, unknown>;
  config?: Record<string, unknown>;
}) {
  const { data } = await api.post("/student/simulator/command", payload);
  return data;
}

export async function listStudents(tenantId = "demo-school-001"): Promise<StudentSummary[]> {
  const { data } = await api.get("/student/list", { params: { tenant_id: tenantId } });
  return data.students;
}

export async function listConcepts(segment: string): Promise<ConceptSummary[]> {
  const { data } = await api.get(`/admin/curriculum/${segment}/concepts`);
  return data.concepts ?? [];
}

export async function sendChatMessageStream(
  payload: {
    student_id: string;
    concept_id: string;
    message: string;
    history: Array<{ role: string; content: string }>;
    session_id?: string;
  },
  onChunk: (char: string) => void,
  onDone: () => void,
): Promise<void> {
  const res = await fetch(`${BASE}/api/v1/student/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.body) { onDone(); return; }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    for (const line of decoder.decode(value).split("\n")) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();
      if (data === "[DONE]") { onDone(); return; }
      try {
        const parsed = JSON.parse(data);
        if (parsed.char) onChunk(parsed.char);
      } catch { /* skip malformed SSE lines */ }
    }
  }
  onDone();
}

// ── Teacher ───────────────────────────────────────────────────────────────────

export async function getClassroomInsights(tenantId: string, grade: string) {
  const { data } = await api.get(`/teacher/classroom/${tenantId}/grade/${grade}/insights`);
  return data;
}

export async function generateLessonPlan(payload: {
  concept_id: string;
  grade: string;
  segment: string;
  duration_minutes: number;
}) {
  const { data } = await api.post("/teacher/lesson-plan", payload);
  return data;
}
