import React, { useEffect, useMemo } from 'react';
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
  CircularProgress,
  LinearProgress,
  Divider,
} from '@mui/material';

import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

import { useFileStore } from '../../../store/useFileStore';
import { useProjectStore } from '../../../store/useProjectStore';
import { useVerifyStore } from '../../../store/useVerifyStore';
import { useNavigate } from 'react-router-dom';
import {
  FEATURE_EXCLUDE_KEYWORDS,
  FEATURE_MERGE_RULES,
  normalizeFeatureLabel,
  buildNormalizedMissingFeatureList,
} from '../../../utils/verifyUtils';

// =======================================================
// 🚀 공고문 비교 대시보드 (초안 검증 결과)
// =======================================================
function AnnouncementCompareDashboard({ result, noticeEval }) {
  if (!result) return null;

  const missingSections = result?.missing_sections || [];

  // 원본 데이터
  const rawMissingFeatures = result?.feature_mismatch || [];
  const mapped = result?.mapped_sections || [];
  const rawSectionDetails = result?.section_analysis?.details || [];
  const rawFeatureDetails = result?.feature_analysis?.details || [];

  // 🔹 백엔드에서 계산해 준 progress 정보
  const tocProgress = result?.toc_progress || {};
  const featureProgress = result?.feature_progress || {};

  const tocPercent =
    typeof tocProgress.progress_percent === 'number'
      ? tocProgress.progress_percent
      : null;

  const featurePercent =
    typeof featureProgress.progress_percent === 'number'
      ? featureProgress.progress_percent
      : null;

  // 🔹 공고문 요구사항 충족률 = (목차 기준 + 세부 요구사항 기준) 평균
  let coverageRate = 0;
  let metricCount = 0;
  if (tocPercent !== null) {
    coverageRate += tocPercent;
    metricCount += 1;
  }
  if (featurePercent !== null) {
    coverageRate += featurePercent;
    metricCount += 1;
  }
  coverageRate = metricCount > 0 ? Math.round(coverageRate / metricCount) : 0;

  // 🔹 부족/불일치 feature 이름 정리
  const missingFeatures = buildNormalizedMissingFeatureList(rawMissingFeatures);

  const sectionDetails = rawSectionDetails;

  // 🔹 섹션 상세 상태 분리 (partial / missing)
  const partialSectionDetails = sectionDetails.filter(
    (item) => item.status === 'partial',
  );
  const missingSectionDetails = sectionDetails.filter(
    (item) => item.status === 'missing',
  );

  // 🔹 세부 조건 상세에서도
  //   - EXCLUDE 키워드 들어간 건 숨기고
  //   - 사업기간 / 주요 추진일정 등은 하나의 feature로 합치기
  const mergedFeatureMap = {};

  rawFeatureDetails.forEach((item) => {
    if (!item?.feature) return;

    const rawLabel =
      typeof item.feature === 'string'
        ? item.feature
        : String(item.feature ?? '');

    // 숨길 키워드면 제외
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

  // 🔹 개수 요약 (대략적인 "충족/보완 필요 항목 수" 표현용)
  const tocTotal = tocProgress.total_sections ?? 0;
  const tocWritten = tocProgress.written_sections ?? 0;
  const tocMissingCount = Math.max(tocTotal - tocWritten, 0);

  const featOk = featureProgress.ok_features ?? 0;
  const featPartial = featureProgress.partial_features ?? 0;
  const featMissing = featureProgress.missing_features ?? 0;

  const includedCount = tocWritten + featOk;
  const missingCount = tocMissingCount + featPartial + featMissing;

  // 🔹 도넛 차트 데이터 (충족 vs 보완 필요)
  const chartData = [
    { name: '충족', value: coverageRate },
    { name: '보완 필요', value: Math.max(100 - coverageRate, 0) },
  ];

  const COLORS = ['#4caf50', '#f44336'];

  return (
    <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* ✅ 상단 요약 카드 (퍼센트 + 그래프) */}
      <Card>
        <CardContent>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={4}
            alignItems="center"
          >
            {/* 왼쪽: 퍼센트 + 진행바 + 카운트 */}
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                초안 vs 공고문 매칭 요약
              </Typography>
              <Typography
                variant="body2"
                sx={{ mt: 1, color: 'text.secondary' }}
              >
                공고문에서 요구하는 형식(목차)과 세부 조건이 초안에 얼마나
                반영되어 있는지 한눈에 확인할 수 있습니다.
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Typography
                  variant="h3"
                  sx={{ fontWeight: 800, lineHeight: 1.1 }}
                >
                  {coverageRate}%
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ color: 'text.secondary', mt: 0.5 }}
                >
                  공고문 요구사항 충족률
                </Typography>

                <LinearProgress
                  variant="determinate"
                  value={coverageRate}
                  sx={{
                    mt: 1.5,
                    height: 8,
                    borderRadius: 999,
                  }}
                />
              </Box>

              <Stack
                direction="row"
                spacing={1.5}
                sx={{ mt: 2 }}
                flexWrap="wrap"
              >
                <Chip
                  icon={<CheckCircleOutlineIcon />}
                  color="success"
                  label={`충족 항목 약 ${includedCount}개`}
                  size="small"
                />
                <Chip
                  icon={<ErrorOutlineIcon />}
                  color="error"
                  variant="outlined"
                  label={`보완 필요 항목 약 ${missingCount}개`}
                  size="small"
                />
              </Stack>

              {/* 세부 수치 한 줄 요약 */}
              <Typography
                variant="caption"
                sx={{ mt: 1, display: 'block', color: 'text.secondary' }}
              >
                · 목차: {tocWritten}개 섹션 작성 / 총 {tocTotal}개 섹션
                <br />
              </Typography>
            </Box>

            {/* 오른쪽: 도넛 차트 */}
            <Box
              sx={{
                width: 260,
                height: 230,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {metricCount === 0 ? (
                <Typography sx={{ color: 'text.secondary' }}>
                  비교 가능한 항목이 없습니다.
                </Typography>
              ) : (
                <PieChart width={260} height={230}>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                  >
                    {chartData.map((entry, idx) => (
                      <Cell key={idx} fill={COLORS[idx]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              )}
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* 🔵 공고문 평가기준 자가진단 (매칭 요약 바로 아래) */}
      {noticeEval && <NoticeCriteriaSelfCheck data={noticeEval} />}

      {/* 섹션별 상세 분석 */}
      {sectionDetails.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              섹션별 상세 분석
            </Typography>
            <Typography
              variant="body2"
              sx={{ mt: 0.5, mb: 1.5, color: 'text.secondary' }}
            >
              공고문의 큰 목차 단위(섹션)를 기준으로, 왜 부족한지 / 어떻게
              보완하면 좋은지에 대한 설명입니다.
            </Typography>

            {sectionDetails.map((item, i) => (
              <Accordion key={i} sx={{ boxShadow: 'none' }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography sx={{ fontWeight: 600 }}>
                      {item.section}
                    </Typography>
                    {item.status && (
                      <Chip
                        size="small"
                        variant="outlined"
                        label={item.status}
                        color={
                          item.status === 'missing'
                            ? 'error'
                            : item.status === 'partial'
                            ? 'warning'
                            : 'default'
                        }
                      />
                    )}
                  </Stack>
                </AccordionSummary>

                <AccordionDetails>
                  <Typography sx={{ mt: 1 }}>
                    <b>이유:</b> {item.reason}
                  </Typography>
                  <Typography sx={{ mt: 1 }}>
                    <b>보완 제안:</b> {item.suggestion}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 세부 조건별 분석 */}
      {featureDetails.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              세부 조건별 분석
            </Typography>
            <Typography
              variant="body2"
              sx={{ mt: 0.5, mb: 1.5, color: 'text.secondary' }}
            >
              공고문에서 추출한 세부 조건(지원대상, 사업기간, 예산 조건 등)을
              기준으로, 초안이 공고문 조건을 얼마나 정확하게 반영하고 있는지
              분석한 결과입니다. (문의처·공고기관·접수기관 등 안내성 정보는
              리포트에서 제외됩니다.)
            </Typography>

            {featureDetails.map((item, i) => (
              <Accordion key={i} sx={{ boxShadow: 'none' }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Stack direction="row" spacing={1}>
                    <Typography sx={{ fontWeight: 600 }}>
                      {item.feature}
                    </Typography>
                  </Stack>
                </AccordionSummary>

                <AccordionDetails>
                  <Typography sx={{ mt: 1 }}>
                    <b>이유:</b> {item.reason}
                  </Typography>
                  <Typography sx={{ mt: 1 }}>
                    <b>보완 제안:</b> {item.suggestion}
                  </Typography>
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
// 🚀 공고 평가기준 자가진단 대시보드
// =======================================================
function NoticeCriteriaSelfCheck({ data }) {
  if (!data) return null;

  const { block_name, total_score, total_max_score, percent, items = [] } = data;

  const percentValue =
    typeof percent === 'number'
      ? Math.max(0, Math.min(percent, 100))
      : total_max_score
      ? Math.round((total_score / total_max_score) * 100)
      : null;

  const statusColor = (status) => {
    if (!status) return 'default';
    if (status.includes('우수') || status.includes('적합')) return 'success';
    if (status.includes('보통') || status.includes('보완')) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* 상단 요약 카드 */}
      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={4}>
            {/* 왼쪽: 설명 */}
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                {block_name || '공고문 평가기준 자가진단'}
              </Typography>
              <Typography
                variant="body2"
                sx={{ mt: 1, color: 'text.secondary' }}
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
                  bgcolor: 'rgba(25, 118, 210, 0.03)',
                  border: '1px solid rgba(25, 118, 210, 0.15)',
                }}
              >
                <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                  · 총점 기준으로 약{' '}
                  <b>
                    {percentValue !== null ? `${percentValue}%` : '-'}
                  </b>
                  수준의 경쟁력을 보이고 있습니다.
                  <br />· 각 평가 항목별 강점과 보완 포인트를 참고해 초안을
                  수정하면, 실제 평가 점수 향상에 도움이 됩니다.
                </Typography>
              </Box>
            </Box>

            {/* 오른쪽: 점수 / 퍼센트 */}
            <Box
              sx={{
                width: 260,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
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
                    sx={{ color: 'text.secondary', mt: 0.5 }}
                  >
                    평가기준 달성도
                  </Typography>

                  <LinearProgress
                    variant="determinate"
                    value={percentValue}
                    sx={{
                      mt: 1.5,
                      width: '100%',
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
                <Typography sx={{ color: 'text.secondary' }}>
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
              sx={{ mt: 0.5, mb: 1.5, color: 'text.secondary' }}
            >
              각 평가 항목에 대해 현재 초안이 어떤 점에서 강점이 있고, 어떤
              부분을 보완하면 좋은지 정리한 내용입니다.
            </Typography>

            {items.map((item, idx) => (
              <Accordion key={idx} sx={{ boxShadow: 'none' }}>
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
                      <Typography sx={{ whiteSpace: 'pre-line' }}>
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
                      <Typography sx={{ whiteSpace: 'pre-line' }}>
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
// 🚀 법령 검증 대시보드
// =======================================================
function LawVerifyDashboard({ results }) {
    const hasResults = results && Object.keys(results).length > 0;

    const {
        statusCounts,
        overallStatus,
        overallRisk,
        actionItems,
        sortedEntries,
        violationItems,
        overallViolationSeverity,
    } = useMemo(() => {
        if (!hasResults) {
            return {
                statusCounts: {},
                overallStatus: null,
                overallRisk: null,
                actionItems: [],
                sortedEntries: [],
                violationItems: [],
                overallViolationSeverity: null,
            };
        }

        const statusCounts = { 적합: 0, 보완: 0, 부적합: 0 };
        const actionItems = [];
        const violationItems = [];
        const entries = Object.entries(results);

        const SEVERITY_ORDER = { LOW: 1, MEDIUM: 2, HIGH: 3 };

        let overallViolationSeverity = null;

        entries.forEach(([key, r]) => {
            if (!r) return;

            if (r.status && statusCounts[r.status] !== undefined) {
                statusCounts[r.status] += 1;
            }

            // 부족한 요소 → 보완 항목
            if (Array.isArray(r.missing)) {
                r.missing.forEach((m) => {
                    actionItems.push({
                        focusKey: key,
                        focusLabel: r.label,
                        text: m,
                    });
                });
            }

            // 법령 위반/리스크 항목
            if (Array.isArray(r.violations)) {
                r.violations.forEach((v) => {
                    const sev = v.severity || 'MEDIUM';

                    violationItems.push({
                        focusKey: key,
                        focusLabel: r.label,
                        lawName: v.law_name,
                        articleNo: v.article_no,
                        articleTitle: v.article_title,
                        severity: sev,
                        violationType: v.violation_type,
                        summary: v.reason,
                        recommendation: v.recommendation,
                    });

                    if (!overallViolationSeverity) {
                        overallViolationSeverity = sev;
                    } else {
                        if (SEVERITY_ORDER[sev] > SEVERITY_ORDER[overallViolationSeverity]) {
                            overallViolationSeverity = sev;
                        }
                    }
                });
            }
        });

        const STATUS_ORDER = { 적합: 1, 보완: 2, 부적합: 3 };
        const RISK_ORDER = { LOW: 1, MEDIUM: 2, HIGH: 3 };

        const sortedEntries = entries.sort(([, a], [, b]) => {
            const aStatus = a?.status || '적합';
            const bStatus = b?.status || '적합';
            const aRisk = a?.risk_level || 'LOW';
            const bRisk = b?.risk_level || 'LOW';

            const statusDiff = STATUS_ORDER[bStatus] - STATUS_ORDER[aStatus];
            if (statusDiff !== 0) return statusDiff;

            return RISK_ORDER[bRisk] - RISK_ORDER[aRisk];
        });

        const overallStatus = sortedEntries[0]?.[1]?.status || null;
        const overallRisk = sortedEntries[0]?.[1]?.risk_level || null;

        return {
            statusCounts,
            overallStatus,
            overallRisk,
            actionItems,
            sortedEntries,
            violationItems,
            overallViolationSeverity,
        };
    }, [results, hasResults]);

    const STATUS_COLORS = { 적합: '#4caf50', 보완: '#ffb300', 부적합: '#f44336' };
    const statusChartData = Object.entries(statusCounts)
        .filter(([, count]) => count > 0)
        .map(([name, value]) => ({ name, value }));

    const JUDGMENT_LABELS = {
        NO_ISSUE: '법령 위반 징후 없음',
        POTENTIAL_VIOLATION: '법령 위반 가능성 있음',
        POSSIBLE_ISSUE: '법령 리스크 가능성 있음',
        UNCLEAR: '법령 위반 판단 어려움',
    };

    const JUDGMENT_COLORS = {
        NO_ISSUE: 'success',
        POTENTIAL_VIOLATION: 'error',
        POSSIBLE_ISSUE: 'warning',
        UNCLEAR: 'default',
    };

    const SEVERITY_LABELS = {
        LOW: '위험도 낮음',
        MEDIUM: '위험도 보통',
        HIGH: '위험도 높음',
    };

    const SEVERITY_CHIP_COLORS = {
        LOW: 'success',
        MEDIUM: 'warning',
        HIGH: 'error',
    };

    const totalFocusCount = sortedEntries.length;
    const violationCount = violationItems.length;

    const highRiskFocuses = sortedEntries
        .filter(
            ([, r]) =>
                r?.status === '부적합' ||
                r?.risk_level === 'HIGH' ||
                (r?.violations && r.violations.length > 0),
        )
        .slice(0, 3)
        .map(([, r]) => r.label);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 3 }}>
            {/* 요약 카드 */}
            <Card>
                <CardContent>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={3}>
                        {/* 🔹 왼쪽: 종합 요약 + 항목별 한줄 요약 */}
                        <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 700 }}>
                                법령 검증 종합 의견
                            </Typography>

                            {/* 1) 숫자 기반 간단 총평 */}
                            <Stack spacing={1} sx={{ mt: 1.5, mb: 2 }}>
                                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                                    총 {totalFocusCount}개 관점 중{' '}
                                    <b>적합 {statusCounts.적합 || 0}개</b>,{' '}
                                    <b>보완 {statusCounts.보완 || 0}개</b>,{' '}
                                    <b>부적합 {statusCounts.부적합 || 0}개</b>로 평가되었습니다.
                                </Typography>

                                {(overallStatus || overallViolationSeverity) && (
                                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                                        {overallStatus === '적합' && '전반적으로 법령 및 지침에 잘 부합하는 초안으로 판단되며, 일부 항목만 보완하면 제출에 무리가 없는 수준입니다.'}
                                        {overallStatus === '보완' && '전반적으로는 큰 위반 소지는 없으나, 일부 항목에서 법령·지침과의 정합성을 높이기 위한 내용 보완이 필요한 상태입니다.'}
                                        {overallStatus === '부적합' && '여러 관점에서 법령 및 지침과 충돌 가능성이 있어, 제출 전 구조적인 수정이 요구되는 수준으로 판단됩니다.'}

                                        {overallViolationSeverity && (
                                            <>
                                                {' '}전반적인 법령 위반 가능성은 <b>{SEVERITY_LABELS[overallViolationSeverity]}</b> 수준입니다.
                                            </>
                                        )}
                                        {violationCount > 0 && (
                                            <> (위반 가능성 의심 항목 {violationCount}건 탐지)</>
                                        )}
                                    </Typography>
                                )}
                            </Stack>

                            {/* 구분선 */}
                            <Divider sx={{ my: 1.5 }} />

                            {/* 2) 처음처럼: 관점별 제목 + 간단 한 줄 설명 */}
                            <Stack spacing={1.2}>
                                {sortedEntries.map(([key, r]) => {
                                    // 한 줄 요약용 텍스트 선택: brief → violation_summary → reason
                                    const baseText =
                                        (r.brief && String(r.brief)) ||
                                        (r.violation_summary && String(r.violation_summary)) ||
                                        (r.reason && String(r.reason)) ||
                                        '';

                                    // 첫 번째 유의미한 줄만 추출
                                    const firstLine =
                                        baseText
                                            .split('\n')
                                            .map((line) => line.trim())
                                            .filter((line) => line.length > 0)[0] || '';

                                    // 너무 길면 살짝 잘라주기 (80자 기준)
                                    const shortText =
                                        firstLine.length > 80
                                            ? firstLine.slice(0, 80) + '…'
                                            : firstLine;

                                    return (
                                        <Box key={key}>
                                            <Typography sx={{ fontWeight: 600 }}>
                                                {r.label}
                                            </Typography>
                                            {shortText && (
                                                <Typography
                                                    variant="body2"
                                                    sx={{ ml: 1, color: 'text.secondary' }}
                                                >
                                                    {shortText}
                                                </Typography>
                                            )}
                                        </Box>
                                    );
                                })}
                            </Stack>
                        </Box>

                        {/* 🔵 오른쪽: 도넛 차트 + 리스크 Chip */}
                        <Box sx={{ width: 260 }}>
                            {statusChartData.length === 0 ? (
                                <Box
                                    sx={{
                                        height: 230,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                    }}
                                >
                                    <Typography sx={{ textAlign: 'center', color: 'text.secondary' }}>
                                        검증 결과 없음
                                    </Typography>
                                </Box>
                            ) : (
                                <Box
                                    sx={{
                                        width: 260,
                                        height: 230,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
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
                                                <Cell
                                                    key={idx}
                                                    fill={STATUS_COLORS[entry.name] || '#999'}
                                                />
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
                                        label={`전체 리스크: ${overallRisk}`}
                                    />
                                )}

                                {overallViolationSeverity && (
                                    <Chip
                                        size="small"
                                        variant="outlined"
                                        label={`법령 위반 가능성: ${SEVERITY_LABELS[overallViolationSeverity]}`}
                                        color={SEVERITY_CHIP_COLORS[overallViolationSeverity]}
                                    />
                                )}
                            </Stack>
                        </Box>
                    </Stack>
                </CardContent>
            </Card>

            {/* 보완이 필요한 핵심 항목 */}
            {actionItems.length > 0 && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            보완이 필요한 핵심 항목
                        </Typography>

                        <List dense>
                            {actionItems.map((item, idx) => (
                                <ListItem key={idx}>
                                    <ListItemText
                                        primary={
                                            <>
                                                <Typography
                                                    variant="caption"
                                                    sx={{ fontWeight: 600, mr: 1 }}
                                                >
                                                    [{item.focusLabel}]
                                                </Typography>
                                                {item.text}
                                            </>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </CardContent>
                </Card>
            )}

            {/* 관점별 상세 분석 (아래는 그대로 유지) */}
            <Card>
                <CardContent>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        관점별 상세 분석
                    </Typography>

                    {sortedEntries.map(([key, r]) => (
                        <Accordion key={key} sx={{ boxShadow: 'none' }}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Stack direction="row" spacing={1} alignItems="center">
                                    <Typography sx={{ fontWeight: 600 }}>{r.label}</Typography>

                                    {r.status && (
                                        <Chip
                                            size="small"
                                            label={r.status}
                                            color={
                                                r.status === '적합'
                                                    ? 'success'
                                                    : r.status === '보완'
                                                    ? 'warning'
                                                    : 'error'
                                            }
                                        />
                                    )}

                                    {r.risk_level && (
                                        <Chip
                                            size="small"
                                            variant="outlined"
                                            label={r.risk_level}
                                        />
                                    )}

                                    {r.violation_judgment && (
                                        <Chip
                                            size="small"
                                            variant="outlined"
                                            label={
                                                JUDGMENT_LABELS[r.violation_judgment] ||
                                                r.violation_judgment
                                            }
                                            color={
                                                JUDGMENT_COLORS[r.violation_judgment] || 'default'
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
                                                bgcolor: 'rgba(244, 67, 54, 0.04)',
                                                border: '1px solid rgba(244, 67, 54, 0.3)',
                                            }}
                                        >
                                            <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                                                법령 위반 가능성 요약
                                            </Typography>
                                            <Typography
                                                variant="body2"
                                                sx={{ whiteSpace: 'pre-line' }}
                                            >
                                                {r.violation_summary}
                                            </Typography>
                                        </Box>
                                    )}

                                {/* 부족한 요소 */}
                                {r.missing?.length > 0 && (
                                    <Box sx={{ mb: 2 }}>
                                        <Typography sx={{ fontWeight: 600 }}>부족한 요소</Typography>
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
                                        <Typography sx={{ fontWeight: 600 }}>보완 제안</Typography>
                                        <Typography sx={{ whiteSpace: 'pre-line' }}>
                                            {r.suggestion}
                                        </Typography>
                                    </Box>
                                )}

                                {/* 관련 법령 */}
                                {r.related_laws?.length > 0 && (
                                    <Box>
                                        <Typography sx={{ fontWeight: 600 }}>관련 법령</Typography>
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
        </Box>
    );
}


// =======================================================
// 🚀 VerifyView Main
// =======================================================
function VerifyView3() {
  const filePath = useFileStore((state) => state.filePath);
  const project = useProjectStore((state) => state.project);
  const projectIdx = project?.projectIdx;
  const navigate = useNavigate();

  const {
    loading,
    progress,
    text,
    results,
    compareResult,
    activeTab,
    loadDraft,
    verifyAll,
    compareAll,
    noticeEvalResult,
    runFullVerify,
  } = useVerifyStore();

  // 🔹 종합 리포트 이동 가능 여부 (검증 결과가 있어야 의미 있음)
  const isReportReady =
    (results && Object.keys(results).length > 0) || !!compareResult;

  // 🔹 초안 로딩 (filePath 변경 시마다)
  useEffect(() => {
    if (!filePath) return;
    loadDraft(filePath);
  }, [filePath, loadDraft]);

  const handleVerifyAllClick = () => {
    if (!projectIdx) {
      alert('프로젝트 정보(projectIdx)가 없습니다.');
      console.error('[VerifyView3] projectIdx 없음:', projectIdx);
      return;
    }
    verifyAll(projectIdx);
  };

  // ✅ 초안 검증 버튼 클릭 시 (통합 그래프 실행)
  const handleCompareClick = async () => {
    // projectIdx 없으면 둘 다 의미 없으니까 가드 한 번
    if (!projectIdx) {
      alert('프로젝트 정보(projectIdx)가 없습니다.');
      console.error('[VerifyView3] projectIdx 없음:', projectIdx);
      return;
    }

    await compareAll(projectIdx);
  };

  const handleFullVerifyClick = async () => {
    if (!projectIdx) {
      alert('프로젝트 정보(projectIdx)가 없습니다.');
      console.error('[VerifyView3] projectIdx 없음:', projectIdx);
      return;
    }
    await runFullVerify(projectIdx);
  };

  const handleReportClick = () => {
    navigate('/works/verify/report');
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* 🔥 중앙 로딩 오버레이 */}
      {loading && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            bgcolor: 'rgba(255,255,255,0.7)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
          }}
        >
          <CircularProgress size={60} />
          <Typography sx={{ mt: 2, fontSize: 18, fontWeight: 600 }}>
            분석 중... {progress}%
          </Typography>
        </Box>
      )}

      {/* Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            검증
          </Typography>
          <Typography sx={{ color: 'text.secondary' }}>
            기획서 초안을 기반으로 법령 준수 및 공고문 요구사항 충족 여부를
            자동 점검합니다.
          </Typography>
        </Box>

        <Stack direction="row" spacing={2}>
          <Button variant="contained" onClick={handleVerifyAllClick}>
            법령 검증
          </Button>

          <Button variant="outlined" onClick={handleCompareClick}>
            초안 검증
          </Button>

          {/* <Button variant="contained" color="secondary" onClick={handleFullVerifyClick}>
            통합 검증
          </Button> */}

          <Button
            variant="outlined"
            onClick={handleReportClick}
            disabled={!isReportReady}
          >
            종합 리포트
          </Button>
        </Stack>
      </Stack>

      {!text && (
        <Typography sx={{ mt: 2, color: 'text.secondary' }}>
          초안을 불러오는 중입니다…
        </Typography>
      )}

      {activeTab === 'law' &&
        results &&
        Object.keys(results).length > 0 && (
          <LawVerifyDashboard results={results} />
        )}

      {activeTab === 'compare' && compareResult && (
        <AnnouncementCompareDashboard
          result={compareResult}
          noticeEval={noticeEvalResult}
        />
      )}
    </Box>
  );
}

export default VerifyView3;
