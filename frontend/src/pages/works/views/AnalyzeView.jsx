// 📄 AnalyzeView.jsx
import { Box, Button, Grid, Stack, Typography } from '@mui/material';
import React, { useRef } from 'react';
import 문서아이콘 from './icons/문서 아이콘.png';
import 폴더아이콘 from './icons/폴더 아이콘.png';
import Upload from '../../../components/Upload';
import { useNavigate } from 'react-router';

const AnalyzeView = () => {
    const nav = useNavigate();
    const analyzeStart = () => {
        nav('/works/analyze/_new');
    };
    // ✅ 업로드 컴포넌트 각각 제어할 Ref
    const rfpUploadRef = useRef(null);
    const attachUploadRef = useRef(null);

    // ✅ 클릭 시 input 클릭 트리거
    const triggerUpload = (ref) => {
        ref.current?.click();
    };

    return (
        <Stack sx={{ backgroundColor: '#F4F7F9' }} height="100vh" justifyContent="center">
            <Stack spacing={3} mb={5} alignItems="center">
                <Typography fontSize="2rem" fontFamily="Isamanru-Bold">
                    PALADOC 프로젝트 분석 준비
                </Typography>
                <Typography fontFamily="Pretendard4">프로젝트 공고문과 관련 첨부파일을 업로드하면 PALADOC AI가 핵심 요구사항, 목차, 예상 일정을 자동으로 도출하여 분석을 시작합니다.</Typography>
            </Stack>

            <Grid display="flex" justifyContent="center" container spacing={5} mb={10}>
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
                    onClick={() => triggerUpload(rfpUploadRef)} // ✅ 클릭 시 ref 실행
                >
                    <Box component="img" src={문서아이콘} alt="문서" sx={{ width: '42px', mb: '12px' }} />
                    <Typography sx={{ fontSize: '20px', fontWeight: 'bold', mb: '12px' }}>1. 필수: 공고문/RFP 문서 업로드</Typography>
                    <Typography sx={{ color: '#1890FF', fontWeight: 'bold', mb: '8px' }}>(PDF, DOCX, HWP 등)</Typography>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily="Pretendard4">
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
                    onClick={() => triggerUpload(attachUploadRef)} // ✅ 클릭 시 ref 실행
                >
                    <Box component="img" src={폴더아이콘} alt="폴더" sx={{ width: '63px', mb: '12px' }} />
                    <Typography sx={{ fontSize: '20px', fontWeight: 'bold', mb: '12px' }}>2. 선택: 첨부파일 모음 업로드</Typography>
                    <Typography sx={{ color: '#FAAD14', fontWeight: 'bold', mb: '8px' }}>(ZIP 파일 또는 개별 파일)</Typography>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily="Pretendard4">
                        관련 자료(도면, 이미지, 기타 부속 문서)를 함께 분석합니다.
                    </Typography>
                </Stack>
            </Grid>

            {/* ✅ 숨겨진 Upload 컴포넌트 2개 */}
            <Upload ref={rfpUploadRef} rootId={'root-01'} asButton={false} />
            <Upload ref={attachUploadRef} rootId={'root-02'} asButton={false} />

            <Stack alignItems="center" spacing={3}>
                <Box height="50px">
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily="Pretendard4">
                        지원되는 파일 형식: PDF, docx, hwp, txt, Markdown, ZIP/RAR (첨부파일)
                    </Typography>
                </Box>
                <Box>
                    <Button
                        variant="contained"
                        size="large"
                        sx={{
                            backgroundColor: '#8c8c8c',
                            fontSize: '24px',
                            fontWeight: 'bold',
                            fontFamily: 'Pretendard4',
                            '&:hover': { bgcolor: '#1660cfff' },
                        }}
                        onClick={analyzeStart}
                    >
                        분석 시작 (RFP 필수)
                    </Button>
                </Box>
                <Box>
                    <Typography sx={{ color: '#8C8C8C' }} fontFamily="Pretendard4">
                        RFP 파일을 업로드해야 분석을 시작할 수 있습니다.
                    </Typography>
                </Box>
            </Stack>
        </Stack>
    );
};

export default AnalyzeView;
