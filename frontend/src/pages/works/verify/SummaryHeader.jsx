import React, { useMemo } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Chip,
} from "@mui/material";

import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

// 색상 상수
const STATUS_COLORS = { 적합: "#4caf50", 보완: "#ffb300", 부적합: "#f44336" };
const SEVERITY_COLORS = { LOW: "#4caf50", MEDIUM: "#ffb300", HIGH: "#f44336" };
const COVERAGE_COLORS = ["#4caf50", "#f44336"];

// 한글 라벨
const SEVERITY_LABELS = {
  LOW: "위험도 낮음",
  MEDIUM: "위험도 보통",
  HIGH: "위험도 높음",
};

export default function SummaryHeader({ results, compareResult, noticeEval }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;

  // ⚖️ 법령 요약 계산
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

    return {
      statusCounts,
      overallStatus: sorted[0]?.[1]?.status || null,
      overallRisk: worstRisk,
      overallViolationSeverity: worstViolSeverity,
    };
  }, [results, hasLaw]);

  // 📊 공고문 비교 요약 (충족률)
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

    // feature 충족률
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

    return {
      tocPercent,
      featurePercent,
      combinedPercent: count > 0 ? Math.round(combined / count) : null,
      tocCounts: { written: tocWritten, total: tocTotal },
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

  // 🔴 도넛용 데이터 생성
  const statusChartData =
    lawSummary &&
    Object.entries(lawSummary.statusCounts)
      .filter(([, count]) => count > 0)
      .map(([name, value]) => ({ name, value }));

  const lawTotal =
    statusChartData?.reduce((sum, item) => sum + item.value, 0) ?? 0;
  const lawFit =
    statusChartData?.find((item) => item.name === "적합")?.value ?? 0;
  const lawFitPercent =
    lawTotal > 0 ? Math.round((lawFit / lawTotal) * 100) : null;

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
      {/* 카드 1: 전체 요약 */}
      <Card sx={{ flex: 1.1 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            전체 평가 요약
          </Typography>

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
                      size="small"
                      label={lawSummary.overallStatus}
                      color={
                        lawSummary.overallStatus === "적합"
                          ? "success"
                          : lawSummary.overallStatus === "보완"
                          ? "warning"
                          : "error"
                      }
                    />
                  ) : (
                    "-"
                  )}
                </Stack>

                {/* 리스크 */}
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                    리스크
                  </Typography>
                  {lawSummary.overallRisk ? (
                    <Chip size="small" variant="outlined" label={lawSummary.overallRisk} />
                  ) : (
                    "-"
                  )}
                </Stack>

                {/* 위반 가능성 */}
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                    법령 위반 가능성
                  </Typography>
                  {lawSummary.overallViolationSeverity ? (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={
                        SEVERITY_LABELS[lawSummary.overallViolationSeverity] ||
                        lawSummary.overallViolationSeverity
                      }
                      sx={{
                        borderColor:
                          SEVERITY_COLORS[lawSummary.overallViolationSeverity],
                        color:
                          SEVERITY_COLORS[lawSummary.overallViolationSeverity],
                      }}
                    />
                  ) : (
                    "-"
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
              </Stack>
            )}

            {/* 자가진단 점수 */}
            {noticeEval && selfPercent !== null && (
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Typography sx={{ minWidth: 80, color: "text.secondary" }}>
                  자가진단 점수
                </Typography>
                <Typography sx={{ fontWeight: 700 }}>{selfPercent}%</Typography>
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* 카드 2: 법령 도넛 */}
      {lawSummary && statusChartData?.length > 0 && (
        <Card sx={{ width: { xs: "100%", md: 280 } }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
              법령 검증 분포
            </Typography>

            <Box sx={{ display: "flex", justifyContent: "center" }}>
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

            {/* 하단 요약 */}
            {lawFitPercent !== null && (
              <Typography sx={{ mt: 1.5, fontSize: 13, color: "text.secondary" }}>
                법령 기준 {lawTotal}개 중 <b>{lawFit}개</b>가 적합하여  
                약 <b>{lawFitPercent}%</b> 수준으로 충족하고 있습니다.
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* 카드 3: 공고문 기준 충족률 */}
      {(coverageChartData || selfPercent !== null) && (
        <Card sx={{ width: { xs: "100%", md: 280 } }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
              초안 결과 분포
            </Typography>

            {/* 도넛 */}
            {coverageChartData ? (
              <Box sx={{ display: "flex", justifyContent: "center" }}>
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
                  공고문 기준 검사 결과 없음
                </Typography>
              </Box>
            )}

            {coverageRate !== null && (
              <Typography sx={{ mt: 1.5, fontSize: 13, color: "text.secondary" }}>
                공고문 기준 충족률은 약 <b>{coverageRate}%</b>입니다.
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Stack>
  );
}
