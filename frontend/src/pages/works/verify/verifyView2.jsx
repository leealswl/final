import React, { useEffect, useMemo, useState } from 'react';
import { Box, Card, CardContent, Chip, Typography, Stack, Divider, Accordion, AccordionSummary, AccordionDetails, List, ListItem, ListItemText, Button, CircularProgress } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { draftApi } from '../../../utils/draftApi';
import { tiptapDocToPlainText } from '../../../utils/tiptapText';
import { verifyLawSection } from '../../../utils/fastapi';
import { useFileStore } from '../../../store/useFileStore';

// =============================
// FOCUSES 정의
// =============================
const FOCUSES = [
    {
        key: 'purpose',
        label: '사업 목적/필요성/국가 R&D 기본 원칙',
        focus: '국가연구개발사업의 기본 원칙과 정책 방향을 기준으로, 사업의 목적과 필요성이 타당한지 검토하세요.',
    },
    {
        key: 'budget',
        label: '연구개발비·예산',
        focus: '연구개발비 및 예산(직접비·간접비·자부담 등) 편성이 관련 법령과 지침에 부합하는지, 항목별 배분과 산정 근거가 타당한지 검토하세요.',
    },
    {
        key: 'structure',
        label: '수행체계·책임·참여제한',
        focus: '수행기관·주관기관·참여기관의 역할과 책임이 명확한지, 참여제한·격리의무 등 관련 규정을 충족하는지 검토하세요.',
    },
    {
        key: 'outcome',
        label: '성과지표·평가·성과관리',
        focus: '성과지표, 평가 방식, 성과관리·사후관리 체계가 관련 지침에 맞게 구체적으로 설계되어 있는지 검토하세요.',
    },
    // {
    //   key: 'privacy',
    //   label: '개인정보 보호·정보보호',
    //   focus:
    //     '개인정보 보호법 및 정보통신망법 등 관련 법령을 고려하여, 개인정보 수집·이용·제공·보관·파기 절차와 정보보호 체계가 적정한지 검토하세요.',
    // },
];

// =============================
// 대시보드용 상수/함수
// =============================
const STATUS_ORDER = { 부적합: 3, 보완: 2, 적합: 1 };
const RISK_ORDER = { HIGH: 3, MEDIUM: 2, LOW: 1 };
const STATUS_COLORS = { 적합: '#4caf50', 보완: '#ffb300', 부적합: '#f44336' };

function getOverallStatus(results) {
    let maxStatus = null;
    Object.values(results || {}).forEach((r) => {
        if (!r || !r.status) return;
        const s = r.status;
        if (!maxStatus || STATUS_ORDER[s] > STATUS_ORDER[maxStatus]) {
            maxStatus = s;
        }
    });
    return maxStatus;
}

function getOverallRisk(results) {
    let maxRisk = null;
    Object.values(results || {}).forEach((r) => {
        if (!r || !r.risk_level) return;
        const rl = r.risk_level;
        if (!maxRisk || RISK_ORDER[rl] > RISK_ORDER[maxRisk]) {
            maxRisk = rl;
        }
    });
    return maxRisk;
}

