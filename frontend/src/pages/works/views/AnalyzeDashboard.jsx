/**
 * 2025-11-09 수연 추가: 분석 대시보드 페이지
 * 목적: FastAPI 분석 결과를 시각화하여 표시
 * 데이터: AnalyzeView에서 navigate로 전달받은 analysisResult 사용
 */

import { Box, Paper, Stack, Typography, CircularProgress } from '@mui/material'
import { useLocation } from 'react-router-dom'

const AnalyzeDashboard = () => {
  const location = useLocation()
  const analysisResult = location.state?.analysisResult

  // 로딩 중이거나 데이터가 없을 때
  if (!analysisResult) {
    return (
      <Stack
        sx={{backgroundColor:"#F4F7F9", height:"100vh"}}
        justifyContent={'center'}
        alignItems={'center'}
      >
        <CircularProgress size={60} />
        <Typography sx={{mt: 3, fontSize: '1.2rem'}}>
          분석 결과를 불러오는 중입니다...
        </Typography>
      </Stack>
    )
  }

  return (
    <Stack sx={{backgroundColor:"#F4F7F9", height:"100vh", overflow: 'auto', p: 4}}>
      {/* 헤더 */}
      <Box mb={4}>
        <Typography fontSize={"2rem"} fontFamily={'Isamanru-Bold'} mb={2}>
          📊 프로젝트 분석 결과
        </Typography>
        <Typography fontFamily={'Pretendard4'} color={'#8C8C8C'}>
          PALADOC AI가 분석한 프로젝트 요구사항 및 첨부 양식입니다.
        </Typography>
      </Box>

      {/* 분석 결과 카드 */}
      <Stack spacing={3}>
        {/* 상태 정보 */}
        <Paper elevation={2} sx={{p: 3, borderRadius: 2}}>
          <Typography fontSize={'1.3rem'} fontWeight={'bold'} mb={2}>
            ✅ 분석 상태
          </Typography>
          <Typography>
            상태: <strong>{analysisResult.data?.status || 'completed'}</strong>
          </Typography>
          <Typography>
            메시지: {analysisResult.message}
          </Typography>
        </Paper>

        {/* 사용자 입력 폼 (form_source, user_form) */}
        {analysisResult.data?.user_form && (
          <Paper elevation={2} sx={{p: 3, borderRadius: 2}}>
            <Typography fontSize={'1.3rem'} fontWeight={'bold'} mb={2}>
              📝 사용자 입력 폼
            </Typography>
            <Typography mb={1}>
              출처: <strong>{analysisResult.data.form_source === 'TEMPLATE' ? '첨부 양식' : '공고 목차'}</strong>
            </Typography>
            <Box
              component={'pre'}
              sx={{
                backgroundColor: '#f5f5f5',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.9rem'
              }}
            >
              {JSON.stringify(analysisResult.data.user_form, null, 2)}
            </Box>
          </Paper>
        )}

        {/* 분석된 문서 목록 */}
        {analysisResult.data?.documents && analysisResult.data.documents.length > 0 && (
          <Paper elevation={2} sx={{p: 3, borderRadius: 2}}>
            <Typography fontSize={'1.3rem'} fontWeight={'bold'} mb={2}>
              📄 분석된 문서
            </Typography>
            <Stack spacing={1}>
              {analysisResult.data.documents.map((doc, index) => (
                <Box key={index} sx={{p: 2, backgroundColor: '#f9f9f9', borderRadius: 1}}>
                  <Typography fontWeight={'bold'}>{doc.filename || doc.name}</Typography>
                  <Typography fontSize={'0.9rem'} color={'#666'}>
                    유형: {doc.folder === 1 ? '공고문' : '첨부파일'} |
                    페이지: {doc.pages || 'N/A'}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        )}

        {/* 첨부 양식 템플릿 */}
        {analysisResult.data?.attachment_templates && analysisResult.data.attachment_templates.length > 0 && (
          <Paper elevation={2} sx={{p: 3, borderRadius: 2}}>
            <Typography fontSize={'1.3rem'} fontWeight={'bold'} mb={2}>
              📋 첨부 양식 템플릿
            </Typography>
            <Stack spacing={2}>
              {analysisResult.data.attachment_templates.map((template, index) => (
                <Box key={index} sx={{p: 2, backgroundColor: '#f9f9f9', borderRadius: 1}}>
                  <Typography fontWeight={'bold'}>{template.filename}</Typography>
                  <Typography fontSize={'0.9rem'} color={'#666'}>
                    형식: {template.format} | 필드 수: {template.fields?.length || 0}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        )}

        {/* 원본 데이터 (디버깅용) */}
        <Paper elevation={2} sx={{p: 3, borderRadius: 2}}>
          <Typography fontSize={'1.3rem'} fontWeight={'bold'} mb={2}>
            🔍 원본 분석 데이터 (디버깅)
          </Typography>
          <Box
            component={'pre'}
            sx={{
              backgroundColor: '#f5f5f5',
              p: 2,
              borderRadius: 1,
              overflow: 'auto',
              fontSize: '0.85rem',
              maxHeight: '400px'
            }}
          >
            {JSON.stringify(analysisResult, null, 2)}
          </Box>
        </Paper>
      </Stack>
    </Stack>
  )
}

export default AnalyzeDashboard
