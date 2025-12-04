import { create } from "zustand";
import { draftApi } from "../utils/draftApi";
import { tiptapDocToPlainText } from "../utils/tiptapText";
import { verifyLawSection } from "../utils/fastapi";
import { compareDraft } from "../utils/compareDraft";

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
      "본 사업이 일반회계 비R&D 사업임을 고려할 때, 총사업비(국고, 지자체, 자부담 등)와 예산 편성이 관련 법령·지침에 부합하는지, 인건비·용역비·운영비 등 항목별 계상과 산정 근거가 타당한지, 기술료·간접비 등 편성 제한 사항을 준수했는지 검토하세요.",
  },
  {
    key: "structure",
    label: "수행체계·역할·참여제한",
    focus:
      "주관기관·참여기관·협력기관 등의 역할과 책임이 공고문 및 관련 규정에 따라 명확히 정의되어 있는지, 참여제한·중복참여 제한·격리의무 등 규정을 위반할 소지가 없는지 검토하세요.",
  },
  {
    key: "outcome",
    label: "성과목표·지표·평가·사후관리",
    focus:
      "사업 성과목표와 성과지표가 공고문에서 요구하는 목표·지표 체계와 일치하는지, 성과 평가 방식과 성과관리·사후관리(성과 공유·확산, 유지관리 계획 등)가 관련 지침에 맞게 구체적으로 설계되어 있는지 검토하세요.",
  },
];

export const useVerifyStore = create((set, get) => ({
  loading: false,
  progress: 0,

  text: "",
  draftJson: null,

  results: {},          // 법령 검증 결과
  compareResult: null,  // 공고문 비교 결과

  activeTab: null,      // 'law' | 'compare' | null

  // ===== 액션 =====
  setActiveTab: (tab) => set({ activeTab: tab }),

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

  // 🔹 법령 검증 전체 실행
  verifyAll: async () => {
    const { text } = get();
    if (!text) {
      alert("초안이 없습니다.");
      console.error("[verifyAll] text 없음");
      return;
    }

    set({ activeTab: "law", loading: true, progress: 0 });

    const total = FOCUSES.length;
    let count = 0;

    const settled = await Promise.allSettled(
      FOCUSES.map(async (f) => {
        const res = await verifyLawSection({ text, focus: f.focus });

        count += 1;
        set({ progress: Math.round((count / total) * 100) });

        return { key: f.key, label: f.label, data: res.data };
      })
    );

    const next = {};
    settled.forEach((res, idx) => {
      const f = FOCUSES[idx];

      if (res.status === "fulfilled") {
        next[f.key] = {
          label: f.label,
          ...res.value.data,
        };
      } else {
        next[f.key] = {
          label: f.label,
          status: "error",
          risk_level: "UNKNOWN",
          reason: "검증 과정 중 오류 발생",
        };
      }
    });

    set({ results: next });

    setTimeout(() => {
      set({ loading: false });
    }, 300);
  },

  // 🔹 공고문 비교 실행 (초안 검증)
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

    const result = await compareDraft(projectIdx, draftJson); // res.data 리턴됨
    console.log("[compareAll] compareDraft 결과:", result);

    // 🔴 여기서 status 체크
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
}));