// =============================
// LawVerifyDashboard 컴포넌트
// =============================
function LawVerifyDashboard({ results }) {
    const hasResults = results && Object.keys(results).length > 0;

    const { statusCounts, overallStatus, overallRisk, actionItems, sortedEntries } = useMemo(() => {
        if (!hasResults) {
            return {
                statusCounts: {},
                overallStatus: null,
                overallRisk: null,
                actionItems: [],
                sortedEntries: [],
            };
        }

        const statusCounts = { 적합: 0, 보완: 0, 부적합: 0 };
        const actionItems = [];
        const entries = Object.entries(results);

        entries.forEach(([key, r]) => {
            if (!r) return;

            if (r.status && statusCounts[r.status] !== undefined) {
                statusCounts[r.status] += 1;
            }

            if (Array.isArray(r.missing)) {
                r.missing.forEach((m) => {
                    actionItems.push({
                        focusKey: key,
                        focusLabel: r.label,
                        text: m,
                    });
                });
            }
        });

        const overallStatus = getOverallStatus(results);
        const overallRisk = getOverallRisk(results);

        const sortedEntries = entries.sort(([, a], [, b]) => {
            const aStatus = a?.status || '적합';
            const bStatus = b?.status || '적합';
            const aRisk = a?.risk_level || 'LOW';
            const bRisk = b?.risk_level || 'LOW';

            const statusDiff = (STATUS_ORDER[bStatus] || 0) - (STATUS_ORDER[aStatus] || 0);
            if (statusDiff !== 0) return statusDiff;

            return (RISK_ORDER[bRisk] || 0) - (RISK_ORDER[aRisk] || 0);
        });

        return {
            statusCounts,
            overallStatus,
            overallRisk,
            actionItems,
            sortedEntries,
        };
    }, [results, hasResults]);

    const statusChartData = useMemo(() => {
        if (!hasResults) return [];
        return Object.entries(statusCounts)
            .filter(([, count]) => count > 0)
            .map(([name, value]) => ({ name, value }));
    }, [statusCounts, hasResults]);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 3 }}>
            {/* 1. 상단 요약 카드 + 도넛 차트 */}
            <Card>
                <CardContent>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="stretch" justifyContent="space-between">
                        {/* 왼쪽: 관점별 요약 문장만 */}
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                            <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                                summary
                            </Typography>
                            {/* <Typography
                variant="body2"
                sx={{ color: 'text.secondary', mb: 1.5 }}
              >
                각 검증 관점에서 나온 핵심 코멘트만 모아 보여줍니다. 상태/리스크 표시는
                상세 영역에서 확인할 수 있습니다.
              </Typography> */}

                            {hasResults && (
                                <Box sx={{ mt: 1.5 }}>
                                    <Stack spacing={1.2}>
                                        {sortedEntries.map(([key, r]) => (
                                            <Box key={key}>
                                                {/* 관점 이름 */}
                                                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.3 }}>
                                                    {r.label}
                                                </Typography>
                                                {/* 설명(reason)만 출력 (상태/리스크 문구 X) */}
                                                {r.reason && (
                                                    <Typography
                                                        variant="body2"
                                                        sx={{
                                                            color: 'text.secondary',
                                                            ml: 0.5,
                                                            whiteSpace: 'pre-line',
                                                        }}
                                                    >
                                                        {r.reason}
                                                    </Typography>
                                                )}
                                            </Box>
                                        ))}
                                    </Stack>
                                </Box>
                            )}
                        </Box>

                        {/* 오른쪽: 상태 분포 도넛 + 전체 리스크 간단 표시 */}
                        <Box
                            sx={{
                                flexBasis: 260,
                                height: 230,
                                width: '100%',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                            }}
                        >
                            {statusChartData.length === 0 ? (
                                <Typography variant="body2" sx={{ color: 'text.secondary', textAlign: 'center', mt: 7 }}>
                                    아직 검증 결과가 없습니다.
                                </Typography>
                            ) : (
                                <>
                                    <Box sx={{ width: '100%', height: 190 }}>
                                        <ResponsiveContainer>
                                            <PieChart>
                                                <Pie data={statusChartData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={80} paddingAngle={3}>
                                                    {statusChartData.map((entry, index) => (
                                                        <Cell key={`${entry.name}-${index}`} fill={STATUS_COLORS[entry.name] || '#90a4ae'} />
                                                    ))}
                                                </Pie>
                                                <Tooltip />
                                                <Legend />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </Box>
                                    {overallRisk && <Chip size="small" variant="outlined" label={`전체 리스크: ${overallRisk}`} sx={{ mt: 0.5 }} />}
                                </>
                            )}
                        </Box>
                    </Stack>
                </CardContent>
            </Card>

            {/* 2. 보완이 필요한 핵심 항목 모아보기 */}
            {hasResults && actionItems.length > 0 && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                            보완이 필요한 핵심 항목
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                            여러 관점에서 공통으로 부족하다고 언급된 항목을 모아보는 영역입니다. 아래 항목을 중심으로 기획서를 보완해 보세요.
                        </Typography>
                        <List dense sx={{ pl: 0 }}>
                            {actionItems.map((item, idx) => (
                                <ListItem key={`${item.focusKey}-${idx}`} sx={{ py: 0.4 }}>
                                    <ListItemText
                                        primary={
                                            <>
                                                <Typography
                                                    variant="caption"
                                                    sx={{
                                                        fontWeight: 600,
                                                        mr: 1,
                                                        color: 'text.secondary',
                                                    }}
                                                >
                                                    [{item.focusLabel}]
                                                </Typography>
                                                <Typography variant="body2" component="span" sx={{ whiteSpace: 'pre-line' }}>
                                                    {item.text}
                                                </Typography>
                                            </>
                                        }
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </CardContent>
                </Card>
            )}

            {/* 3. 관점별 상세 카드 (여기는 칩 그대로 유지) */}
            <Card>
                <CardContent>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        관점별 상세 분석
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                        각 관점을 펼쳐 부족한 요소, 보완 제안, 관련 법령을 확인하세요.
                    </Typography>
                    <Divider sx={{ mb: 1 }} />
                    {!hasResults ? (
                        <Typography variant="body2" sx={{ color: 'text.secondary', mt: 2 }}>
                            검증 결과가 없습니다.
                        </Typography>
                    ) : (
                        sortedEntries.map(([key, r]) => (
                            <Accordion key={key} sx={{ boxShadow: 'none' }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 0 }}>
                                    <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap">
                                        <Typography variant="subtitle1" sx={{ fontWeight: 600, mr: 1 }}>
                                            {r.label}
                                        </Typography>
                                        {r.status && <Chip size="small" label={r.status} color={r.status === '적합' ? 'success' : r.status === '보완' ? 'warning' : 'error'} />}
                                        {r.risk_level && <Chip size="small" label={r.risk_level} variant="outlined" />}
                                    </Stack>
                                </AccordionSummary>
                                <AccordionDetails sx={{ px: 0 }}>
                                    {Array.isArray(r.missing) && r.missing.length > 0 && (
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                                                부족한 요소
                                            </Typography>
                                            <List dense sx={{ pl: 2 }}>
                                                {r.missing.map((m, idx) => (
                                                    <ListItem key={idx} sx={{ py: 0.3 }}>
                                                        <ListItemText primary={<Typography variant="body2">{m}</Typography>} />
                                                    </ListItem>
                                                ))}
                                            </List>
                                        </Box>
                                    )}

                                    {r.suggestion && (
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                                                보완 제안
                                            </Typography>
                                            <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                                                {r.suggestion}
                                            </Typography>
                                        </Box>
                                    )}

                                    {/* evidence는 UI에서 숨김 처리 (필요하면 주석 해제해서 사용 가능)
                  {r.evidence && (
                    <Box sx={{ mb: 2 }}>
                      <Typography
                        variant="subtitle2"
                        sx={{ fontWeight: 600, mb: 0.5 }}
                      >
                        기획서상 근거/문제 지점
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{ whiteSpace: 'pre-line' }}
                      >
                        {r.evidence}
                      </Typography>
                    </Box>
                  )} */}

                                    {Array.isArray(r.related_laws) && r.related_laws.length > 0 && (
                                        <Box sx={{ mb: 1 }}>
                                            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                                                관련 법령
                                            </Typography>
                                            <Stack direction="row" flexWrap="wrap" gap={1}>
                                                {r.related_laws.map((law, idx) => (
                                                    <Chip key={idx} size="small" label={`${law.law_name} ${law.article_title}`} variant="outlined" />
                                                ))}
                                            </Stack>
                                        </Box>
                                    )}
                                </AccordionDetails>
                            </Accordion>
                        ))
                    )}
                </CardContent>
            </Card>
        </Box>
    );
}

