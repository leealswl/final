import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
    persist(
        (set, get) => ({
            user: null, // { userId, username } 또는 null
            setUser: (user) => set({ user }),
            clear: () => set({ user: null }), //로그아웃 여부
            isAuthed: () => !!get().user, // 파생 상태(로그인 여부)
        }),
        {
            name: 'auth-store', // localStorage key
            partialize: (state) => ({ user: state.user }), // user만 저장
        },
    ),
);
