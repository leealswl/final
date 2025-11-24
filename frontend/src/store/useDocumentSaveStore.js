import { create } from 'zustand';

export const useDocumentSaveStore = create((set, get) => ({
    projectIdx: null,
    documentIdx: null,
    fileName: '',

    content: null,        // TipTap JSON
    isDirty: false,       // 수정됨 여부

    saving: false,        // 서버 저장 중
    saveError: null,      // 마지막 에러
    lastSavedAt: null,    // 마지막 저장 시각

    setMeta: ({ projectIdx, documentIdx, fileName }) =>
        set(() => ({
        projectIdx,
        documentIdx,
        fileName: fileName || '',
        })),

    setContent: (content) =>
        set(() => ({
        content,
        isDirty: true,
        })),

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
    }));