// =============================
// 메인 VerifyView 컴포넌트
// =============================
function VerifyView() {
    const [text, setText] = useState('');
    const [results, setResults] = useState({});
    const [loading, setLoading] = useState(false);
    const [showDashboard, setShowDashboard] = useState(false);
    const [verified, setVerified] = useState(false);
    const filePath = useFileStore((state) => state.filePath);

    useEffect(() => {
        (async () => {
            try {
                const docJson = await draftApi(filePath);
                const plain = tiptapDocToPlainText(docJson);
                console.log('초안 텍스트:', plain);
                setText(plain);
            } catch (e) {
                console.error('초안 JSON 불러오기 실패', e);
            }
        })();
    }, []);

    const handleVerifyAll = async () => {
        if (!text) {
            alert('초안 텍스트가 없습니다. 먼저 초안을 작성/저장한 뒤 다시 시도해 주세요.');
            return;
        }

        try {
            setLoading(true);
            setResults({});
            setShowDashboard(false);
            setVerified(true);

            const settled = await Promise.allSettled(
                FOCUSES.map((f) =>
                    verifyLawSection({ text, focus: f.focus }).then((apiRes) => ({
                        key: f.key,
                        label: f.label,
                        data: apiRes.data,
                    })),
                ),
            );

            const next = {};

            settled.forEach((res, idx) => {
                const f = FOCUSES[idx];

                if (res.status === 'fulfilled') {
                    next[f.key] = {
                        label: f.label,
                        ...res.value.data,
                    };
                } else {
                    console.error('관점 검증 실패:', f.key, res.reason);
                    next[f.key] = {
                        label: f.label,
                        status: 'error',
                        risk_level: 'UNKNOWN',
                        reason: '이 관점 검증 중 오류가 발생했습니다. 나중에 다시 시도해 주세요.',
                    };
                }
            });

            setResults(next);
            setShowDashboard(true);
        } catch (e) {
            console.error('법령 검증 전체 실패', e);
        } finally {
            setLoading(false);
        }
    };

    const toggleDashboard = () => {
        if (!results || Object.keys(results).length === 0) {
            alert('먼저 검증을 실행해주세요!');
            return;
        }
        setShowDashboard((prev) => !prev);
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* 상단 헤더 + 버튼 영역 */}
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'flex-start', md: 'center' }} justifyContent="space-between" sx={{ mb: 2 }}>
                <Box>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5 }}>
                        검증
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        현재 기획서 초안을 기반으로 예산, 수행체계, 성과관리 등 주요 관점에서 국가 R&D 관련 법령·지침 준수 여부를 자동으로 점검합니다.
                    </Typography>
                </Box>

                <Stack direction="row" spacing={1.5}>
                    {!loading && !verified && (
                        <Button variant="contained" onClick={handleVerifyAll} disabled={loading || !text}>
                            검증 하기
                        </Button>
                    )}
                    {/* <Button
            variant="outlined"
            onClick={toggleDashboard}
            disabled={loading}
          >
            검증 결과 보기
          </Button> */}
                </Stack>
            </Stack>

            {/* 초안이 아직 없을 때 안내 문구 */}
            {!text && (
                <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        초안 텍스트를 불러오는 중이거나 아직 생성되지 않았습니다. 생성/작성 단계에서 기획서를 저장한 후 다시 검증을 실행해 주세요.
                    </Typography>
                </Box>
            )}

            {/* 검증 결과 대시보드 */}
            {showDashboard && (
                <Box sx={{ mt: 3 }}>
                    <LawVerifyDashboard results={results} />
                </Box>
            )}
        </Box>
    );
}

export default VerifyView;
