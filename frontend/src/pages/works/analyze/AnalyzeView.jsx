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
    const setAnalysisResult = useAnalysisStore((state) => state.setAnalysisResult);
    // const [analysisResult, setAnalysisResult] = useState(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    // const [analyzeResult, setAnalyzeResult] = useState(true);

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

            // setAnalyzeResult(false);

            navigate('/works/analyze/dashboard', { state: { analysisResult: response.data } });
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

    return (
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
    );
};

export default AnalyzeView;
