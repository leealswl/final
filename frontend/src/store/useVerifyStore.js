import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { draftApi } from "../utils/draftApi";
import { tiptapDocToPlainText } from "../utils/tiptapText";
import { verifyLawSection, evaluateNoticeCriteria, runFullVerify as runFullVerifyApi } from "../utils/fastapi";
import { compareDraft } from "../utils/compareDraft";

/**
 * 법령 검증 관점
 */
export const FOCUSES = [
  {
    key: "purpose",
    label: "사업 목적·필요성·정책부합성",
    focus:
      "본 사업의 목적과 추진 배경이 공고문에서 제시한 추진목적·세부목표 및 관련 정책 방향(디지털정부, 행정 효율화, 국민 편익 제고 등)과 정합적인지 검토하세요.",
  },
  {
    key: "budget",
    label: "사업비·예산 편성",
    focus:
      "본 사업이 정보통신진흥기금 기반 일반회계 비R&D 사업임을 고려할 때, 총사업비(국고, 지자체, 자부담 등)와 예산 편성이 관련 법령·지침에 부합하는지, 인건비·용역비·운영비 등 항목별 계상과 산정 근거가 타당한지, 기술료·간접비 등 편성 제한 사항을 준수했는지 검토하세요.",
  },
  {
    key: "structure",
    label: "수행체계·역할·참여제한",
    focus:
      "주관기관·참여기관·협력기관 등의 역할과 책임이 공고문 및 관련 기금사업 관리지침에 따라 명확히 정의되어 있는지, 참여제한·중복참여 제한·격리의무 등 규정을 위반할 소지가 없는지 검토하세요.",
  },
  {
    key: "outcome",
    label: "성과목표·지표·평가·사후관리",
    focus:
      "사업 성과목표와 성과지표가 공고문에서 요구하는 목표·지표 체계와 일치하는지, 성과 평가 방식과 성과관리·사후관리(성과 공유·확산, 유지관리 계획 등)가 관련 지침에 맞게 구체적으로 설계되어 있는지 검토하세요.",
  },
];

