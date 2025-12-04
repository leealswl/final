import React, { useMemo } from "react";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Typography,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Button,
  Divider,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

import { useProjectStore } from "../../../store/useProjectStore";
import { useVerifyStore } from "../../../store/useVerifyStore";
import { useNavigate } from "react-router-dom";

// 색상 상수
const STATUS_COLORS = { 적합: "#4caf50", 보완: "#ffb300", 부적합: "#f44336" };
const SEVERITY_COLORS = { LOW: "#4caf50", MEDIUM: "#ffb300", HIGH: "#f44336" };

// 🔹 사용자에게 보여줄 한글 라벨
const SEVERITY_LABELS = {
  LOW: "위험도 낮음",
  MEDIUM: "위험도 보통",
  HIGH: "위험도 높음",
};

const FEATURE_EXCLUDE_KEYWORDS = [
  // 문의/연락/담당자 정보
  "문의처",
  "담당자",
  "전화번호",
  "이메일",
  "홈페이지",

  // 공고/기관/접수 장소 정보
  "공고기관",
  "공고일",
  "접수기관",

  // 접수/신청 관련 (기간/방법)
  "접수시간",
  "접수기간",
  "신청기간",
  "신청방법",
  "신청방법 및 신청기간",
  "지원방법",

  // 안내용 정보 (규모/절차/기준/법령)
  "지원규모",
  "선정절차",
  "평가기준",
  "관련법령",

  // "추출된 공고기관" 같은 거 제거
  "추출된",

  // 🔥 초안/작성요령/목차 같은 메타 정보
  "초안",
  "사업계획서",
  "사업계획서목차",
  "사업계획서 작성요령",
  "사업계획서작성요령",
  "작성요령",
  "제출서류",
  "제출 양식",
  "제출양식",
  "작성 서식",
  "작성 예시",
  "작성 방법",
  "기술제안서",
  "제안요청서",
];

// ✅ 비슷한 의미의 Feature를 하나로 묶기 위한 규칙
//   - 사업기간 / 2025년 공공AX 프로젝트 사업기간 / 주요 추진일정 → "사업기간" 하나로
const FEATURE_MERGE_RULES = [
  {
    canonical: "사업기간",
    keywords: ["사업기간", "주요 추진일정"],
  },
];

// 라벨 정규화 (예: "2025년 공공AX 프로젝트 사업기간" → "사업기간")
const normalizeFeatureLabel = (rawLabel) => {
  for (const rule of FEATURE_MERGE_RULES) {
    if (rule.keywords.some((kw) => rawLabel.includes(kw))) {
      return rule.canonical;
    }
  }
  return rawLabel;
};

// feature_mismatch 배열을
// 1) EXCLUDE 키워드 제거
// 2) normalize 해서
// 3) 중복 제거한 문자열 배열로 만드는 헬퍼
const buildNormalizedMissingFeatureList = (rawList = []) => {
  const result = [];
  rawList.forEach((item) => {
    const rawLabel = typeof item === "string" ? item : String(item ?? "");
    if (FEATURE_EXCLUDE_KEYWORDS.some((kw) => rawLabel.includes(kw))) {
      return;
    }
    const label = normalizeFeatureLabel(rawLabel);
    if (!result.includes(label)) {
      result.push(label);
    }
  });
  return result;
};

