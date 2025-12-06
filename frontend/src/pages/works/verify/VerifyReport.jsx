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
  LinearProgress,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

import { useProjectStore } from "../../../store/useProjectStore";
import { useVerifyStore } from "../../../store/useVerifyStore";
import { useNavigate } from "react-router-dom";
import {
  FEATURE_EXCLUDE_KEYWORDS,
  normalizeFeatureLabel,
  buildNormalizedMissingFeatureList,
} from "../../../utils/verifyUtils";

// 색상 상수
const STATUS_COLORS = { 적합: "#4caf50", 보완: "#ffb300", 부적합: "#f44336" };
const SEVERITY_COLORS = { LOW: "#4caf50", MEDIUM: "#ffb300", HIGH: "#f44336" };
const COVERAGE_COLORS = ["#4caf50", "#f44336"];

// 🔹 사용자에게 보여줄 한글 라벨
const SEVERITY_LABELS = {
  LOW: "위험도 낮음",
  MEDIUM: "위험도 보통",
  HIGH: "위험도 높음",
};

// =======================================================
// 🔍 리포트 상단: 요약 카드들 (법령 + 공고문 + 자가진단)
// =======================================================
function SummaryHeader({ results, compareResult, noticeEval }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;

  // ⚖️ 법령 요약
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
      const STATUS_NUM = { 적합: 1, 보완: 2, 부적합: 3 };
      const RISK_NUM = { LOW: 1, MEDIUM: 2, HIGH: 3 };

      const aStatus = a?.status || "적합";
      const bStatus = b?.status || "적합";
      const aRisk = a?.risk_level || "LOW";
      const bRisk = b?.risk_level || "LOW";

      const statusDiff = STATUS_NUM[bStatus] - STATUS_NUM[aStatus];
      if (statusDiff !== 0) return statusDiff;

      return RISK_NUM[bRisk] - RISK_NUM[aRisk];
    });

    const overallStatus = sorted[0]?.[1]?.status || null;

    return {
      statusCounts,
      overallStatus,
      overallRisk: worstRisk,
      overallViolationSeverity: worstViolSeverity,
    };
  }, [results, hasLaw]);

  // 📊 공고문 비교 요약 (공고문 충족률)
  const compareSummary = useMemo(() => {
    if (!hasCompare) return null;

    const toc = compareResult?.toc_progress || {};
    const fa = compareResult?.feature_analysis || {};

    const tocTotal = toc.total_sections ?? 0;
    const tocWritten = toc.written_sections ?? 0;
    let tocPercent = null;

    if (typeof toc.progress_percent === "number") {
      tocPercent = toc.progress_percent;
    } else if (tocTotal > 0) {
      tocPercent = Math.round((tocWritten / tocTotal) * 100);
    }

    const totalFeatures = fa.total_features ?? 0;
    const missingFeatureCount = fa.missing_count ?? 0;
    const partialFeatureCount = fa.partial_count ?? 0;

    let okFeatures = 0;
    let featurePercent = null;

    if (totalFeatures > 0) {
      okFeatures = totalFeatures - missingFeatureCount - partialFeatureCount;
      if (okFeatures < 0) okFeatures = 0;
      featurePercent = Math.round((okFeatures / totalFeatures) * 100);
    }

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
        written: tocWritten,
        total: tocTotal,
      },
    };
  }, [compareResult, hasCompare]);

  // 🟦 자가진단 퍼센트
  const selfPercent = useMemo(() => {
    if (!noticeEval) return null;

    if (typeof noticeEval.percent === "number") {
      return Math.max(0, Math.min(noticeEval.percent, 100));
    }

    if (
      typeof noticeEval.total_score === "number" &&
      typeof noticeEval.total_max_score === "number" &&
      noticeEval.total_max_score > 0
    ) {
      return Math.round(
        (noticeEval.total_score / noticeEval.total_max_score) * 100
      );
    }

    return null;
  }, [noticeEval]);

  // 법령 상태 분포 (도넛 차트 데이터)
  const statusChartData =
    lawSummary &&
    Object.entries(lawSummary.statusCounts)
      .filter(([, count]) => count > 0)
      .map(([name, value]) => ({ name, value }));

  // 🔹 법령 적합 비율(적합 개수 / 전체 관점 개수)
  const lawTotal =
    statusChartData?.reduce((sum, item) => sum + item.value, 0) ?? 0;
  const lawFit =
    statusChartData?.find((item) => item.name === "적합")?.value ?? 0;
  const lawFitPercent =
    lawTotal > 0 ? Math.round((lawFit / lawTotal) * 100) : null;

  // 공고문/초안 검사 결과 분포 (충족 vs 보완 필요)
  const coverageRate =
    compareSummary && typeof compareSummary.combinedPercent === "number"
      ? compareSummary.combinedPercent
      : null;

  const coverageChartData =
    coverageRate !== null
      ? [
          { name: "충족", value: coverageRate },
          { name: "보완 필요", value: Math.max(100 - coverageRate, 0) },
        ]
      : null;

  return (
    <Stack direction={{ xs: "column", md: "row" }} spacing={3} sx={{ mt: 3 }}>
      {/* 전체 평가 요약 카드 */}
      <Card sx={{ flex: 1.1, minWidth: 0 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            전체 평가 요약
          </Typography>

          {!hasLaw && !hasCompare && !noticeEval && (
            <Typography sx={{ mt: 1.5, color: "text.secondary" }}>
              아직 생성된 리포트가 없습니다. 먼저 검증 화면에서 법령 검증 또는
              초안 검증을 실행해 주세요.
            </Typography>
          )}

          {(hasLaw || hasCompare || noticeEval) && (
            <Stack spacing={1.5} sx={{ mt: 1.5 }}>
              {/* 법령 판단 / 리스크 / 위반 가능성 */}
              {lawSummary && (
                <>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                      법령 판단
                    </Typography>
                    {lawSummary.overallStatus ? (
                      <Chip
                        label={lawSummary.overallStatus}
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      <Typography>-</Typography>
                    )}
                  </Stack>

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
                            SEVERITY_COLORS[lawSummary.overallViolationSeverity],
                          color:
                            SEVERITY_COLORS[lawSummary.overallViolationSeverity],
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
                      <> (목차 기준 {compareSummary.tocPercent}% 기준)</>
                    )}
                  </Typography>
                </Stack>
              )}

              {/* 자가진단 퍼센트 한 줄 */}
              {noticeEval && selfPercent !== null && (
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                    자가진단 점수
                  </Typography>
                  <Typography sx={{ fontWeight: 700 }}>
                    {selfPercent}%
                  </Typography>
                  <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                    (총점 {noticeEval.total_score} /{" "}
                    {noticeEval.total_max_score} 기준)
                  </Typography>
                </Stack>
              )}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* 🟢 중간 카드: 법령 검증 분포 (도넛) */}
      {lawSummary && statusChartData && statusChartData.length > 0 && (
        <Card
          sx={{
            width: { xs: "100%", md: 280 },
            flexShrink: 0,
          }}
        >
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
              법령 검증 분포
            </Typography>
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

            {/* 🔹 법령 도넛 한 줄 요약 */}
            {lawFitPercent !== null && (
              <Box sx={{ mt: 1.5 }}>
                <Typography sx={{ fontSize: 13, color: "text.secondary" }}>
                  법령 검증 관점에서 주요 관점 {lawTotal}개 중{" "}
                  <b>{lawFit}개</b>가 적합 판정을 받아, 약{" "}
                  <b>{lawFitPercent}%</b> 수준으로 법령 요구사항을 충족하고
                  있습니다.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* 🟡 오른쪽 카드: 검사 결과 분포 (공고문 기준 충족/보완 필요) */}
      {(coverageChartData || selfPercent !== null) && (
        <Card
          sx={{
            width: { xs: "100%", md: 280 },
            flexShrink: 0,
          }}
        >
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
              초안 결과 분포
            </Typography>

            {coverageChartData ? (
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <PieChart width={220} height={200}>
                  <Pie
                    data={coverageChartData}
                    dataKey="value"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {coverageChartData.map((entry, idx) => (
                      <Cell
                        key={idx}
                        fill={COVERAGE_COLORS[idx] || "#999"}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </Box>
            ) : (
              <Box
                sx={{
                  height: 200,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                  공고문 기준 검사 결과가 아직 없습니다.
                </Typography>
              </Box>
            )}

            <Box sx={{ mt: 1.5 }}>
              {compareSummary && (
                <Typography sx={{ fontSize: 13, color: "text.secondary" }}>
                  공고문 형식(목차)·세부 조건 기준으로 초안을 평가했을 때,{" "}
                  <b>{coverageRate ?? "-"}%</b> 정도 충족하고 있습니다.
                </Typography>
              )}
            </Box>
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
      Object.entries(results).forEach(([_, r]) => {
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
      (a, b) => (SEVERITY_ORDER[b.severity] || 0) - (SEVERITY_ORDER[a.severity] || 0)
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

        <Typography
          sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}
        >
          아래 항목부터 순서대로 보완하면, 심사 관점에서 눈에 띄는 리스크를
          빠르게 줄일 수 있습니다.
        </Typography>

        <List dense>
          {items.map((item, idx) => (
            <ListItem key={idx} alignItems="flex-start">
              <ListItemText
                primary={
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Chip size="small" variant="outlined" label={item.focusLabel} />
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
        <Typography
          sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}
        >
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
              {/* 법령 위반 가능성 요약 */}
              {r.violation_summary &&
                r.violation_summary.trim().length > 0 && (
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

              {/* 부족한 요소 */}
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

              {/* 보완 제안 */}
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

              {/* 법령 위반 가능성이 있는 조항 */}
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
                                  sx={{
                                    mt: 0.5,
                                    whiteSpace: "pre-line",
                                  }}
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

              {/* 참고할 법령 */}
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

  const missingFeatures = buildNormalizedMissingFeatureList(rawMissingFeatures);

  const sectionDetails = compareResult?.section_analysis?.details || [];
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
        <Typography
          sx={{ color: "text.secondary", mb: 2, fontSize: 14 }}
        >
          공고문에서 요구한 항목이 초안에 어떻게 반영되었는지,{" "}
          <b>어떤 섹션이 빠져 있는지</b>와{" "}
          <b>
            지원대상·사업기간·예산 등 심사에 영향을 주는 세부 조건이 어디에서
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
// 🟦   자가진단 대시보드 (종합 리포트용)
// =======================================================
function NoticeCriteriaSelfCheck({ data }) {
  if (!data) return null;

  const {
    block_name,
    total_score,
    total_max_score,
    percent,
    items = [],
  } = data;

  const percentValue =
    typeof percent === "number"
      ? Math.max(0, Math.min(percent, 100))
      : total_max_score
      ? Math.round((total_score / total_max_score) * 100)
      : null;

  const statusColor = (status) => {
    if (!status) return "default";
    if (status.includes("우수") || status.includes("적합")) return "success";
    if (status.includes("보통") || status.includes("보완")) return "warning";
    return "error";
  };

  return (
    <Box sx={{ mt: 3, display: "flex", flexDirection: "column", gap: 3 }}>
      {/* 상단 요약 카드 */}
      <Card>
        <CardContent>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4}>
            {/* 왼쪽: 설명 */}
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {block_name || "공고문 평가기준 자가진단"}
              </Typography>
              <Typography
                variant="body2"
                sx={{ mt: 1, color: "text.secondary" }}
              >
                실제 평가표에 들어갈 수 있는 기준(확산 가능성, 사업관리 적정성,
                품질관리 우수성, 일자리 창출 등)을 바탕으로, 현재 초안이 어느
                수준인지 진단한 결과입니다.
              </Typography>

              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  borderRadius: 1,
                  bgcolor: "rgba(25, 118, 210, 0.03)",
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: "pre-line" }}>
                  · 총점 기준으로 약{" "}
                  <b>{percentValue !== null ? `${percentValue}%` : "-"}</b>
                  수준의 경쟁력을 보이고 있습니다.
                  <br />
                  · 각 평가 항목별 강점과 보완 포인트를 참고해 초안을 수정하면,
                  실제 평가 점수 향상에 도움이 됩니다.
                </Typography>
              </Box>
            </Box>

            {/* 오른쪽: 점수 / 퍼센트 */}
            <Box
              sx={{
                width: 260,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {percentValue !== null ? (
                <>
                  <Typography
                    variant="h3"
                    sx={{ fontWeight: 800, lineHeight: 1.1 }}
                  >
                    {percentValue}%
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ color: "text.secondary", mt: 0.5 }}
                  >
                    평가기준 달성도
                  </Typography>

                  <LinearProgress
                    variant="determinate"
                    value={percentValue}
                    sx={{
                      mt: 1.5,
                      width: "100%",
                      height: 8,
                      borderRadius: 999,
                    }}
                  />

                  <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`총점 ${total_score} / ${total_max_score}`}
                    />
                  </Stack>
                </>
              ) : (
                <Typography sx={{ color: "text.secondary" }}>
                  점수 정보가 없습니다.
                </Typography>
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* 항목별 상세 카드 */}
      {items.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              평가기준별 진단 결과
            </Typography>
            <Typography
              variant="body2"
              sx={{ mt: 0.5, mb: 1.5, color: "text.secondary" }}
            >
              각 평가 항목에 대해 현재 초안이 어떤 점에서 강점이 있고, 어떤
              부분을 보완하면 좋은지 정리한 내용입니다.
            </Typography>

            {items.map((item, idx) => (
              <Accordion key={idx} sx={{ boxShadow: "none" }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography sx={{ fontWeight: 600 }}>
                      {item.name}
                    </Typography>

                    <Chip
                      size="small"
                      variant="outlined"
                      label={`${item.score} / ${item.max_score}점`}
                    />

                    {item.status && (
                      <Chip
                        size="small"
                        color={statusColor(item.status)}
                        label={item.status}
                      />
                    )}
                  </Stack>
                </AccordionSummary>

                <AccordionDetails>
                  {/* 이유 */}
                  {item.reason && (
                    <Box sx={{ mb: 1.5 }}>
                      <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                        왜 이렇게 평가되었나요?
                      </Typography>
                      <Typography sx={{ whiteSpace: "pre-line" }}>
                        {item.reason}
                      </Typography>
                    </Box>
                  )}

                  {/* 보완 제안 */}
                  {item.suggestion && (
                    <Box>
                      <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                        어떤 점을 보완하면 좋을까요?
                      </Typography>
                      <Typography sx={{ whiteSpace: "pre-line" }}>
                        {item.suggestion}
                      </Typography>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

// =======================================================
// 🚀 종합 리포트 메인
// =======================================================
function VerifyReport() {
  const navigate = useNavigate();
  const project = useProjectStore((state) => state.project); // 필요하면 나중에 활용
  const { results, compareResult, noticeEvalResult } = useVerifyStore();

  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;
  const isEmpty = !hasLaw && !hasCompare;

  return (
    <Box sx={{ p: 3 }}>
      {/* 상단 헤더 */}
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
      >
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            종합 리포트
          </Typography>
          <Typography sx={{ color: "text.secondary", fontSize: 14 }}>
            현재 프로젝트에 대해 수행한 <b>법령 검증</b> 및{" "}
            <b>공고문-초안 비교 결과</b>를 한눈에 정리한 리포트입니다.
          </Typography>
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

      {/* 데이터가 있을 때만 나머지 섹션들 렌더링 */}
      {!isEmpty && (
        <>
          <SummaryHeader
            results={results}
            compareResult={compareResult}
            noticeEval={noticeEvalResult}
          />
          <TopIssuesSection
            results={results}
            compareResult={compareResult}
          />

          {/* 🔵 공고문 평가기준 자가진단: 상단 요약 바로 아래에 배치 */}
          {noticeEvalResult && (
            <NoticeCriteriaSelfCheck data={noticeEvalResult} />
          )}

          {hasLaw && <LawDetailSection results={results} />}
          {hasCompare && (
            <NoticeDetailSection compareResult={compareResult} />
          )}
        </>
      )}

      {isEmpty && (
        <Typography sx={{ mt: 3, color: "text.secondary" }}>
          아직 생성된 리포트가 없습니다. 검증 화면에서 먼저 법령 검증 또는 초안
          검증을 실행해 주세요.
        </Typography>
      )}
    </Box>
  );
}

export default VerifyReport;
