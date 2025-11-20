// 📄 AnalyzeView.jsx
import { Box, Button, Grid, Stack, Typography, CircularProgress, Paper, Chip, Modal } from '@mui/material';
import { useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFileStore } from '../../../store/useFileStore';
import { useAnalysisStore } from '../../../store/useAnalysisStore';
import api from '../../../utils/api';
import 문서아이콘 from './icons/문서 아이콘.png';
import 폴더아이콘 from './icons/폴더 아이콘.png';
import Upload from '../../../components/Upload';
import { useProjectStore } from '../../../store/useProjectStore';
import { useAuthStore } from '../../../store/useAuthStore';

const AnalyzeView = () => {
    const navigate = useNavigate();
    const { tree } = useFileStore();
    const analysisResult = useAnalysisStore((state)=> state.analysisResult);
    const setAnalysisResult = useAnalysisStore((state) => state.setAnalysisResult);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    //const [analyzeResult, setAnalyzeResult] = useState(true);

    const user = useAuthStore((s) => s.user);
    const project = useProjectStore((s) => s.project);

    console.log('projectIdx: ', project.projectIdx);
    console.log('user: ', user.userId);

    // ✅ 업로드 컴포넌트 각각 제어할 Ref
    const rfpUploadRef = useRef(null);
    const attachUploadRef = useRef(null);

    // ✅ 클릭 시 input 클릭 트리거
    const triggerUpload = (ref) => {
        ref.current?.click();
    };

    const collectFiles = (nodes) => {
        let files = [];
        for (const node of nodes) {
            if (node.type === 'file') files.push(node);
            if (node.children?.length) files = files.concat(collectFiles(node.children));
        }
        return files;
    };

    const featureCards = useMemo(() => {
        if (!analysisResult || !analysisResult.data || !analysisResult.data.features) return [];
        return analysisResult.data.features.map((feature, index) => {
            const resultId = feature.result_id ?? index + 1;
            const cardId = `${feature.feature_code || feature.feature_name || 'feature'}_${resultId}`;
            return { ...feature, result_id: resultId, card_id: cardId };
        });
    }, [analysisResult]);

    const handleAnalysisStart = async () => {
        try {
            setLoading(true);
            setError(null);

            const 공고문폴더 = tree.find((node) => node.id === 'root-01');
            const 파일폴더 = tree.find((node) => node.id === 'root-02');

            const 공고문파일들 = 공고문폴더 ? collectFiles([공고문폴더]) : [];
            const 첨부파일들 = 파일폴더 ? collectFiles([파일폴더]) : [];

            if (공고문파일들.length === 0) {
                setError('공고문/RFP 파일을 먼저 업로드해주세요.');
                setLoading(false);
                return;
            }

            console.log('📁 공고문 파일:', 공고문파일들.length, '개');
            console.log('📁 첨부 파일:', 첨부파일들.length, '개');

            const payload = {
                projectId: project.projectIdx,
                userId: user.userId,
                announcement_files: 공고문파일들.map((f) => ({
                    id: f.id,
                    name: f.name,
                    path: f.path,
                    folderId: 1,
                })),
                attachment_files: 첨부파일들.map((f) => ({
                    id: f.id,
                    name: f.name,
                    path: f.path,
                    folderId: 2,
                })),
            };

            console.log('🚀 분석 요청 시작:', payload);

            const response = await api.post('/api/analysis/start', payload);

            console.log('✅ 분석 완료:', response.data);

            setAnalysisResult(response.data);

            //setAnalyzeResult(false);

            // navigate('/works/analyze/dashboard', { state: { analysisResult: response.data } });
        } catch (err) {
            console.error('❌ 분석 실패:', err);

            // 타임아웃 에러 처리
            if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
                setError('분석 시간이 초과되었습니다. 파일 크기가 크거나 분석이 오래 걸리는 경우 10분 이상 소요될 수 있습니다. 다시 시도해주세요.');
            } else if (err.response?.data?.message) {
                setError(err.response.data.message);
            } else if (err.message) {
                setError(`분석 중 오류가 발생했습니다: ${err.message}`);
            } else {
                setError('분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
            }
        } finally {
            setLoading(false);
        }
    };

    return analysisResult==null ? (
        <Stack sx={{ backgroundColor: '#F4F7F9' }} height={'100vh'} justifyContent={'center'}>
            <Stack spacing={3} mb={5} alignItems={'center'}>
                <Typography fontSize={'2rem'} fontFamily={'Isamanru-Bold'}>
                    PALADOC 프로젝트 분석 준비
                </Typography>
                <Typography fontFamily={'Pretendard4'}>프로젝트 공고문과 관련 첨부파일을 업로드하면 PALADOC AI가 핵심 요구사항, 목차, 예상 일정을 자동으로 도출하여 분석을 시작합니다.</Typography>
            </Stack>

            <Grid display={'flex'} justifyContent={'center'} container spacing={5} mb={10}>
                {/* ✅ 1. 필수 RFP 업로드 */}
                <Stack
                    sx={{
                        cursor: 'pointer',
                        width: '500px',
                        height: '250px',
                        border: '2px dashed #1890FF',
                        borderRadius: '10px',
                        backgroundColor: 'white',
                        alignItems: 'center',
                        justifyContent: 'center',
                        '&:hover': { bgcolor: '#f3f4f6' },
                    }}
                    onClick={() => triggerUpload(rfpUploadRef)}
                >
                    <Box component={'img'} src={문서아이콘} alt="문서" sx={{ width: '42px', mb: '12px' }} />
                    <Typography sx={{ fontSize: '20px', fontWeight: 'bold', mb: '12px' }}>1. 필수: 공고문/RFP 문서 업로드</Typography>
                    <Typography sx={{ color: '#1890FF', fontWeight: 'bold', mb: '8px' }}>(PDF, DOCX, HWP 등)</Typography>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily={'Pretendard4'}>
                        가장 핵심이 되는 제안 요청서를 먼저 업로드해주세요.
                    </Typography>
                </Stack>

                {/* ✅ 2. 선택 첨부파일 업로드 */}
                <Stack
                    sx={{
                        cursor: 'pointer',
                        width: '500px',
                        height: '250px',
                        border: '2px dashed #E8E8E8',
                        borderRadius: '10px',
                        backgroundColor: 'white',
                        alignItems: 'center',
                        justifyContent: 'center',
                        '&:hover': { bgcolor: '#f3f4f6' },
                    }}
                    onClick={() => triggerUpload(attachUploadRef)}
                >
                    <Box component={'img'} src={폴더아이콘} alt="폴더" sx={{ width: '63px', mb: '12px' }} />
                    <Typography sx={{ fontSize: '20px', fontWeight: 'bold', mb: '12px' }}>2. 선택: 첨부파일 모음 업로드</Typography>
                    <Typography sx={{ color: '#FAAD14', fontWeight: 'bold', mb: '8px' }}>(ZIP 파일 또는 개별 파일)</Typography>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily={'Pretendard4'}>
                        관련 자료(도면, 이미지, 기타 부속 문서)를 함께 분석합니다.
                    </Typography>
                </Stack>
            </Grid>

            {/* ✅ 숨겨진 Upload 컴포넌트 */}
            <Upload ref={rfpUploadRef} rootId={'root-01'} asButton={false} />
            <Upload ref={attachUploadRef} rootId={'root-02'} asButton={false} />

            <Stack alignItems={'center'} spacing={3}>
                <Box height={'50px'}>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily={'Pretendard4'}>
                        지원되는 파일 형식: PDF, docx, hwp, txt, Markdown, ZIP/RAR (첨부파일)
                    </Typography>
                </Box>
                <Box>
                    <Button
                        variant="contained"
                        size="large"
                        onClick={handleAnalysisStart}
                        disabled={loading}
                        sx={{
                            backgroundColor: loading ? '#d9d9d9' : '#1890FF',
                            fontSize: '24px',
                            fontWeight: 'bold',
                            fontFamily: 'Pretendard4',
                            '&:hover': { backgroundColor: '#096dd9' },
                            '&:disabled': { backgroundColor: '#d9d9d9' },
                        }}
                    >
                        {loading ? <CircularProgress size={24} sx={{ color: 'white', mr: 1 }} /> : null}
                        {loading ? '분석 중...' : '분석 시작 (RFP 필수)'}
                    </Button>
                </Box>
                <Box>
                    {error ? (
                        <Typography sx={{ color: '#ff4d4f' }} fontFamily={'Pretendard4'}>
                            {error}
                        </Typography>
                    ) : (
                        <Typography sx={{ color: '#8C8C8C' }} fontFamily={'Pretendard4'}>
                            RFP 파일을 업로드해야 분석을 시작할 수 있습니다.
                        </Typography>
                    )}
                </Box>
            </Stack>
        </Stack>
    ) : (
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

export default AnalyzeView;
