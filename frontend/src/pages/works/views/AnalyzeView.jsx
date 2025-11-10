<<<<<<< HEAD
import { Box, Button, Grid, Stack, Typography, CircularProgress } from '@mui/material'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFileStore } from '../../../store/useFileStore'
import { useAnalysisStore } from '../../../store/useAnalysisStore'
import api from '../../../utils/api'
import 문서아이콘 from './icons/문서 아이콘.png'
import 폴더아이콘 from './icons/폴더 아이콘.png'

const AnalyzeView = () => {
  const navigate = useNavigate()
  const { tree, currentProjectId, currentUserId } = useFileStore()
  const setAnalysisResult = useAnalysisStore(state => state.setAnalysisResult)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 파일 트리에서 파일 수집 함수
  const collectFiles = (nodes) => {
    let files = []
    for (const node of nodes) {
      if (node.type === 'file') {
        files.push(node)
      }
      if (node.children?.length) {
        files = files.concat(collectFiles(node.children))
      }
    }
    return files
  }

  // 분석 시작 버튼 핸들러
  const handleAnalysisStart = async () => {
    try {
      setLoading(true)
      setError(null)

      // 1. 공고문 폴더(root-01)와 파일 폴더(root-02)에서 파일 수집
      const 공고문폴더 = tree.find(node => node.id === 'root-01')
      const 파일폴더 = tree.find(node => node.id === 'root-02')

      const 공고문파일들 = 공고문폴더 ? collectFiles([공고문폴더]) : []
      const 첨부파일들 = 파일폴더 ? collectFiles([파일폴더]) : []

      // 2. 공고문 필수 체크
      if (공고문파일들.length === 0) {
        setError('공고문/RFP 파일을 먼저 업로드해주세요.')
        setLoading(false)
        return
      }

      console.log('📁 공고문 파일:', 공고문파일들.length, '개')
      console.log('📁 첨부 파일:', 첨부파일들.length, '개')

      // 3. Backend로 분석 요청
      // 파일 경로를 기반으로 실제 파일을 가져와야 함
      // 여기서는 파일 정보만 전송 (실제 파일은 이미 업로드되어 서버에 저장됨)
      const payload = {
        projectId: currentProjectId,
        userId: currentUserId,
        announcement_files: 공고문파일들.map(f => ({
          id: f.id,
          name: f.name,
          path: f.path,
          folderId: 1 // 공고문 폴더 ID
        })),
        attachment_files: 첨부파일들.map(f => ({
          id: f.id,
          name: f.name,
          path: f.path,
          folderId: 2 // 첨부파일 폴더 ID
        }))
      }

      console.log('🚀 분석 요청 시작:', payload)

      // Backend API 호출
      const response = await api.post('/api/analysis/start', payload)

      console.log('✅ 분석 완료:', response.data)

      // 전역 스토어에 결과 저장 (Dashboard, Create 뷰에서 공유)
      setAnalysisResult(response.data)

      // 4. 분석 완료 후 대시보드로 이동
      // TODO: 분석 결과를 state로 전달하거나 store에 저장
      navigate('/works/analyze/dashboard', { state: { analysisResult: response.data } })

    } catch (err) {
      console.error('❌ 분석 실패:', err)
      setError(err.response?.data?.message || '분석 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Stack sx={{backgroundColor:"#F4F7F9"}} height={"100vh"}justifyContent={'center'}>
      <Stack spacing={3} mb={5} alignItems={'center'}>
        <Typography fontSize={"2rem"} fontFamily={'Isamanru-Bold'}>PALADOC 프로젝트 분석 준비</Typography>
        <Typography fontFamily={'Pretendard4'}>프로젝트 공고문과 관련 첨부파일을 업로드하면 PALADOC AI가 핵심 요구사항, 목차, 예상 일정을 자동으로 도출하여 분석을 시작합니다.</Typography>
      </Stack>
      <Grid display={'flex'} justifyContent={'center'} container spacing={5} mb={10}>
        <Stack sx={{cursor: 'pointer', width:'500px', height:'250px', border: '2px dashed #1890FF', borderRadius: '10px', backgroundColor:'white', alignItems:'center', justifyContent:'center'}}>
          <Box
            component={'img'}
            src={문서아이콘}
            alt='문서'
            sx={{
              width: '42px',
              mb: '12px'
            }}
          />
          <Typography sx={{fontSize:'20px', fontWeight:'bold', mb: '12px'}}>1. 필수: 공고문/RFP 문서 업로드</Typography>
          <Typography sx={{color:'#1890FF', fontWeight:'bold', mb: '8px'}}>(PDF, DOCX, HWP 등)</Typography>
          <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>가장 핵심이 되는 제안 요청서를 먼저 업로드해주세요.</Typography>
        </Stack>
        <Stack sx={{cursor: 'pointer', width:'500px', height:'250px', border: '2px dashed #E8E8E8', borderRadius: '10px', backgroundColor:'white', alignItems:'center', justifyContent:'center'}}>
          <Box
            component={'img'}
            src={폴더아이콘}
            alt='폴더'
            sx={{
              width:'63px',
              mb: '12px'
            }}
          />
          <Typography sx={{fontSize:'20px', fontWeight:'bold', mb: '12px'}}>2. 선택: 첨부파일 모음 업로드</Typography>
          <Typography sx={{color:'#FAAD14', fontWeight:'bold', mb: '8px'}}>(ZIP 파일 또는 개별 파일)</Typography>
          <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>관련 자료(도면, 이미지, 기타 부속 문서)를 함께 분석합니다.</Typography>
        </Stack>
      </Grid>
      <Stack alignItems={'center'} spacing={3}>
        <Box height={'50px'}>
          <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>지원되는 파일 형식: PDF, docx, hwp, txt, Markdown, ZIP/RAR (첨부파일)</Typography>
        </Box>
        <Box>
          <Button
            variant="contained"
            size='large'
            onClick={handleAnalysisStart}
            disabled={loading}
            sx={{
              backgroundColor: loading ? '#d9d9d9' : '#1890FF',
              fontSize:'24px',
              fontWeight:'bold',
              fontFamily:'Pretendard4',
              '&:hover': {
                backgroundColor: '#096dd9'
              },
              '&:disabled': {
                backgroundColor: '#d9d9d9'
              }
            }}
          >
            {loading ? <CircularProgress size={24} sx={{color: 'white', mr: 1}} /> : null}
            {loading ? '분석 중...' : '분석 시작 (RFP 필수)'}
          </Button>
        </Box>
        <Box>
          {error ? (
            <Typography sx={{color:'#ff4d4f'}} fontFamily={'Pretendard4'}>{error}</Typography>
          ) : (
            <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>RFP 파일을 업로드해야 분석을 시작할 수 있습니다.</Typography>
          )}
        </Box>
      </Stack>
=======
// import { Box, Button, Grid, Stack, Typography } from '@mui/material'
// import React from 'react'
// import 문서아이콘 from './icons/문서 아이콘.png'
// import 폴더아이콘 from './icons/폴더 아이콘.png'

// const AnalyzeView = () => {
//   return (
//     <Stack sx={{backgroundColor:"#F4F7F9"}} height={"100vh"}justifyContent={'center'}>
//       <Stack spacing={3} mb={5} alignItems={'center'}>
//         <Typography fontSize={"2rem"} fontFamily={'Isamanru-Bold'}>PALADOC 프로젝트 분석 준비</Typography>
//         <Typography fontFamily={'Pretendard4'}>프로젝트 공고문과 관련 첨부파일을 업로드하면 PALADOC AI가 핵심 요구사항, 목차, 예상 일정을 자동으로 도출하여 분석을 시작합니다.</Typography>
//       </Stack>
//       <Grid display={'flex'} justifyContent={'center'} container spacing={5} mb={10}>
//         <Stack sx={{cursor: 'pointer', width:'500px', height:'250px', border: '2px dashed #1890FF', borderRadius: '10px', backgroundColor:'white', alignItems:'center', justifyContent:'center'}}>
//           <Box
//             component={'img'}
//             src={문서아이콘}
//             alt='문서'
//             sx={{
//               width: '42px',
//               mb: '12px'
//             }}
//           />
//           <Typography sx={{fontSize:'20px', fontWeight:'bold', mb: '12px'}}>1. 필수: 공고문/RFP 문서 업로드</Typography>
//           <Typography sx={{color:'#1890FF', fontWeight:'bold', mb: '8px'}}>(PDF, DOCX, HWP 등)</Typography>
//           <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>가장 핵심이 되는 제안 요청서를 먼저 업로드해주세요.</Typography>
//         </Stack>
//         <Stack sx={{cursor: 'pointer', width:'500px', height:'250px', border: '2px dashed #E8E8E8', borderRadius: '10px', backgroundColor:'white', alignItems:'center', justifyContent:'center'}}>
//           <Box
//             component={'img'}
//             src={폴더아이콘}
//             alt='폴더'
//             sx={{
//               width:'63px',
//               mb: '12px'
//             }}
//           />
//           <Typography sx={{fontSize:'20px', fontWeight:'bold', mb: '12px'}}>2. 선택: 첨부파일 모음 업로드</Typography>
//           <Typography sx={{color:'#FAAD14', fontWeight:'bold', mb: '8px'}}>(ZIP 파일 또는 개별 파일)</Typography>
//           <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>관련 자료(도면, 이미지, 기타 부속 문서)를 함께 분석합니다.</Typography>
//         </Stack>
//       </Grid>
//       <Stack alignItems={'center'} spacing={3}>
//         <Box height={'50px'}>
//           <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>지원되는 파일 형식: PDF, docx, hwp, txt, Markdown, ZIP/RAR (첨부파일)</Typography>
//         </Box>
//         <Box>
//           <Button variant="contained" size='large' sx={{backgroundColor:'#8c8c8c', fontSize:'24px', fontWeight:'bold', fontFamily:'Pretendard4'}}>분석 시작 (RFP 필수)</Button>
//         </Box>
//         <Box>
//           <Typography sx={{color:'#8C8C8C'}} fontFamily={'Pretendard4'}>RFP 파일을 업로드해야 분석을 시작할 수 있습니다.</Typography>
//         </Box>
//       </Stack>

//     </Stack>
//   )
// }

// export default AnalyzeView

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
>>>>>>> dev

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