export const useVerifyStore = create(
  persist(
    (set, get) => ({
  loading: false,
  progress: 0,

  text: "",
  draftJson: null,

  // key: FOCUSES.key
  results: {}, // 법령 검증 결과
  compareResult: null, // 공고문 비교 결과

  // 🔥 공고문 평가기준 자가진단 결과
  noticeEvalResult: null,

  activeTab: null, // 'law' | 'compare' | null

  // ===== 액션 =====
  setActiveTab: (tab) => set({ activeTab: tab }),

  // 전체 초기화가 필요하면 쓸 수 있게
  resetVerifyState: () =>
    set({
      results: {},
      compareResult: null,
      noticeEvalResult: null,
      activeTab: null,
      progress: 0,
    }),

  // 🔹 초안 로딩
  loadDraft: async (filePath) => {
    if (!filePath) return;

    try {
      console.log("[loadDraft] filePath:", filePath);
      const docJson = await draftApi(filePath);
      const plain = tiptapDocToPlainText(docJson);

      set({
        draftJson: docJson,
        text: plain,
      });
    } catch (e) {
      console.error("초안 JSON 불러오기 실패:", e);
    }
  },

  // 🔹 법령 검증 전체 실행 (FOCUSES 기반)
  verifyAll: async () => {
    const { text } = get();
    if (!text) {
      alert("초안이 없습니다.");
      console.error("[verifyAll] text 없음");
      return;
    }

    set({ activeTab: "law", loading: true, progress: 0 });

    const total = FOCUSES.length;
    const next = {};

    for (let i = 0; i < total; i++) {
      const f = FOCUSES[i];

      try {
        const law = await verifyLawSection({
          text,
          focus: f.focus,
        });

        console.log("[verifyAll] law result for", f.key, law);

        next[f.key] = {
          label: f.label,
          ...law, // ✅ 여기서 status, reason, violations 등이 바로 들어감
        };
      } catch (e) {
        console.error(`verifyLawSection error for ${f.key}:`, e);

        next[f.key] = {
          label: f.label,
          status: "error",
          risk_level: "UNKNOWN",
          reason: "검증 과정 중 오류가 발생했습니다.",
          missing: [],
          suggestion: "",
          violation_judgment: "UNCLEAR",
          violation_summary: "",
          violations: [],
          related_laws: [],
        };
      }

      set({ progress: Math.round(((i + 1) / total) * 100) });
    }

    console.log("[verifyAll] final results:", next);

    set({ results: next, loading: false });
  },


  // 🔹 공고문 비교 실행 (초안 vs 공고문 요구사항)
  compareAll: async (projectIdx) => {
    const { draftJson } = get();

    if (!draftJson) {
      alert("초안 JSON이 없습니다.");
      console.error("[compareAll] draftJson 없음");
      return;
    }

    if (!projectIdx) {
      alert("프로젝트 정보(projectIdx)가 없습니다.");
      console.error("[compareAll] projectIdx 없음:", projectIdx);
      return;
    }

    console.log("[compareAll] 실행, projectIdx:", projectIdx, draftJson);

    set({ activeTab: "compare", loading: true, progress: 10 });

    try {
      set({ progress: 40 });

      // utils/compareDraft 에서 res.data를 리턴한다고 가정
      const result = await compareDraft(projectIdx, draftJson);
      console.log("[compareAll] compareDraft 결과:", result);

      if (result.status === "error") {
        alert(result.message || "초안 비교 중 오류가 발생했습니다. (서버 응답)");
        console.error("[compareAll] 서버 도메인 에러:", result);
        return;
      }

      set({
        compareResult: result,
        progress: 100,
      });
    } catch (e) {
      console.error(
        "❌ 초안 비교 오류 (compareAll):",
        e.response?.data || e.message || e
      );
      alert("초안 비교 중 서버 오류가 발생했습니다. 콘솔을 확인해주세요.");
    } finally {
      setTimeout(() => set({ loading: false }), 300);
    }
  },

  // 🔹 공고문 “평가기준” 기반 자가진단 실행
  runNoticeEvaluation: async (projectIdx) => {
    const { text } = get();

    if (!text) {
      alert("초안이 없습니다.");
      console.error("[runNoticeEvaluation] text 없음");
      return;
    }

    if (!projectIdx) {
      alert("프로젝트 정보(projectIdx)가 없습니다.");
      console.error("[runNoticeEvaluation] projectIdx 없음:", projectIdx);
      return;
    }

    try {
      // 탭은 굳이 바꾸지 않고, 로딩만 공유
      set({ loading: true });

      const res = await evaluateNoticeCriteria({ projectIdx, text });
      console.log("[runNoticeEvaluation] 결과:", res);

      if (res.status !== "success") {
        alert(
          res.message ||
            "공고 평가기준 자가진단 중 오류가 발생했습니다. (서버 응답)"
        );
        console.error("[runNoticeEvaluation] 서버 응답 에러:", res);
        return;
      }

      // 🔥 종합 리포트에서 쓸 수 있도록 결과 저장
      set({ noticeEvalResult: res.data });
    } catch (e) {
      console.error(
        "❌ 공고 평가기준 자가진단 오류 (runNoticeEvaluation):",
        e.response?.data || e.message || e
      );
      alert(
        "공고 평가기준 자가진단 중 서버 오류가 발생했습니다. 콘솔을 확인해주세요."
      );
    } finally {
      set({ loading: false });
    }
  },

  // 통합 검증 (공고문 비교 + 법령 다중 포커스 + 평가기준)
  runFullVerify: async (projectIdx) => {
    const { draftJson } = get();

    if (!draftJson) {
      alert("초안 JSON이 없습니다.");
      console.error("[runFullVerify] draftJson 없음");
      return;
    }

    if (!projectIdx) {
      alert("프로젝트 정보(projectIdx)가 없습니다.");
      console.error("[runFullVerify] projectIdx 없음:", projectIdx);
      return;
    }

    const focusKeys = FOCUSES.map((f) => f.key);

    try {
      set({ loading: true, progress: 10, activeTab: "law" });

      const res = await runFullVerifyApi({
        projectIdx,
        draftJson,
        lawFocuses: focusKeys,
      });

      if (res.status !== "success") {
        alert(res.message || "통합 검증 중 오류가 발생했습니다.");
        console.error("[runFullVerify] server error:", res);
        return;
      }

      const data = res.data || {};
      const lawResults = data.law_results || {};

      const mappedResults = {};
      FOCUSES.forEach((f) => {
        mappedResults[f.key] = {
          label: f.label,
          ...(lawResults[f.key] || {}),
        };
      });

      set({
        results: mappedResults,
        compareResult: data.compare_result || null,
        noticeEvalResult: data.notice_result || null,
        progress: 100,
      });
    } catch (e) {
      console.error("[runFullVerify] error:", e.response?.data || e.message || e);
      alert("통합 검증 중 서버 오류가 발생했습니다. 콘솔을 확인해 주세요.");
    } finally {
      set({ loading: false });
    }
  },
    }),
    {
      name: "verify-cache",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        text: state.text,
        draftJson: state.draftJson,
        results: state.results,
        compareResult: state.compareResult,
        noticeEvalResult: state.noticeEvalResult,
        activeTab: state.activeTab,
      }),
    }
  )
);
