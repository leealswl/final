export const FEATURE_EXCLUDE_KEYWORDS = [
  "문의처", "담당자", "전화번호", "이메일", "홈페이지",
  "공고기관", "공고일", "접수기관",
  "접수시간", "접수기간", "신청기간",
  "신청방법", "신청방법 및 신청기간", "지원방법",
  "지원규모", "선정절차", "평가기준", "관련법령",
  "추출된",
  "초안", "사업계획서", "사업계획서목차", "사업계획서 작성요령",
  "사업계획서작성요령", "작성요령", "제출서류", "제출 양식",
  "제출양식", "작성 서식", "작성 예시", "작성 방법",
  "기술제안서", "제안요청서",
];

// Feature 병합 규칙
export const FEATURE_MERGE_RULES = [
  {
    canonical: "사업기간",
    keywords: ["사업기간", "주요 추진일정", "공공AX 프로젝트 사업기간"],
  },
];

// 라벨 통합 함수
export function normalizeFeatureLabel(rawLabel) {
  for (const rule of FEATURE_MERGE_RULES) {
    if (rule.keywords.some((kw) => rawLabel.includes(kw))) {
      return rule.canonical;
    }
  }
  return rawLabel;
}

// Feature 리스트 정제
export function buildNormalizedMissingFeatureList(rawList = []) {
  const result = [];

  rawList.forEach((item) => {
    const rawLabel = typeof item === "string" ? item : String(item ?? "");

    if (FEATURE_EXCLUDE_KEYWORDS.some((kw) => rawLabel.includes(kw))) return;

    const label = normalizeFeatureLabel(rawLabel);
    if (!result.includes(label)) result.push(label);
  });

  return result;
}
