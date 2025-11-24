import { Box, Button, Grid, Stack, Typography, CircularProgress, Paper, Chip, Modal } from '@mui/material';
import { useState, useRef, useMemo, useEffect } from 'react';
import { useFileStore } from '../../../store/useFileStore';
import { useAnalysisStore } from '../../../store/useAnalysisStore';
import api from '../../../utils/api';
import 문서아이콘 from './icons/문서 아이콘.png';
import 폴더아이콘 from './icons/폴더 아이콘.png';
import Upload from '../../../components/Upload';
import { useProjectStore } from '../../../store/useProjectStore';
import { useAuthStore } from '../../../store/useAuthStore';

/**
 * 프로젝트 분석 페이지 (분석 전/후 통합 컴포넌트)
 * - analysisResult가 null이면: 파일 업로드 및 분석 시작 화면
 * - analysisResult가 있으면: 분석 결과 카드 표시 화면
 */
const AnalyzeView = () => {
    // 전역 상태 관리
    const { tree } = useFileStore(); // 업로드된 파일 트리 구조
    const setAnalysisResult = useAnalysisStore((state) => state.setAnalysisResult); // 분석 결과 저장 함수
    const clearAnalysisResult = useAnalysisStore((state) => state.clearAnalysisResult); // 분석 결과 초기화 함수
    const analysisResult = useAnalysisStore((state) => state.analysisResult); // 분석 결과 데이터
    const analysisData = analysisResult?.data || {}; // 분석 결과 내부 data 객체

    // 로컬 상태 관리
    const [loading, setLoading] = useState(false); // 분석 진행 중 상태
    const [error, setError] = useState(null); // 에러 메시지 상태
    const [loadingAnalysis, setLoadingAnalysis] = useState(false); // 분석 결과 로딩 상태

    // 사용자 및 프로젝트 정보
    const user = useAuthStore((s) => s.user);
    const project = useProjectStore((s) => s.project);

    console.log('projectIdx: ', project.projectIdx);
    console.log('user: ', user.userId);

    /**
     * 2025-11-23 추가: 프로젝트 변경 시 해당 프로젝트의 분석 결과를 DB에서 자동 로드
     * 
     * 문제점: 이전에는 sessionStorage에 저장된 분석 결과가 프로젝트 변경 시에도 그대로 표시됨
     * 해결: 프로젝트가 변경될 때마다 해당 프로젝트의 분석 결과를 DB에서 조회하여 표시
     * 
     * 동작 흐름:
     * 1. projectIdx가 변경되면 useEffect 트리거
     * 2. /api/analysis/get-context API 호출하여 해당 프로젝트의 분석 결과 조회
     * 3. 분석 결과가 있으면 store에 저장하여 화면에 표시
     * 4. 분석 결과가 없으면 store 초기화하여 파일 업로드 화면 표시
     */
    useEffect(() => {
        const loadAnalysisResult = async () => {
            // 프로젝트 ID가 없으면 분석 결과 초기화
            if (!project.projectIdx) {
                clearAnalysisResult();
                return;
            }

            try {
                setLoadingAnalysis(true);
                console.log('📖 프로젝트별 분석 결과 로드 시작: projectIdx=', project.projectIdx);
                
                // 백엔드 API 호출: 해당 프로젝트의 분석 결과 조회
                const response = await api.get('/api/analysis/get-context', {
                    params: { projectIdx: project.projectIdx }
                });

                if (response.data.status === 'success' && response.data.data) {
                    const contextData = response.data.data;
                    const features = contextData.extracted_features || []; // 분석된 Feature 배열
                    const resultToc = contextData.result_toc; // 목차 데이터

                    // 분석 결과가 있으면 store에 저장 (화면에 표시됨)
                    if (features.length > 0 || resultToc) {
                        const analysisResultData = {
                            status: 'success',
                            data: {
                                features: features,
                                table_of_contents: resultToc,
                                features_summary: {
                                    total_count: features.length
                                }
                            }
                        };
                        setAnalysisResult(analysisResultData);
                        console.log('✅ 분석 결과 로드 완료:', features.length, '개 Feature');
                    } else {
                        // 분석 결과가 없으면 초기화 (파일 업로드 화면 표시)
                        clearAnalysisResult();
                        console.log('⚠️ 분석 결과 없음 (새 프로젝트 또는 분석 미실행)');
                    }
                } else {
                    // API 응답이 실패한 경우 초기화
                    clearAnalysisResult();
                    console.log('⚠️ 분석 결과 조회 실패:', response.data.message);
                }
            } catch (err) {
                // API 호출 실패 시 초기화
                console.error('❌ 분석 결과 로드 실패:', err);
                clearAnalysisResult();
            } finally {
                setLoadingAnalysis(false);
            }
        };

        loadAnalysisResult();
    }, [project.projectIdx, setAnalysisResult, clearAnalysisResult]);

    // 분석 결과의 features 배열을 카드 데이터로 변환
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

    // 업로드 컴포넌트를 제어하기 위한 Ref
    const rfpUploadRef = useRef(null); // 공고문/RFP 업로드 컴포넌트
    const attachUploadRef = useRef(null); // 첨부파일 업로드 컴포넌트

    /**
     * 업로드 영역 클릭 시 숨겨진 input 클릭 트리거
     * @param {React.RefObject} ref - Upload 컴포넌트의 ref
     */
    const triggerUpload = (ref) => {
        ref.current?.click();
    };

    /**
     * 파일 트리에서 모든 파일 노드를 재귀적으로 수집
     * @param {Array} nodes - 파일 트리 노드 배열
     * @returns {Array} 파일 노드만 포함된 배열
     */
    const collectFiles = (nodes) => {
        let files = [];
        for (const node of nodes) {
            if (node.type === 'file') files.push(node);
            if (node.children?.length) files = files.concat(collectFiles(node.children));
        }
        return files;
    };

    /**
     * 분석 시작 버튼 클릭 핸들러
     * - 업로드된 파일들을 수집하여 백엔드에 분석 요청
     * - 분석 완료 후 결과를 store에 저장하면 화면이 자동으로 전환됨
     */
    const handleAnalysisStart = async () => {
        try {
            setLoading(true);
            setError(null);

            // 파일 트리에서 각 폴더 찾기 (root-01: 공고문, root-02: 첨부파일)
            const 공고문폴더 = tree.find((node) => node.id === 'root-01');
            const 파일폴더 = tree.find((node) => node.id === 'root-02');

            // 각 폴더에서 실제 파일들만 수집
            const 공고문파일들 = 공고문폴더 ? collectFiles([공고문폴더]) : [];
            const 첨부파일들 = 파일폴더 ? collectFiles([파일폴더]) : [];

            // 필수 파일 검증 (공고문이 없으면 분석 불가)
            if (공고문파일들.length === 0) {
                setError('공고문/RFP 파일을 먼저 업로드해주세요.');
                setLoading(false);
                return;
            }

            console.log('📁 공고문 파일:', 공고문파일들.length, '개');
            console.log('📁 첨부 파일:', 첨부파일들.length, '개');

            // 백엔드로 전송할 payload 구성
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

            // 백엔드 API 호출 (분석 요청)
            const response = await api.post('/api/analysis/start', payload);

            console.log('✅ 분석 완료:', response.data);

            // 분석 결과를 store에 저장 (이 시점에서 화면이 결과 화면으로 전환됨)
            setAnalysisResult(response.data);

            // [참고] 이전 방식: 별도 페이지로 navigate 했었으나 현재는 사용 안 함
            //navigate('/works/analyze/dashboard', { state: { analysisResult: response.data } });
        } catch (err) {
            console.error('❌ 분석 실패:', err);

            // 에러 타입별 처리
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

    // === 조건부 렌더링: 분석 전/후 화면 전환 ===
    return analysisResult == null ? (
        /* ========================================
         * [분석 전 화면] 파일 업로드 및 분석 시작
         * ======================================== */
        <Stack sx={{ backgroundColor: '#F4F7F9' }} height={'100vh'} justifyContent={'center'}>
            {/* 상단 타이틀 */}
            <Stack spacing={3} mb={5} alignItems={'center'}>
                <Typography fontSize={'2rem'} fontFamily={'Isamanru-Bold'}>
                    PALADOC 프로젝트 분석 준비
                </Typography>
                <Typography fontFamily={'Pretendard4'}>프로젝트 공고문과 관련 첨부파일을 업로드하면 PALADOC AI가 핵심 요구사항, 목차, 예상 일정을 자동으로 도출하여 분석을 시작합니다.</Typography>
            </Stack>

            {/* 파일 업로드 영역 (2개) */}
            <Grid display={'flex'} justifyContent={'center'} container spacing={5} mb={10}>
                {/* 1. 필수 RFP 업로드 */}
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

                {/* 2. 선택 첨부파일 업로드 */}
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

            {/* 실제 업로드 기능을 수행하는 숨겨진 컴포넌트 (화면에는 보이지 않음) */}
            <Upload ref={rfpUploadRef} rootId={'root-01'} asButton={false} />
            <Upload ref={attachUploadRef} rootId={'root-02'} asButton={false} />

            {/* 하단 안내 및 버튼 영역 */}
            <Stack alignItems={'center'} spacing={3}>
                <Box height={'50px'}>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily={'Pretendard4'}>
                        지원되는 파일 형식: PDF, docx, hwp, txt, Markdown, ZIP/RAR (첨부파일)
                    </Typography>
                </Box>
                <Box>
                    {/* 분석 시작 버튼 */}
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
                    {/* 에러 메시지 또는 안내 메시지 */}
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
    ) : 
    (
            <Stack sx={{ backgroundColor: '#F4F7F9', height: '100vh', overflow: 'auto', p: 4 }} spacing={3}>
                {/* 헤더 */}
                <Box>
                    <Typography fontSize={'2rem'} fontFamily={'Isamanru-Bold'} mb={1}>
                        📊 프로젝트 분석 결과
                    </Typography>
                    <Typography fontFamily={'Pretendard4'} color={'#8C8C8C'}>
                        PALADOC AI가 분석한 프로젝트 요구사항 및 첨부 양식입니다.
                    </Typography>
                </Box>

                {/* 핵심 정보 박스 */}
                <Paper 
                    elevation={2} 
                    sx={{ 
                        p: 4, 
                        borderRadius: 3, 
                        backgroundColor: 'white',
                        border: '1px solid #e0e0e0'
                    }}
                >
                    <Typography fontSize="1.6rem" fontWeight={700} mb={3} fontFamily={'Isamanru-Bold'}>
                        🔑 핵심 정보
                    </Typography>
                    <Grid container spacing={3}>
                        {featureCards
                            .filter(feature => {
                                // 핵심 정보로 분류할 feature_code들
                                const coreFeatures = [
                                    'project_name', 'announcement_date', 'application_period',
                                    'project_period', 'support_scale', 'deadline'
                                ];
                                return coreFeatures.includes(feature.feature_code);
                            })
                            .slice(0, 6) // 최대 6개만 표시
                            .map((feature) => (
                                <Grid item xs={12} sm={6} md={4} key={feature.card_id}>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography fontSize="1.4rem" color="#262626" mb={1} fontWeight={700}>
                                            {feature.feature_name || feature.feature_code}
                                        </Typography>
                                        <Typography fontSize="1.1rem" fontWeight={400} color="#595959">
                                            {feature.summary || feature.full_content?.substring(0, 50) || '정보 없음'}
                                        </Typography>
                                    </Box>
                                </Grid>
                            ))}
                        {featureCards.filter(f => {
                            const coreFeatures = ['project_name', 'announcement_date', 'application_period', 'project_period', 'support_scale', 'deadline'];
                            return coreFeatures.includes(f.feature_code);
                        }).length === 0 && (
                            <Grid item xs={12}>
                                <Typography color="#8C8C8C" textAlign="center">
                                    핵심 정보가 없습니다.
                                </Typography>
                            </Grid>
                        )}
                    </Grid>
                </Paper>

                {/* Feature 카드 박스 */}
                <Paper 
                    elevation={2} 
                    sx={{ 
                        p: 4, 
                        borderRadius: 3, 
                        backgroundColor: 'white',
                        border: '1px solid #e0e0e0'
                    }}
                >
                    <Typography fontSize="1.3rem" fontWeight={700} mb={3} fontFamily={'Isamanru-Bold'}>
                        📋 상세 요구사항
                    </Typography>
                    {featureCards.length ? (
                        <Grid container spacing={2}>
                            {featureCards.map((feature) => (
                                <Grid item size={4} key={feature.card_id}>
                                    <FeatureCard feature={feature} />
                                </Grid>
                            ))}
                        </Grid>
                    ) : (
                        <Box sx={{ p: 6, textAlign: 'center' }}>
                            <Typography fontSize="1.1rem" fontWeight={600} color="#8C8C8C">
                                표시할 Feature 정보가 없습니다
                            </Typography>
                        </Box>
                    )}
                </Paper>
    
                {/* 디버깅 JSON */}
                {/* <Paper elevation={0} sx={{ p: 4, borderRadius: 3, mt: 4 }}>
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
                </Paper> */}
            </Stack>
    );
};

/**
 * Feature 카드 컴포넌트
 * - 분석된 각 feature를 카드 형태로 표시
 * - 클릭 시 상세 정보를 모달로 표시
 */
const FeatureCard = ({ feature }) => {
    const [open, setOpen] = useState(false); // 모달 열림/닫힘 상태

    return (
        <>
            {/* Feature 카드 */}
            <Paper
                elevation={1}
                sx={{
                    p: 3,
                    borderRadius: 3,
                    minHeight: 220,
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
                    {/* Feature 이름 */}
                    <Typography fontSize="1.1rem" fontWeight={700}>
                        {feature.feature_name || feature.feature_code || 'Feature'}
                    </Typography>

                    {/* 요약 내용 */}
                    {feature.summary ? (
                        <Typography 
                            fontSize="0.9rem" 
                            color="#595959"
                            sx={{
                                display: '-webkit-box',
                                WebkitLineClamp: 3,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                lineHeight: 1.5,
                            }}
                        >
                            {feature.summary}
                        </Typography>
                    ) : (
                        <Typography fontSize="0.85rem" color="#8C8C8C" sx={{ fontStyle: 'italic' }}>
                            요약 정보가 없습니다.
                        </Typography>
                    )}

                    {/* 안내 텍스트 */}
                    <Typography fontSize="0.85rem" color="#8C8C8C" sx={{ mt: 'auto' }}>
                        상세 내용을 확인하려면 클릭하세요.
                    </Typography>
                </Stack>
            </Paper>

            {/* 상세 정보 모달 */}
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
                    {/* 모달 타이틀 */}
                    <Typography fontSize="1.4rem" fontWeight={700} mb={2}>
                        {feature.feature_name || feature.feature_code}
                    </Typography>

                    {/* 요약 섹션 (있을 경우만 표시) */}
                    {feature.summary && <Section title="요약">{feature.summary}</Section>}

                    {/* 핵심 포인트 섹션 (배열이 있고 비어있지 않을 경우만 표시) */}
                    {Array.isArray(feature.key_points) && feature.key_points.length > 0 && (
                        <Section title="핵심 포인트">
                            {feature.key_points.map((p, i) => (
                                <Typography key={i} fontSize="0.9rem" sx={{ mb: 0.5 }}>
                                    • {p}
                                </Typography>
                            ))}
                        </Section>
                    )}

                    {/* 원문 내용 섹션 (있을 경우만 표시) */}
                    {feature.full_content && (
                        <Section title="원문 내용">
                            <Box sx={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem' }}>{feature.full_content}</Box>
                        </Section>
                    )}

                    {/* 닫기 버튼 */}
                    <Typography mt={3} fontSize="0.9rem" color="primary" sx={{ cursor: 'pointer', textAlign: 'center' }} onClick={() => setOpen(false)}>
                        닫기
                    </Typography>
                </Box>
            </Modal>
        </>
    );
};

/**
 * 모달 내부 섹션 공용 컴포넌트
 * - title: 섹션 제목
 * - children: 섹션 내용
 */
const Section = ({ title, children }) => (
    <Box sx={{ mb: 3 }}>
        <Typography fontWeight={700} mb={1}>
            {title}
        </Typography>
        {children}
    </Box>
);


export default AnalyzeView;