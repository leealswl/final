import { create } from 'zustand';
import api from '../utils/api';

export const useDocumentStore = create((set, get) => ({
    content: null,
    status: 'idle',
    error: null,
    saveTimer: null,

    userId: null,
    projectIdx: null,
    documentIdx: null,
    fileName: '',
    filePath: null,
    folder: 0,

    isDirty: false, // 수정됨 여부

    saving: false, // 서버 저장 중
    saveError: null, // 마지막 에러
    lastSavedAt: null, // 마지막 저장 시각

    setUserId: (userid) => set({ userId: userid }),
    setProjectIdx: (projectidx) => set({ projectIdx: projectidx }),

    setMeta: ({ projectIdx, documentIdx, fileName, filePath }) =>
        set(() => ({
            projectIdx,
            documentIdx,
            fileName: fileName || '',
            filePath,
        })),
    setContent: (content, shouldSave = true) => {
        set({ content });

        // shouldSave가 false면 저장하지 않음
        if (!shouldSave) return;

        const { saveTimer } = get();
        if (saveTimer) clearTimeout(saveTimer);

        // 저장 예약
        const newTimer = setTimeout(() => {
            get()
                .saveDocument()
                .catch(() => {});
        }, 1500);

        set({ saveTimer: newTimer });
    },
    setSaving: (saving) =>
        set(() => ({
            saving,
            ...(saving ? { saveError: null } : {}),
        })),

    markSaved: () =>
        set(() => ({
            isDirty: false,
            saving: false,
            saveError: null,
            lastSavedAt: new Date(),
        })),

    setSaveError: (errorMessage) =>
        set(() => ({
            saving: false,
            saveError: errorMessage || '저장 중 오류가 발생했습니다.',
        })),

    resetDocument: () =>
        set(() => ({
            projectIdx: null,
            documentIdx: null,
            fileName: '',
            content: null,
            isDirty: false,
            saving: false,
            saveError: null,
            lastSavedAt: null,
        })),

    loadDocument: async (id) => {
        const targetId = id ?? get().documentId;
        if (!targetId) throw new Error('문서 ID가 설정되어 있지 않습니다.');

        set({ status: 'loading', error: null, documentId: targetId });
        try {
            const { data } = await api.get(`/api/documents/${targetId}/content`);
            const content = data?.content || null;
            set({ content, status: 'success' });
            return content;
        } catch (error) {
            set({ status: 'error', error: error.message });
            throw error;
        }
    },

    saveDocument: async ({ content } = {}) => {
        // const targetId = id ?? get().documentId;
        const payload = content ?? get().content;
        // if (!targetId) throw new Error('문서 ID가 설정되어 있지 않습니다.');
        if (!payload) throw new Error('저장할 문서 내용이 없습니다.');
        const userId = get().userId;
        const projectIdx = get().projectIdx;

        console.log('[DEBUG] AutoSave 요청 발생', payload);

        set({ status: 'saving', error: null });
        try {
            // await api.post(`/api/documents/${targetId}/content`, { content: payload });
            await api.post(`/api/documents/${userId}/${projectIdx}/content`, { content: payload });
            set({ status: 'success' });
        } catch (error) {
            set({ status: 'error', error: error.message });
            throw error;
        }
    },
}));