// =======================================================
// 🔍 리포트 상단: 요약 카드들 (최종 정리본)
// =======================================================
function SummaryHeader({ results, compareResult }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;

  // 🔹 법령 쪽 요약 계산
  const lawSummary = useMemo(() => {
    if (!hasLaw) return null;

    const entries = Object.entries(results);
    const STATUS_ORDER = { 적합: 1, 보완: 2, 부적합: 3 };
    const RISK_ORDER = { LOW: 1, MEDIUM: 2, HIGH: 3 };
    const SEVERITY_ORDER = { LOW: 1, MEDIUM: 2, HIGH: 3 };

    const statusCounts = { 적합: 0, 보완: 0, 부적합: 0 };
    let worstRisk = null;
    let worstViolSeverity = null;

    entries.forEach(([, r]) => {
      if (!r) return;

      if (r.status && statusCounts[r.status] !== undefined) {
        statusCounts[r.status] += 1;
      }

      if (r.risk_level) {
        if (!worstRisk) worstRisk = r.risk_level;
        else if (RISK_ORDER[r.risk_level] > RISK_ORDER[worstRisk]) {
          worstRisk = r.risk_level;
        }
      }

      if (Array.isArray(r.violations)) {
        r.violations.forEach((v) => {
          const sev = v.severity || "MEDIUM";
          if (!worstViolSeverity) worstViolSeverity = sev;
          else if (SEVERITY_ORDER[sev] > SEVERITY_ORDER[worstViolSeverity]) {
            worstViolSeverity = sev;
          }
        });
      }
    });

    const sorted = entries.sort(([, a], [, b]) => {
      const aStatus = a?.status || "적합";
      const bStatus = b?.status || "적합";
      const aRisk = a?.risk_level || "LOW";
      const bRisk = b?.risk_level || "LOW";

      const statusDiff = STATUS_ORDER[bStatus] - STATUS_ORDER[aStatus];
      if (statusDiff !== 0) return statusDiff;

      return RISK_ORDER[bRisk] - RISK_ORDER[aRisk];
    });

    const overallStatus = sorted[0]?.[1]?.status || null;

    return {
      statusCounts,
      overallStatus,
      overallRisk: worstRisk,
      overallViolationSeverity: worstViolSeverity,
    };
  }, [results, hasLaw]);

  // 🔹 공고문 비교 요약 계산 (백엔드 progress 사용)
  const compareSummary = useMemo(() => {
    if (!hasCompare) return null;

    const toc = compareResult?.toc_progress || {};
    const feat = compareResult?.feature_progress || {};

    const tocPercent =
      typeof toc.progress_percent === "number" ? toc.progress_percent : null;
    const featurePercent =
      typeof feat.progress_percent === "number" ? feat.progress_percent : null;

    let combined = 0;
    let count = 0;
    if (tocPercent !== null) {
      combined += tocPercent;
      count += 1;
    }
    if (featurePercent !== null) {
      combined += featurePercent;
      count += 1;
    }

    const combinedPercent = count > 0 ? Math.round(combined / count) : null;

    return {
      tocPercent,
      featurePercent,
      combinedPercent,
      tocCounts: {
        written: toc.written_sections ?? 0,
        total: toc.total_sections ?? 0,
      },
      featureCounts: {
        ok: feat.ok_features ?? 0,
        partial: feat.partial_features ?? 0,
        missing: feat.missing_features ?? 0,
      },
    };
  }, [compareResult, hasCompare]);

  const statusChartData =
    lawSummary &&
    Object.entries(lawSummary.statusCounts)
      .filter(([, count]) => count > 0)
      .map(([name, value]) => ({ name, value }));

  return (
    <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ mt: 3 }}>
      {/* 전체 요약 카드 */}
      <Card sx={{ flex: 1 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            전체 평가 요약
          </Typography>

          {!hasLaw && !hasCompare && (
            <Typography sx={{ mt: 1.5, color: "text.secondary" }}>
              아직 생성된 리포트가 없습니다. 먼저 검증 화면에서 법령 검증 또는
              초안 검증을 실행해 주세요.
            </Typography>
          )}

          {(hasLaw || hasCompare) && (
            <Stack spacing={1.5} sx={{ mt: 1.5 }}>
              {lawSummary && (
                <>
                  {/* 법령 판단 */}
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                      법령 판단
                    </Typography>
                    {lawSummary.overallStatus ? (
                      <Chip
                        label={lawSummary.overallStatus}
                        size="small"
                        color={
                          lawSummary.overallStatus === "적합"
                            ? "success"
                            : lawSummary.overallStatus === "보완"
                            ? "warning"
                            : "error"
                        }
                      />
                    ) : (
                      <Typography>-</Typography>
                    )}
                  </Stack>

                  {/* 리스크 */}
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                      리스크
                    </Typography>
                    {lawSummary.overallRisk ? (
                      <Chip
                        label={lawSummary.overallRisk}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      <Typography>-</Typography>
                    )}
                  </Stack>

                  {/* 법령 위반 가능성 */}
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                      법령 위반 가능성
                    </Typography>
                    {lawSummary.overallViolationSeverity ? (
                      <Chip
                        label={
                          SEVERITY_LABELS[lawSummary.overallViolationSeverity] ||
                          lawSummary.overallViolationSeverity
                        }
                        size="small"
                        variant="outlined"
                        sx={{
                          borderColor:
                            SEVERITY_COLORS[
                              lawSummary.overallViolationSeverity
                            ],
                          color:
                            SEVERITY_COLORS[
                              lawSummary.overallViolationSeverity
                            ],
                        }}
                      />
                    ) : (
                      <Typography>-</Typography>
                    )}
                  </Stack>
                </>
              )}

              {/* 공고문 충족률 */}
              {compareSummary && (
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                    공고문 충족률
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {compareSummary.combinedPercent ?? "-"}
                    {compareSummary.combinedPercent !== null && "%"}
                  </Typography>
                  <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                    {compareSummary.tocPercent !== null && (
                      <>
                        (목차 기준 {compareSummary.tocPercent}%{", "}
                      </>
                    )}
                    {compareSummary.featurePercent !== null && (
                      <>세부 요구사항 기준 {compareSummary.featurePercent}%</>
                    )}
                  </Typography>
                </Stack>
              )}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* 법령 상태 분포 + 공고문 차트 요약 */}
      {(lawSummary || compareSummary) && (
        <Card sx={{ width: { xs: "100%", md: 380 } }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
              검사 결과 분포
            </Typography>

            <Stack spacing={2}>
              {lawSummary && statusChartData && statusChartData.length > 0 && (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                  }}
                >
                  <PieChart width={220} height={200}>
                    <Pie
                      data={statusChartData}
                      dataKey="value"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={3}
                    >
                      {statusChartData.map((entry, idx) => (
                        <Cell
                          key={idx}
                          fill={STATUS_COLORS[entry.name] || "#999"}
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </Box>
              )}

              {compareSummary && (
                <Box sx={{ textAlign: "left" }}>
                  <Typography
                    variant="caption"
                    sx={{ color: "text.secondary" }}
                  >
                    공고문 비교 한 줄 요약
                  </Typography>
                  <Typography sx={{ fontSize: 14, mt: 0.5 }}>
                    공고문 형식 기준으로는{" "}
                    <b>{compareSummary.tocPercent ?? 0}%</b>, 세부 요구사항
                    기준으로는 <b>{compareSummary.featurePercent ?? 0}%</b>가
                    초안에 반영되어 있습니다.
                    <br />
                    두 관점을 평균한 전체 공고문 요구사항 충족률은{" "}
                    <b>
                      {compareSummary.combinedPercent ?? 0}
                      %
                    </b>
                    입니다.
                  </Typography>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Stack>
  );
}

// =======================================================
// 🧩 Top 3 보완 포인트 (법령 + 공고문 통합)
// =======================================================
function TopIssuesSection({ results, compareResult }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;

  const items = useMemo(() => {
    const list = [];

    // 1) 법령 쪽 missing + violations 요약
    if (hasLaw) {
      Object.entries(results).forEach(([key, r]) => {
        if (!r) return;

        if (Array.isArray(r.missing)) {
          r.missing.forEach((m) => {
            list.push({
              type: "LAW_MISSING",
              focusLabel: r.label,
              text: m,
              severity: r.risk_level || "MEDIUM",
            });
          });
        }

        if (Array.isArray(r.violations)) {
          r.violations.forEach((v) => {
            list.push({
              type: "LAW_VIOLATION",
              focusLabel: r.label,
              text: v.reason || v.recommendation || "",
              law: v.law_name,
              article: v.article_title,
              severity: v.severity || "MEDIUM",
            });
          });
        }
      });
    }

    // 2) 공고문 쪽 누락/세부 조건 차이
    if (hasCompare) {
      const missingSections = compareResult?.missing_sections || [];
      const rawMissingFeatures = compareResult?.feature_mismatch || [];

      const normalizedMissingFeatures =
        buildNormalizedMissingFeatureList(rawMissingFeatures);

      missingSections.forEach((s) => {
        list.push({
          type: "NOTICE_SECTION",
          focusLabel: "공고문 섹션",
          text: `${s} 섹션이 초안에서 빠져 있습니다.`,
          severity: "MEDIUM",
        });
      });

      normalizedMissingFeatures.forEach((f) => {
        list.push({
          type: "NOTICE_FEATURE",
          focusLabel: "공고문 세부 조건",
          text: `${f} 관련 공고문 조건이 초안 내용과 다르거나 빠져 있습니다. (예: 지원대상, 예산 한도, 사업기간 등)`,
          severity: "MEDIUM",
        });
      });
    }

    const SEVERITY_ORDER = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    list.sort(
      (a, b) =>
        (SEVERITY_ORDER[b.severity] || 0) - (SEVERITY_ORDER[a.severity] || 0)
    );

    return list.slice(0, 3);
  }, [results, compareResult, hasLaw, hasCompare]);

  if (items.length === 0) return null;

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          sx={{ mb: 1 }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            지금 바로 보완하면 좋은 Top 3
          </Typography>
          <Chip
            icon={<WarningAmberIcon />}
            label={`${items.length}개 핵심 보완 포인트`}
            size="small"
            color="warning"
          />
        </Stack>

        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          아래 항목부터 순서대로 보완하면, 심사 관점에서 눈에 띄는 리스크를
          빠르게 줄일 수 있습니다.
        </Typography>

        <List dense>
          {items.map((item, idx) => (
            <ListItem key={idx} alignItems="flex-start">
              <ListItemText
                primary={
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Chip
                      size="small"
                      variant="outlined"
                      label={item.focusLabel}
                    />
                    <Chip
                      size="small"
                      label={SEVERITY_LABELS[item.severity] || item.severity}
                      sx={{
                        borderColor: SEVERITY_COLORS[item.severity] || "#999",
                        color: SEVERITY_COLORS[item.severity] || "#999",
                      }}
                      variant="outlined"
                    />
                  </Stack>
                }
                secondary={
                  <Box sx={{ mt: 0.5 }}>
                    <Typography
                      variant="body2"
                      sx={{ whiteSpace: "pre-line" }}
                    >
                      {idx + 1}. {item.text}
                    </Typography>
                    {item.law && (
                      <Typography
                        variant="caption"
                        sx={{ color: "text.secondary" }}
                      >
                        관련 법령: {item.law} {item.article}
                      </Typography>
                    )}
                  </Box>
                }
                secondaryTypographyProps={{ component: "div" }}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}

// =======================================================
// 📘 법령 검증 상세
// =======================================================
function LawDetailSection({ results }) {
  const hasResults = results && Object.keys(results).length > 0;
  if (!hasResults) return null;

  const JUDGMENT_LABELS = {
    NO_ISSUE: "법령 위반 징후 없음",
    POTENTIAL_VIOLATION: "법령 위반 가능성 있음",
    POSSIBLE_ISSUE: "법령 리스크 가능성 있음",
    UNCLEAR: "법령 위반 판단 어려움",
  };

  return (
    <Card sx={{ mt: 4 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
          법령 검증 상세 결과
        </Typography>
        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          주요 관점별로 어떤 이유로 적합/보완/부적합 판정이 났는지, 법령 위반
          가능성이 어디에서 발생하는지 확인할 수 있습니다.
        </Typography>

        {Object.entries(results).map(([key, r], idx) => (
          <Accordion key={key || idx} sx={{ boxShadow: "none" }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography sx={{ fontWeight: 600 }}>{r.label}</Typography>

                {r.status && (
                  <Chip
                    size="small"
                    label={r.status}
                    color={
                      r.status === "적합"
                        ? "success"
                        : r.status === "보완"
                        ? "warning"
                        : "error"
                    }
                  />
                )}

                {r.risk_level && (
                  <Chip size="small" variant="outlined" label={r.risk_level} />
                )}

                {r.violation_judgment && (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={
                      JUDGMENT_LABELS[r.violation_judgment] ||
                      r.violation_judgment
                    }
                  />
                )}
              </Stack>
            </AccordionSummary>

            <AccordionDetails>
              {r.violation_summary && r.violation_summary.trim().length > 0 && (
                <Box
                  sx={{
                    mb: 2,
                    p: 1.5,
                    borderRadius: 1,
                    bgcolor: "rgba(244, 67, 54, 0.03)",
                    border: "1px solid rgba(244, 67, 54, 0.3)",
                  }}
                >
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    법령 위반 가능성 요약
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ whiteSpace: "pre-line" }}
                  >
                    {r.violation_summary}
                  </Typography>
                </Box>
              )}

              {r.missing?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    부족한 요소
                  </Typography>
                  <List dense>
                    {r.missing.map((m, i) => (
                      <ListItem key={i}>
                        <ListItemText primary={m} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {r.suggestion && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    보완 제안
                  </Typography>
                  <Typography sx={{ whiteSpace: "pre-line" }}>
                    {r.suggestion}
                  </Typography>
                </Box>
              )}

              {r.violations?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    법령 위반 가능성이 있는 조항
                  </Typography>
                  <List dense>
                    {r.violations.map((v, i) => (
                      <ListItem key={i} alignItems="flex-start">
                        <ListItemText
                          primary={
                            <Typography variant="body2">
                              {v.law_name}{" "}
                              {v.article_no ? `${v.article_no} ` : ""}
                              {v.article_title}
                            </Typography>
                          }
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              {v.reason && (
                                <Typography
                                  variant="body2"
                                  sx={{ whiteSpace: "pre-line" }}
                                >
                                  {v.reason}
                                </Typography>
                              )}
                              {v.recommendation && (
                                <Typography
                                  variant="body2"
                                  sx={{ mt: 0.5, whiteSpace: "pre-line" }}
                                >
                                  <b>보완 제안:</b> {v.recommendation}
                                </Typography>
                              )}
                            </Box>
                          }
                          secondaryTypographyProps={{ component: "div" }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {r.related_laws?.length > 0 && (
                <Box>
                  <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                    참고할 법령
                  </Typography>
                  <Stack direction="row" gap={1} flexWrap="wrap">
                    {r.related_laws.map((law, i) => (
                      <Chip
                        key={i}
                        size="small"
                        variant="outlined"
                        label={`${law.law_name} ${law.article_title}`}
                      />
                    ))}
                  </Stack>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </CardContent>
    </Card>
  );
}

// =======================================================
// 📗 공고문 vs 초안 상세
// =======================================================
function NoticeDetailSection({ compareResult }) {
  if (!compareResult) return null;

  const missingSections = compareResult?.missing_sections || [];
  const rawMissingFeatures = compareResult?.feature_mismatch || [];

  // 🔹 EXCLUDE 키워드 제거 + normalize + 중복 제거
  const missingFeatures = buildNormalizedMissingFeatureList(rawMissingFeatures);

  const sectionDetails = compareResult?.section_analysis?.details || [];

  // 🔹 Feature 상세 분석에서도
  //     - EXCLUDE 키워드 포함된 건 숨기고
  //     - 사업기간 / 주요 추진일정 등은 하나로 합치기
  const rawFeatureDetails = compareResult?.feature_analysis?.details || [];
  const mergedFeatureMap = {};

  rawFeatureDetails.forEach((item) => {
    const rawLabel =
      typeof item?.feature === "string"
        ? item.feature
        : String(item?.feature ?? "");

    if (FEATURE_EXCLUDE_KEYWORDS.some((kw) => rawLabel.includes(kw))) {
      return;
    }

    const label = normalizeFeatureLabel(rawLabel);

    if (!mergedFeatureMap[label]) {
      mergedFeatureMap[label] = {
        ...item,
        feature: label,
      };
    }
  });

  const featureDetails = Object.values(mergedFeatureMap);

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
          공고문 요구사항 vs 초안 상세
        </Typography>
        <Typography sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}>
          공고문에서 요구한 항목이 초안에 어떻게 반영되었는지,{" "}
          <b>어떤 섹션이 빠져 있는지</b>와{" "}
          <b>
            지원대상·기간·예산 등 심사에 영향을 주는 세부 조건이 어디에서
            다른지
          </b>
          를 확인할 수 있습니다. (문의처, 공고기관, 접수기관, 평가기준 등
          단순 안내 정보는 리포트에서 제외됩니다.)
        </Typography>

        {/* 섹션 상세 */}
        {sectionDetails.length > 0 && (
          <>
            <Typography sx={{ fontWeight: 600, mt: 1, mb: 1 }}>
              섹션별 상세 분석
            </Typography>
            {sectionDetails.map((item, i) => (
              <Accordion key={i} sx={{ boxShadow: "none" }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography sx={{ fontWeight: 600 }}>
                    {item.section}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>이유:</b> {item.reason}
                  </Typography>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>보완 제안:</b> {item.suggestion}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </>
        )}

        {/* Feature(세부 조건) 상세 */}
        {featureDetails.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography sx={{ fontWeight: 600, mb: 1 }}>
              세부 조건별 분석 (지원대상, 사업기간, 예산 등)
            </Typography>
            <Typography
              sx={{ color: "text.secondary", mb: 1.5, fontSize: 13 }}
            >
              공고문에서 추출한 세부 조건(지원대상, 사업기간, 예산 조건 등)을
              기준으로, 초안의 표현이 충분한지/조건을 정확히 맞추고 있는지
              점검한 결과입니다. 문의처·공고기관·접수기관 등 단순 안내 정보는
              여기에서 제외됩니다.
            </Typography>
            {featureDetails.map((item, i) => (
              <Accordion key={i} sx={{ boxShadow: "none" }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography sx={{ fontWeight: 600 }}>
                    {item.feature}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>이유:</b> {item.reason}
                  </Typography>
                  <Typography sx={{ mt: 0.5 }}>
                    <b>보완 제안:</b> {item.suggestion}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </>
        )}

        {missingSections.length === 0 &&
          missingFeatures.length === 0 &&
          sectionDetails.length === 0 &&
          featureDetails.length === 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography sx={{ color: "text.secondary" }}>
                공고문 기준으로 분석할 세부 항목이 없습니다.
              </Typography>
            </Box>
          )}
      </CardContent>
    </Card>
  );
}

// =======================================================
// 🚀 종합 리포트 메인
// =======================================================
function VerifyReport() {
  const navigate = useNavigate();
  const project = useProjectStore((state) => state.project);
  const { results, compareResult } = useVerifyStore();

  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;
  const isEmpty = !hasLaw && !hasCompare;

  return (
    <Box sx={{ p: 3 }}>
      {/* 상단 헤더 */}
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            종합 리포트
          </Typography>
          <Typography sx={{ color: "text.secondary", fontSize: 14 }}>
            현재 프로젝트에 대해 수행한{" "}
            <b>법령 검증</b> 및 <b>공고문-초안 비교 결과</b>를 한눈에 정리한
            리포트입니다.
          </Typography>
          {project?.projectName && (
            <Typography
              sx={{ mt: 0.5, fontSize: 13, color: "text.secondary" }}
            >
              프로젝트: <b>{project.projectName}</b>
            </Typography>
          )}
        </Stack>

        <Stack direction="row" spacing={1.5}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate("/works/verify")}
          >
            검증 화면으로 돌아가기
          </Button>
        </Stack>
      </Stack>

      {/* 아무 데이터 없을 때 안내 */}
      {isEmpty && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ mb: 1 }}
            >
              <ErrorOutlineIcon color="warning" />
              <Typography sx={{ fontWeight: 600 }}>
                아직 생성된 리포트가 없습니다.
              </Typography>
            </Stack>
            <Typography sx={{ color: "text.secondary", mb: 2 }}>
              먼저 검증 화면에서 <b>법령 검증</b> 또는 <b>초안 검증</b>을
              실행한 뒤, 다시 종합 리포트를 확인해 주세요.
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate("/works/verify")}
              startIcon={<CheckCircleOutlineIcon />}
            >
              검증 실행하러 가기
            </Button>
          </CardContent>
        </Card>
      )}

      {/* 데이터가 있을 때만 나머지 섹션들 렌더링 */}
      {!isEmpty && (
        <>
          <SummaryHeader results={results} compareResult={compareResult} />
          <TopIssuesSection results={results} compareResult={compareResult} />
          {hasLaw && <LawDetailSection results={results} />}
          {hasCompare && <NoticeDetailSection compareResult={compareResult} />}
        </>
      )}
    </Box>
  );
}

export default VerifyReport;
