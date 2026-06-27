import { create } from "zustand";

interface Message {
  role: "student" | "tutor";
  content: string;
  focus_cue?: string | null;
  reflection_prompt?: string | null;
}

interface SessionState {
  studentId: string;
  sessionId: string | null;
  conceptId: string;
  messages: Message[];
  isLoading: boolean;
  setStudentId: (id: string) => void;
  setConceptId: (id: string) => void;
  setSessionId: (id: string) => void;
  addMessage: (msg: Message) => void;
  setLoading: (v: boolean) => void;
  clearMessages: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  studentId: "6d8ea3f0-8049-48be-a854-26af4f4fa12c",  // Arjun Sharma (seeded)
  sessionId: null,
  conceptId: "sci_photosynthesis",
  messages: [],
  isLoading: false,
  setStudentId: (id) => set({ studentId: id }),
  setConceptId: (id) => set({ conceptId: id, messages: [] }),
  setSessionId: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading: (v) => set({ isLoading: v }),
  clearMessages: () => set({ messages: [] }),
}));
