import React, { useMemo } from "react";
import { Card, CardContent, Typography, Stack, Chip, Divider } from "@mui/material";

export default function VerifySummaryCard({ results = {}, compareResult, noticeEval }) {
  const hasLaw = results && Object.keys(results).length > 0;
  const hasCompare = !!compareResult;
  const hasNotice = !!noticeEval;

  const lawIssueCounts = useMemo(() => {
    if (!hasLaw) return { missing: 0, violations: 0 };
    let missing = 0;
    let violations = 0;
    Object.values(results).forEach((r) => {
      missing += r?.missing?.length || 0;
      violations += r?.violations?.length || 0;
    });
    return { missing, violations };
  }, [hasLaw, results]);

  const compareIssueCounts = useMemo(() => {
    if (!hasCompare) return { missingSections: 0, featureMismatch: 0 };
    return {
      missingSections: compareResult?.missing_sections?.length || 0,
      featureMismatch: compareResult?.feature_mismatch?.length || 0,
    };
  }, [hasCompare, compareResult]);

  const lawSummary = useMemo(() => {
    if (!hasLaw) return null;

    const statusCounts = { 적합: 0, 보완: 0, 부적합: 0 };
    let worstRisk = null;

    Object.values(results).forEach((r) => {
      if (!r) return;
      if (r.status && statusCounts[r.status] !== undefined) {
        statusCounts[r.status] += 1;
      }
      if (r.risk_level) {
        const rank = { LOW: 1, MEDIUM: 2, HIGH: 3 };
        if (!worstRisk || rank[r.risk_level] > rank[worstRisk]) {
          worstRisk = r.risk_level;
        }
      }
    });

    const total = Object.values(statusCounts).reduce((a, b) => a + b, 0) || 1;
    const fitPercent = Math.round(((statusCounts["적합"] || 0) / total) * 100);

    return { statusCounts, fitPercent, worstRisk };
  }, [hasLaw, results]);

  const compareSummary = useMemo(() => {
    if (!hasCompare) return null;
    const toc = compareResult?.toc_progress || {};
    const fa = compareResult?.feature_analysis || {};

    const tocTotal = toc.total_sections ?? 0;
    const tocWritten = toc.written_sections ?? 0;
    const tocPercent =
      typeof toc.progress_percent === "number"
        ? toc.progress_percent
        : tocTotal > 0
        ? Math.round((tocWritten / tocTotal) * 100)
        : null;

    const totalFeatures = fa.total_features ?? 0;
    const missingCount = fa.missing_count ?? 0;
    const partialCount = fa.partial_count ?? 0;
    const okFeatures = Math.max(totalFeatures - missingCount - partialCount, 0);
    const featurePercent =
      totalFeatures > 0 ? Math.round((okFeatures / totalFeatures) * 100) : null;

    let combined = null;
    if (tocPercent !== null && featurePercent !== null) {
      combined = Math.round((tocPercent + featurePercent) / 2);
    } else if (tocPercent !== null) combined = tocPercent;
    else if (featurePercent !== null) combined = featurePercent;

    return { tocPercent, featurePercent, combined };
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

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
          종합 리포트 요약
        </Typography>

        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={3}
          divider={<Divider flexItem orientation="vertical" />}
        >
          {lawSummary && (
            <Stack spacing={1}>
              <Typography sx={{ fontWeight: 600 }}>법령 검증</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Chip label={`적합 ${lawSummary.statusCounts["적합"]}`} color="success" size="small" />
                <Chip label={`보완 ${lawSummary.statusCounts["보완"]}`} color="warning" size="small" />
                <Chip label={`부적합 ${lawSummary.statusCounts["부적합"]}`} color="error" size="small" />
                <Chip
                  label={`적합률 ${lawSummary.fitPercent}%`}
                  variant="outlined"
                  size="small"
                />
              </Stack>
              <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                위험도 최고 {lawSummary.worstRisk || "-"} · 부족 항목 {lawIssueCounts.missing}건 · 위반 가능성 {lawIssueCounts.violations}건
              </Typography>
            </Stack>
          )}

          {compareSummary && (
            <Stack spacing={1}>
              <Typography sx={{ fontWeight: 600 }}>공고문·초안 비교</Typography>
              <Typography sx={{ color: "text.secondary" }}>
                목차 충족률 {compareSummary.tocPercent ?? "-"}% / 기능 충족률 {compareSummary.featurePercent ?? "-"}%
              </Typography>
              <Chip
                label={`종합 충족률 ${compareSummary.combined ?? "-" }%`}
                variant="outlined"
                size="small"
              />
              <Typography sx={{ color: "text.secondary", fontSize: 13 }}>
                누락 섹션 {compareIssueCounts.missingSections}건 · 기능 불일치 {compareIssueCounts.featureMismatch}건
              </Typography>
            </Stack>
          )}

          {noticePercent !== null && (
            <Stack spacing={1}>
              <Typography sx={{ fontWeight: 600 }}>자가진단</Typography>
              <Typography sx={{ color: "text.secondary" }}>
                평가기준 충족률 {noticePercent}%
              </Typography>
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
