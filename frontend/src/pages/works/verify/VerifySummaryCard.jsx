import React, { useMemo } from "react";
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
  Divider,
  Box,
} from "@mui/material";
import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

const STATUS_COLORS = { 적합: "#4caf50", 보완: "#ff9800", 부적합: "#f44336" };
const RISK_LABELS = { LOW: "낮음", MEDIUM: "중간", HIGH: "높음" };
const SEVERITY_LABELS = { LOW: "낮음", MEDIUM: "보통", HIGH: "높음" };
const SEVERITY_CHIP_COLORS = { LOW: "default", MEDIUM: "warning", HIGH: "error" };

const riskRank = { LOW: 1, MEDIUM: 2, HIGH: 3 };
const severityRank = { LOW: 1, MEDIUM: 2, HIGH: 3 };

export default function VerifySummaryCard({ results = {}, compareResult, noticeEval }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;
  const hasNotice = !!noticeEval;

  const lawSummary = useMemo(() => {
    if (!hasLaw) return null;

    const statusCounts = { 적합: 0, 보완: 0, 부적합: 0 };
    let worstRisk = null;
    let worstSeverity = null;
    const actionItems = [];
    const highRiskFocuses = [];
    const focusCount = Object.keys(results || {}).length;

    Object.values(results || {}).forEach((r) => {
      if (!r) return;
      const { status, risk_level, violations, missing, label } = r;

      if (status && statusCounts[status] !== undefined) {
        statusCounts[status] += 1;
      }

      if (risk_level) {
        if (!worstRisk || riskRank[risk_level] > riskRank[worstRisk]) {
          worstRisk = risk_level;
        }
      }

      if (Array.isArray(violations)) {
        violations.forEach((v) => {
          const sev = v?.severity;
          if (sev && severityRank[sev]) {
            if (!worstSeverity || severityRank[sev] > severityRank[worstSeverity]) {
              worstSeverity = sev;
            }
            if (sev === "HIGH" && label) {
              highRiskFocuses.push(label);
            }
          }
        });
      }

      if (Array.isArray(missing)) {
        missing.forEach((m) => actionItems.push({ focus: label || "-", text: m }));
      }
    });

    const statusChartData = Object.entries(statusCounts)
      .filter(([, value]) => value > 0)
      .map(([name, value]) => ({ name, value }));

    return {
      statusCounts,
      statusChartData,
      totalFocusCount: focusCount,
      overallRisk: worstRisk,
      overallViolationSeverity: worstSeverity,
      actionItems,
      highRiskFocuses: Array.from(new Set(highRiskFocuses)),
    };
  }, [hasLaw, results]);

  const compareSummary = useMemo(() => {
    if (!hasCompare) return null;
    const toc = compareResult?.toc_progress || {};
    const tocPercent =
      typeof toc.progress_percent === "number" ? toc.progress_percent : null;

    const missingSections = (compareResult?.missing_sections || []).length;
    const featureMismatch = (compareResult?.feature_mismatch || []).length;

    return { tocPercent, missingSections, featureMismatch };
  }, [hasCompare, compareResult]);

  const noticePercent = useMemo(() => {
    if (!hasNotice) return null;
    const root = noticeEval?.data ? noticeEval.data : noticeEval;
    if (typeof root?.percent === "number") return root.percent;
    if (
      typeof root?.total_score === "number" &&
      typeof root?.total_max_score === "number" &&
      root.total_max_score > 0
    ) {
      return Math.round((root.total_score / root.total_max_score) * 100);
    }
    return null;
  }, [hasNotice, noticeEval]);

  if (!hasLaw && !hasCompare && !hasNotice) return null;

  const statusCounts = lawSummary?.statusCounts || { 적합: 0, 보완: 0, 부적합: 0 };
  const totalFocusCount = lawSummary?.totalFocusCount || 0;
  const statusChartData = lawSummary?.statusChartData || [];
  const overallRisk = lawSummary?.overallRisk;
  const overallViolationSeverity = lawSummary?.overallViolationSeverity;
  const actionItems = lawSummary?.actionItems || [];
  const highRiskFocuses = lawSummary?.highRiskFocuses || [];

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
          검증 종합 요약
        </Typography>

        {lawSummary && (
          <Box sx={{ mb: hasCompare || hasNotice ? 3 : 0 }}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={3}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  법령 검증 종합 의견
                </Typography>

                <Stack spacing={1.2} sx={{ mt: 1.5, mb: 3 }}>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    총 {totalFocusCount}개 관점 중{" "}
                    <b>적합 {statusCounts.적합}개</b>,{" "}
                    <b>보완 {statusCounts.보완}개</b>,{" "}
                    <b>부적합 {statusCounts.부적합}개</b>로 평가되었습니다.
                  </Typography>

                  {overallViolationSeverity && (
                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      전반적인 법령 위반 가능성은{" "}
                      <b>{SEVERITY_LABELS[overallViolationSeverity]}</b> 수준이며
                      {highRiskFocuses.length > 0 && (
                        <>
                          , 특히 {highRiskFocuses.join(", ")} 관점에서 리스크가 큽니다.
                        </>
                      )}
                      .
                    </Typography>
                  )}

                  {actionItems.length > 0 && (
                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      세부적으로 보완이 권장된 항목은 총 <b>{actionItems.length}개</b>이며,
                      아래 <b>관점별 상세 분석</b>에서 구체적인 수정 제안을 확인할 수 있습니다.
                    </Typography>
                  )}
                </Stack>
              </Box>

              <Box sx={{ width: 260 }}>
                {statusChartData.length === 0 ? (
                  <Box
                    sx={{
                      height: 230,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Typography sx={{ textAlign: "center", color: "text.secondary" }}>
                      검증 결과 없음
                    </Typography>
                  </Box>
                ) : (
                  <Box
                    sx={{
                      width: 260,
                      height: 230,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <PieChart width={260} height={230}>
                      <Pie
                        data={statusChartData}
                        dataKey="value"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={3}
                      >
                        {statusChartData.map((entry, idx) => (
                          <Cell key={idx} fill={STATUS_COLORS[entry.name] || "#999"} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </Box>
                )}

                <Stack spacing={0.5} sx={{ mt: 1 }}>
                  {overallRisk && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`전체 리스크: ${RISK_LABELS[overallRisk] || overallRisk}`}
                    />
                  )}

                  {overallViolationSeverity && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`법령 위반 가능성: ${
                        SEVERITY_LABELS[overallViolationSeverity] ||
                        overallViolationSeverity
                      }`}
                      color={SEVERITY_CHIP_COLORS[overallViolationSeverity] || "default"}
                    />
                  )}
                </Stack>
              </Box>
            </Stack>
          </Box>
        )}

        {(compareSummary || noticePercent !== null) && <Divider sx={{ my: 2 }} />}

        {(compareSummary || noticePercent !== null) && (
          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={3}
            divider={<Divider flexItem orientation="vertical" />}
          >
            {compareSummary && (
              <Stack spacing={1}>
                <Typography sx={{ fontWeight: 600 }}>공고문 비교 요약</Typography>
                <Typography sx={{ color: "text.secondary" }}>
                  목차 작성도: {compareSummary.tocPercent ?? "-"}%
                </Typography>
                <Chip
                  label={`미작성 섹션 ${compareSummary.missingSections}개 / feature 미스매치 ${compareSummary.featureMismatch}개`}
                  variant="outlined"
                  size="small"
                />
              </Stack>
            )}

            {noticePercent !== null && (
              <Stack spacing={1}>
                <Typography sx={{ fontWeight: 600 }}>평가기준 자가진단</Typography>
                <Typography sx={{ color: "text.secondary" }}>
                  점수 달성도: {noticePercent}%
                </Typography>
              </Stack>
            )}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
