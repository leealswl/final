import { Box, Paper, Stack, Typography, CircularProgress, Button, Chip, Grid, Modal } from '@mui/material';
import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAnalysisStore } from '../../../store/useAnalysisStore';

/* -----------------------------------------------------
 * 메인 페이지
 * ---------------------------------------------------- */
const AnalyzeDashboard = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const storedResult = useAnalysisStore((state) => state.analysisResult);
    const analysisResult = location.state?.analysisResult || storedResult;
    const analysisData = analysisResult?.data || {};

    console.log('analysisResult: ', analysisResult);
    console.log('analysisData: ', analysisData);

    const featureCards = useMemo(() => {
        return (analysisData.features || []).map((feature, index) => {
            const resultId = feature.result_id ?? index + 1;
            const cardId = `${feature.feature_code || feature.feature_name || 'feature'}_${resultId}`;
            return {
                ...feature,
                result_id: resultId,
                card_id: cardId,
            };
        });
    }, [analysisData.features]);

    // 로딩 중
    if (!analysisResult) {
        return (
            <Stack sx={{ backgroundColor: '#F4F7F9', height: '100vh' }} justifyContent={'center'} alignItems={'center'}>
                <CircularProgress size={60} />
                <Typography sx={{ mt: 3, fontSize: '1.2rem' }}>분석 결과를 불러오는 중입니다...</Typography>
            </Stack>
        );
    }

    return (
        <Stack sx={{ backgroundColor: '#F4F7F9', height: '100vh', overflow: 'auto', p: 4 }}>
            {/* 헤더 */}
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} mb={4} spacing={2}>
                <Box>
                    <Typography fontSize={'2rem'} fontFamily={'Isamanru-Bold'} mb={1}>
                        📊 프로젝트 분석 결과
                    </Typography>
                    <Typography fontFamily={'Pretendard4'} color={'#8C8C8C'}>
                        PALADOC AI가 분석한 프로젝트 요구사항 및 첨부 양식입니다.
                    </Typography>
                </Box>

                <Button variant="contained" size="large" sx={{ backgroundColor: '#262626', '&:hover': { backgroundColor: '#000000' } }} onClick={() => navigate('/works/create')}>
                    생성 페이지로 이동
                </Button>
            </Stack>

            {/* Feature 카드 */}
            {featureCards.length ? (
                <Grid container spacing={2}>
                    {featureCards.map((feature) => (
                        <Grid item size={4} key={feature.card_id}>
                            <FeatureCard feature={feature} />
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <Paper elevation={0} sx={{ p: 6, textAlign: 'center', borderRadius: 3 }}>
                    <Typography fontSize="1.1rem" fontWeight={600}>
                        표시할 Feature 정보가 없습니다
                    </Typography>
                </Paper>
            )}

            {/* 디버깅 JSON */}
            <Paper elevation={0} sx={{ p: 4, borderRadius: 3, mt: 4 }}>
                <Typography fontSize="1.2rem" fontWeight={700} mb={2}>
                    🔍 원본 분석 데이터 (디버깅용)
                </Typography>
                <Box
                    component="pre"
                    sx={{
                        backgroundColor: '#111827',
                        color: '#f5f5f5',
                        p: 3,
                        borderRadius: 2,
                        overflow: 'auto',
                        maxHeight: '320px',
                    }}
                >
                    {JSON.stringify(analysisResult, null, 2)}
                </Box>
            </Paper>
        </Stack>
    );
};

/* -----------------------------------------------------
 * FeatureCard + Modal 상세보기
 * ---------------------------------------------------- */
const FeatureCard = ({ feature }) => {
    const [open, setOpen] = useState(false);

    const metaChips = [
        feature.result_id != null ? `ID: ${feature.result_id}` : null,
        feature.feature_code ? `코드: ${feature.feature_code}` : null,
        typeof feature.vector_similarity === 'number' ? `유사도: ${feature.vector_similarity.toFixed(2)}` : null,
    ].filter(Boolean);

    return (
        <>
            {/* === 카드 === */}
            <Paper
                elevation={1}
                sx={{
                    p: 3,
                    borderRadius: 3,
                    height: 220, // 카드 높이 통일
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    border: '1px solid #f0f0f0',
                    transition: 'all 0.18s ease',
                    '&:hover': {
                        borderColor: '#1677ff',
                        boxShadow: '0px 10px 30px rgba(22, 119, 255, 0.15)',
                    },
                }}
                onClick={() => setOpen(true)}
            >
                <Stack spacing={1.5}>
                    <Typography fontSize="1.1rem" fontWeight={700}>
                        {feature.feature_name || feature.feature_code || 'Feature'}
                    </Typography>

                    {/* 메타 정보 */}
                    {metaChips.length > 0 && (
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                            {metaChips.map((label) => (
                                <Chip key={label} label={label} size="small" sx={{ backgroundColor: '#E6F4FF', color: '#0958d9' }} />
                            ))}
                        </Stack>
                    )}

                    <Typography fontSize="0.85rem" color="#8C8C8C">
                        상세 내용을 확인하려면 클릭하세요.
                    </Typography>
                </Stack>
            </Paper>

            {/* === 상세 팝업 === */}
            <Modal open={open} onClose={() => setOpen(false)}>
                <Box
                    sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        width: 'min(700px, 90%)',
                        bgcolor: 'white',
                        borderRadius: 3,
                        boxShadow: 24,
                        p: 4,
                        maxHeight: '80vh',
                        overflowY: 'auto',
                    }}
                >
                    <Typography fontSize="1.4rem" fontWeight={700} mb={2}>
                        {feature.feature_name || feature.feature_code}
                    </Typography>

                    {feature.summary && <Section title="요약">{feature.summary}</Section>}

                    {Array.isArray(feature.key_points) && feature.key_points.length > 0 && (
                        <Section title="핵심 포인트">
                            {feature.key_points.map((p, i) => (
                                <Typography key={i} fontSize="0.9rem" sx={{ mb: 0.5 }}>
                                    • {p}
                                </Typography>
                            ))}
                        </Section>
                    )}

                    {feature.full_content && (
                        <Section title="원문 내용">
                            <Box sx={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>{feature.full_content}</Box>
                        </Section>
                    )}

                    <Typography mt={3} fontSize="0.9rem" color="primary" sx={{ cursor: 'pointer', textAlign: 'center' }} onClick={() => setOpen(false)}>
                        닫기
                    </Typography>
                </Box>
            </Modal>
        </>
    );
};

/* -----------------------------------------------------
 * Modal 내부 섹션 공용 컴포넌트
 * ---------------------------------------------------- */
const Section = ({ title, children }) => (
    <Box sx={{ mb: 3 }}>
        <Typography fontWeight={700} mb={1}>
            {title}
        </Typography>
        {children}
    </Box>
);

export default AnalyzeDashboard;
