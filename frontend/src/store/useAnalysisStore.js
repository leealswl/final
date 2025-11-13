import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

/**
 * 2025-11-09 suyeon: 분석 결과를 페이지 간 공유하기 위한 전역 스토어
 * - AnalyzeView → Dashboard/CreateView 간 analysisResult 전달
 * - sessionStorage 기반으로 새로고침 시에도 유지
 */
export const useAnalysisStore = create(
  persist(
    (set) => ({
      analysisResult: null,
      userInputData: null,

      setAnalysisResult: (result) => set({ analysisResult: result }),
      clearAnalysisResult: () => set({ analysisResult: null }),

      setUserInputData: (data) => set({ userInputData: data }),
      clearUserInputData: () => set({ userInputData: null })
    }),
    {
      name: 'analysis-result-store',
      storage: createJSONStorage(() => sessionStorage)
    }
  )
)

