import { create } from 'zustand';

/**
 * 2025-11-17: 레이아웃 상태 관리 Store
 * - 좌측 사이드바 토글 상태
 * - 페이지별로 독립적인 토글 상태 관리
 */
export const useLayoutStore = create((set) => ({
    // 사이드바 열림/닫힘 상태 (기본값: true)
    sidebarOpen: true,
    
    // 사이드바 토글
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    
    // 사이드바 열기
    openSidebar: () => set({ sidebarOpen: true }),
    
    // 사이드바 닫기
    closeSidebar: () => set({ sidebarOpen: false }),
}));










