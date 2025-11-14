// store/useProjectStore.js
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export const useProjectStore = create(
    persist(
        (set) => ({
            project: null,
            setProject: (data) => set({ project: data }),
            clearProject: () => set({ project: null }),
        }),
        {
            name: 'project-store',
            storage: createJSONStorage(() => sessionStorage),
            partialize: (state) => ({ project: state.project }),
        },
    ),
);
