import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAnalysisStore } from '../../../store/useAnalysisStore'
import {
  Box,
  Button,
  Divider,
  Paper,
  Stack,
  Typography
} from '@mui/material'

/**
 * 2025-11-09 suyeon: 제안서 초안 생성 페이지
 * - CreateView에서 사용자가 입력한 데이터를 생성 에이전트로 전달할 JSON 형태로 표시
 * - 생성 에이전트 담당자가 필요한 데이터 구조 확인용
 */
const GenerateView = () => {
  const navigate = useNavigate()
  const userInputData = useAnalysisStore(state => state.userInputData)

  useEffect(() => {
    // 사용자 입력 데이터가 없으면 생성 페이지로 리다이렉트
    if (!userInputData) {
      navigate('/works/create')
    }
  }, [userInputData, navigate])

  const handleGoBack = () => {
    navigate('/works/create')
  }

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(userInputData, null, 2))
    alert('JSON 데이터가 클립보드에 복사되었습니다!')
  }

  if (!userInputData) {
    return null
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#F5F7FA',
        p: 4,
        overflow: 'auto'
      }}
    >
      <Stack spacing={3} mx="auto" maxWidth="1200px">
        {/* 헤더 */}
        <Paper
          elevation={2}
          sx={{
            p: 4,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }}
        >
          <Stack spacing={2}>
            <Typography fontSize="2rem" fontFamily="Isamanru-Bold">
              📤 생성 에이전트로 전송될 데이터
            </Typography>
            <Typography fontSize="1rem" color="rgba(255,255,255,0.9)">
              아래 JSON 데이터가 생성 에이전트 API로 전송됩니다.
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                onClick={handleCopyJson}
                sx={{
                  backgroundColor: 'white',
                  color: '#667eea',
                  fontWeight: 600,
                  '&:hover': {
                    backgroundColor: '#f0f0f0'
                  }
                }}
              >
                📋 JSON 복사
              </Button>
              <Button
                variant="outlined"
                onClick={handleGoBack}
                sx={{
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': {
                    borderColor: 'white',
                    backgroundColor: 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                ← 입력 폼으로 돌아가기
              </Button>
            </Stack>
          </Stack>
        </Paper>

        {/* 데이터 요약 */}
        <Paper elevation={1} sx={{ p: 4, borderRadius: 3 }}>
          <Typography fontSize="1.4rem" fontWeight={700} mb={2}>
            데이터 요약
          </Typography>
          <Stack spacing={1.5}>
            <Box>
              <Typography fontSize="0.9rem" color="#8C8C8C">폼 타입</Typography>
              <Typography fontWeight={600}>{userInputData.type}</Typography>
            </Box>
            <Divider />
            <Box>
              <Typography fontSize="0.9rem" color="#8C8C8C">입력 필드 수</Typography>
              <Typography fontWeight={600}>{userInputData.formFields?.length || 0}개</Typography>
            </Box>
            <Divider />
            <Box>
              <Typography fontSize="0.9rem" color="#8C8C8C">작성 시각</Typography>
              <Typography fontWeight={600}>{userInputData.timestamp}</Typography>
            </Box>
          </Stack>
        </Paper>

        {/* JSON 데이터 표시 */}
        <Paper elevation={1} sx={{ p: 4, borderRadius: 3 }}>
          <Typography fontSize="1.4rem" fontWeight={700} mb={2}>
            전체 JSON 데이터
          </Typography>
          <Typography fontSize="0.9rem" color="#8C8C8C" mb={2}>
            생성 에이전트 API 엔드포인트: <code>POST http://localhost:8000/api/generate</code>
          </Typography>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              backgroundColor: '#1e1e1e',
              borderRadius: 2,
              overflow: 'auto',
              maxHeight: '600px'
            }}
          >
            <pre
              style={{
                margin: 0,
                color: '#d4d4d4',
                fontSize: '0.85rem',
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}
            >
              {JSON.stringify(userInputData, null, 2)}
            </pre>
          </Paper>
        </Paper>

        {/* 안내 메시지 */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            borderRadius: 3,
            backgroundColor: '#E6F4FF',
            border: '1px solid #91CAFF'
          }}
        >
          <Typography fontSize="0.9rem" color="#0958d9" fontWeight={500}>
            💡 <strong>생성 에이전트 담당자에게:</strong>
            <br />
            위 JSON 데이터를 받아 제안서 초안을 생성하는 API를 개발해주세요.
            <br />
            완료 후 이 페이지에서 실제 API 호출 및 편집 페이지로 자동 이동 기능을 추가할 예정입니다.
          </Typography>
        </Paper>
      </Stack>
    </Box>
  )
}

export default GenerateView
