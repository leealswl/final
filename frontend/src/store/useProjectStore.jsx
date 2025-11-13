// store/useProjectStore.js
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useProjectStore = create(
    persist(
        (set) => ({
            project: null,
            setProject: (data) => set({ project: data }),
            clearProject: () => set({ project: null }),
        }),
        { name: 'project-store' }, // localStorage에 저장
    ),
);
