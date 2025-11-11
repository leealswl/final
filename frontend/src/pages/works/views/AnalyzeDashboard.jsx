/**
 * 2025-11-09 수연 추가: 분석 대시보드 페이지
 * 목적: FastAPI 분석 결과를 시각화하여 표시
 * 데이터: AnalyzeView에서 navigate로 전달받은 analysisResult 사용
 */

import {
  Box,
  Paper,
  Stack,
  Typography,
  CircularProgress,
  Button,
  Chip,
  Grid,
  Collapse
} from '@mui/material'
import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAnalysisStore } from '../../../store/useAnalysisStore'

const AnalyzeDashboard = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const storedResult = useAnalysisStore(state => state.analysisResult)
  const analysisResult = location.state?.analysisResult || storedResult
  const analysisData = analysisResult?.data || {}
  const featureCards = useMemo(() => {
    return (analysisData.features || []).map((feature, index) => {
      const resultId = feature.result_id ?? index + 1
      const cardId = `${feature.feature_code || feature.feature_name || 'feature'}_${resultId}`
      return {
        ...feature,
        result_id: resultId,
        card_id: cardId
      }
    })
  }, [analysisData.features])

  const [expandedCardId, setExpandedCardId] = useState(null)

  const handleToggleCard = cardId => {
    setExpandedCardId(prev => (prev === cardId ? null : cardId))
  }

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
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} mb={4} spacing={2}>
        <Box>
          <Typography fontSize={"2rem"} fontFamily={'Isamanru-Bold'} mb={1}>
            📊 프로젝트 분석 결과
          </Typography>
          <Typography fontFamily={'Pretendard4'} color={'#8C8C8C'}>
            PALADOC AI가 분석한 프로젝트 요구사항 및 첨부 양식입니다.
          </Typography>
        </Box>
        <Button
          variant="contained"
          size="large"
          sx={{ backgroundColor: '#262626', '&:hover': { backgroundColor: '#000000' } }}
          onClick={() => navigate('/works/create')}
        >
          생성 페이지로 이동
        </Button>
      </Stack>

      {/* Feature 카드 리스트 */}
      {featureCards.length ? (
        <Grid container spacing={2}>
          {featureCards.map(feature => (
            <Grid item xs={12} sm={6} md={4} key={feature.card_id}>
              <FeatureCard
                feature={feature}
                expanded={expandedCardId === feature.card_id}
                onToggle={() => handleToggleCard(feature.card_id)}
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Paper
          elevation={0}
          sx={{
            mt: 6,
            p: 6,
            borderRadius: 3,
            border: '1px dashed #d9d9d9',
            textAlign: 'center',
            color: '#8C8C8C'
          }}
        >
          <Typography fontSize="1.05rem" fontWeight={600} mb={1}>
            표시할 Feature 정보가 없습니다
          </Typography>
          <Typography fontSize="0.9rem">
            분석을 다시 실행하거나, FastAPI에서 추출된 Feature 데이터를 확인해주세요.
          </Typography>
        </Paper>
      )}

      {/* 원본 JSON (디버깅용) */}
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
            fontSize: '0.85rem',
            maxHeight: '320px'
          }}
        >
          {JSON.stringify(analysisResult, null, 2)}
        </Box>
      </Paper>
    </Stack>
  )
}

