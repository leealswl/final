import { create } from "zustand";
import api from "../utils/api";

export const useDocumentStore = create((set, get) => ({
  documentId: null,
  content: null,
  status: "idle",
  error: null,

  setDocumentId: (id) => set({ documentId: id }),
  setContent: (content) => set({ content }),

  loadDocument: async (id) => {
    const targetId = id ?? get().documentId;
    if (!targetId) throw new Error("문서 ID가 설정되어 있지 않습니다.");

    set({ status: "loading", error: null, documentId: targetId });
    try {
      const { data } = await api.get(`/api/document/${targetId}/content`);
      const content = data?.content || null;
      set({ content, status: "success" });
      return content;
    } catch (error) {
      set({ status: "error", error: error.message });
      throw error;
    }
  },

  saveDocument: async ({ id, content } = {}) => {
    const targetId = id ?? get().documentId;
    const payload = content ?? get().content;
    if (!targetId) throw new Error("문서 ID가 설정되어 있지 않습니다.");
    if (!payload) throw new Error("저장할 문서 내용이 없습니다.");

    set({ status: "saving", error: null });
    try {
      await api.post(`/api/document/${targetId}/content`, { content: payload });
      set({ status: "success" });
    } catch (error) {
      set({ status: "error", error: error.message });
      throw error;
    }
  },
}));