const FeatureCard = ({ feature, expanded, onToggle }) => {
  const metaChips = [
    feature.result_id != null ? `ID: ${feature.result_id}` : null,
    feature.feature_code ? `코드: ${feature.feature_code}` : null,
    typeof feature.vector_similarity === 'number'
      ? `유사도: ${feature.vector_similarity.toFixed(2)}`
      : null,
    feature.chunks_from_announcement
      ? `공고 청크 ${feature.chunks_from_announcement}개`
      : null,
    feature.chunks_from_attachments
      ? `첨부 청크 ${feature.chunks_from_attachments}개`
      : null
  ].filter(Boolean)

  const handleKeyDown = event => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onToggle()
    }
  }

  return (
    <Paper
      elevation={expanded ? 3 : 1}
      sx={{
        p: 3,
        borderRadius: 3,
        height: '100%',
        cursor: 'pointer',
        border: `1px solid ${expanded ? '#1677ff' : '#f0f0f0'}`,
        transition: 'all 0.18s ease',
        transform: expanded ? 'translateY(-4px)' : 'none',
        boxShadow: expanded ? '0px 10px 30px rgba(22, 119, 255, 0.15)' : 'none'
      }}
      onClick={onToggle}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-expanded={expanded}
    >
      <Stack spacing={1.5}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Stack spacing={0.5}>
            <Typography fontSize="1.1rem" fontWeight={700}>
              {feature.feature_name || feature.feature_code || 'Feature'}
            </Typography>
            <Typography fontSize="0.85rem" color="#8C8C8C">
              {feature.feature_code ? `키: ${feature.feature_code}` : '키 값이 지정되지 않았습니다'}
            </Typography>
          </Stack>
          <Chip
            label={expanded ? '값 숨기기' : '값 보기'}
            size="small"
            sx={{ backgroundColor: expanded ? '#f0f5ff' : '#f5f5f5', color: '#262626' }}
          />
        </Box>

        {metaChips.length ? (
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {metaChips.map(label => (
              <Chip key={label} label={label} size="small" sx={{ backgroundColor: '#E6F4FF', color: '#0958d9' }} />
            ))}
          </Stack>
        ) : null}

        <Typography fontSize="0.85rem" color="#8C8C8C">
          {expanded ? '카드를 다시 클릭하면 값을 숨길 수 있습니다.' : '값을 확인하려면 카드를 클릭하세요.'}
        </Typography>

        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Stack spacing={1.5} mt={0.5}>
            {feature.summary ? (
              <Box>
                <Typography fontWeight={600} mb={0.5}>
                  요약
                </Typography>
                <Typography fontSize="0.95rem" color="#595959">
                  {feature.summary}
                </Typography>
              </Box>
            ) : null}

            {Array.isArray(feature.key_points) && feature.key_points.length ? (
              <Box>
                <Typography fontWeight={600} mb={0.5}>
                  핵심 포인트
                </Typography>
                <Stack spacing={0.5}>
                  {feature.key_points.map((point, index) => (
                    <Typography key={index} fontSize="0.9rem" color="#595959">
                      • {point}
                    </Typography>
                  ))}
                </Stack>
              </Box>
            ) : null}

            {feature.full_content ? (
              <Box>
                <Typography fontWeight={600} mb={0.5}>
                  원문 내용
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, backgroundColor: '#fafafa' }}>
                  <Typography fontSize="0.9rem" color="#595959" sx={{ whiteSpace: 'pre-wrap' }}>
                    {feature.full_content}
                  </Typography>
                </Paper>
              </Box>
            ) : null}

            {Array.isArray(feature.referenced_attachments) && feature.referenced_attachments.length ? (
              <Box>
                <Typography fontWeight={600} mb={0.5}>
                  참조 첨부
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {feature.referenced_attachments.map(name => (
                    <Chip key={name} label={name} size="small" sx={{ backgroundColor: '#fff7e6', color: '#ad6800' }} />
                  ))}
                </Stack>
              </Box>
            ) : null}

            {Array.isArray(feature.chunks_used) && feature.chunks_used.length ? (
              <Box>
                <Typography fontWeight={600} mb={0.5}>
                  사용된 청크
                </Typography>
                <Stack spacing={0.5}>
                  {feature.chunks_used.map((chunk, index) => (
                    <Typography key={index} fontSize="0.85rem" color="#8C8C8C">
                      • {formatChunkReference(chunk)}
                    </Typography>
                  ))}
                </Stack>
              </Box>
            ) : null}
          </Stack>
        </Collapse>
      </Stack>
    </Paper>
  )
}

const formatChunkReference = chunk => {
  if (!chunk || typeof chunk !== 'object') return JSON.stringify(chunk)
  const file = chunk.file || chunk.file_name || '파일 미상'
  const section = chunk.section ? `섹션 ${chunk.section}` : null
  const page = chunk.page != null ? `${chunk.page}p` : null
  return [file, section, page].filter(Boolean).join(' · ')
}

export default AnalyzeDashboard
