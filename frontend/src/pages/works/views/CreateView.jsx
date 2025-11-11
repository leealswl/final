<<<<<<< HEAD
import {
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAnalysisStore } from '../../../store/useAnalysisStore'

const CreateView = () => {
  const navigate = useNavigate()
  const analysisResult = useAnalysisStore(state => state.analysisResult)
  // 2025-11-09 suyeon: 사용자 입력 데이터를 저장하여 생성 에이전트로 전달하기 위함
  const setUserInputData = useAnalysisStore(state => state.setUserInputData)
  const userForm = analysisResult?.data?.user_form
  const tableOfContents = analysisResult?.data?.table_of_contents || userForm?.table_of_contents
  const tocSections = tableOfContents?.sections || []
  // 목차가 있는데 섹션이 1개 이하이면 간단 응답 폼으로 처리
  const useTocForm = tocSections.length > 1

  const isTemplateBased = userForm?.type === 'template_based'
  const isTocBased = userForm?.type === 'toc_based'

  const formFields = useMemo(() => {
    if (useTocForm) {
      return tocSections.map(section => ({
        field_id: section.number,
        field_name: section.title,
        description: section.description || '',
        required: section.required ?? false,
        placeholder: section.description || `${section.title} 관련 내용을 입력하세요`,
        field_type: 'textarea',
        source: tableOfContents?.source_file || tableOfContents?.source || '공고 목차',
        section
      }))
    }

    if (isTemplateBased) {
      return userForm.fields || []
    }

    return []
  }, [isTemplateBased, tableOfContents?.source, tableOfContents?.source_file, tocSections, useTocForm, userForm])

  const initialValues = useMemo(() => {
    if (!formFields.length) return {}
    return formFields.reduce((acc, field, index) => {
      const key = field.field_id || field.field_name || `field_${index}`
      acc[key] = ''
      return acc
    }, {})
  }, [formFields])

  const [formValues, setFormValues] = useState(initialValues)

  useEffect(() => {
    setFormValues(initialValues)
  }, [initialValues])

  const handleChange = (fieldKey) => (event) => {
    const { value } = event.target
    setFormValues(prev => ({ ...prev, [fieldKey]: value }))
  }

  const handleSaveDraft = () => {
    console.log('📝 Save draft:', formValues)
  }

  const handleReset = () => {
    setFormValues(initialValues)
  }

  // 2025-11-09 suyeon: 초안 생성 버튼 클릭 시 데이터를 저장하고 생성 페이지로 이동
  const handleGenerateDraft = () => {
    // 1. 필수 필드 검증
    const requiredFields = formFields.filter(f => f.required)
    const missingFields = requiredFields.filter(f => {
      const key = f.field_id || f.field_name
      return !formValues[key] || formValues[key].trim() === ''
    })

    if (missingFields.length > 0) {
      alert(`필수 항목을 입력해주세요: ${missingFields.map(f => f.field_name).join(', ')}`)
      return
    }

    // 2. 생성 에이전트로 전달할 데이터 구조화
    const generateData = {
      type: useTocForm ? 'toc_based' : 'template_based',
      formValues,
      formFields,
      tableOfContents: useTocForm ? tableOfContents : null,
      userForm: !useTocForm ? userForm : null,
      timestamp: new Date().toISOString()
    }

    // 3. 스토어에 저장
    setUserInputData(generateData)

    // 4. 생성 페이지로 이동
    navigate('/works/generate')
  }

  if (!analysisResult) {
    return (
      <Stack
        justifyContent="center"
        alignItems="center"
        height="100vh"
        sx={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #e4ecf7 100%)' }}
        spacing={2}
      >
        <Typography fontSize="1.6rem" fontFamily="Isamanru-Bold">
          아직 분석 데이터가 없습니다.
        </Typography>
        <Typography color="#8C8C8C">
          먼저 분석을 실행한 뒤 생성 페이지로 이동해주세요.
        </Typography>
        <Button variant="contained" size="large" onClick={() => navigate('/works/analyze')}>
          분석 페이지로 이동
        </Button>
      </Stack>
    )
  }

  return (
    <Box sx={{ backgroundColor: '#F5F7FA', minHeight: '100vh', p: 4, overflow: 'auto' }}>
      <Stack spacing={4} mx="auto" maxWidth="1200px">
        {/* 헤더 */}
        <Paper elevation={0} sx={{ p: 4, borderRadius: 3, background: 'linear-gradient(135deg, #111827, #1f2937)', color: 'white' }}>
          <Stack spacing={1}>
            <Typography fontSize="2rem" fontFamily="Isamanru-Bold">
              ✍️ 사용자 입력 폼 작성
            </Typography>
            <Typography color="rgba(255,255,255,0.7)" fontFamily="Pretendard4">
              분석된 첨부 양식 기반으로 자동 생성된 입력 폼입니다. 각 항목을 작성하고 저장해 보세요.
            </Typography>
          </Stack>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} mt={3}>
            <Chip
              label={`폼 유형: ${userForm?.type === 'template_based' ? '양식 기반' : '목차 기반'}`}
              sx={{ backgroundColor: 'rgba(255,255,255,0.12)', color: 'white', fontWeight: 500 }}
            />
            {userForm?.source_file && (
              <Chip
                label={`출처 파일: ${userForm.source_file}`}
                sx={{ backgroundColor: 'rgba(255,255,255,0.12)', color: 'white', fontWeight: 500 }}
              />
            )}
            {!userForm?.source_file && tableOfContents?.source_file && (
              <Chip
                label={`목차 출처: ${tableOfContents.source_file}`}
                sx={{ backgroundColor: 'rgba(255,255,255,0.12)', color: 'white', fontWeight: 500 }}
              />
            )}
          </Stack>
        </Paper>

        {/* 첨부 양식 기반 입력 폼 */}
        {!useTocForm && isTemplateBased && (
          <Paper elevation={1} sx={{ p: 4, borderRadius: 3, backgroundColor: 'white' }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" mb={3}>
              <Box>
                <Typography fontSize="1.4rem" fontWeight={700}>
                  주요 항목
                </Typography>
                <Typography color="#8C8C8C" fontFamily="Pretendard4">
                  각 항목은 첨부 양식에서 자동 추출되었습니다. 필요한 정보를 입력하세요.
                </Typography>
              </Box>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                <Button variant="outlined" onClick={handleReset}>초기화</Button>
                <Button variant="contained" onClick={handleSaveDraft}>임시 저장</Button>
              </Stack>
            </Stack>

            <Grid container spacing={3}>
              {formFields.map((field, index) => {
                const key = field.field_id || field.field_name || `field_${index}`
                const helperText = field.description || field.source || ''
                return (
                  <Grid item xs={12} md={6} key={key}>
                    <Stack spacing={1.2}>
                      <Typography fontWeight={600} fontSize="1rem">
                        {field.field_name || `필드 ${index + 1}`}
                        {field.required && <Typography component="span" color="#ff4d4f"> *</Typography>}
                      </Typography>
                      <TextField
                        placeholder={field.placeholder || `${field.field_name || '내용'}을 입력하세요`}
                        variant="outlined"
                        fullWidth
                        multiline={field.field_type === 'textarea' || field.field_type === 'rich_text'}
                        minRows={field.field_type === 'textarea' || field.field_type === 'rich_text' ? 3 : 1}
                        value={formValues[key] ?? ''}
                        onChange={handleChange(key)}
                      />
                      {helperText && (
                        <Typography fontSize="0.85rem" color="#8C8C8C">
                          {helperText}
                        </Typography>
                      )}
                      <Stack direction="row" spacing={1}>
                        <Chip
                          label={field.field_type || 'text'}
                          size="small"
                          sx={{ backgroundColor: '#F0F5FF', color: '#1d39c4' }}
                        />
                        {field.source && (
                          <Chip
                            label={`출처: ${field.source}`}
                            size="small"
                            sx={{ backgroundColor: '#F6FFED', color: '#389e0d' }}
                          />
                        )}
                      </Stack>
                    </Stack>
                  </Grid>
                )
              })}
            </Grid>
          </Paper>
        )}

        {/* 제안서 목차 기반 입력 폼 */}
        {useTocForm && (
          <Stack spacing={3}>
            <Paper
              elevation={1}
              sx={{
                p: 4,
                borderRadius: 3,
                background: 'linear-gradient(135deg, #243B53, #1C2A3A)',
                color: 'white'
              }}
            >
              <Stack spacing={1.5}>
                <Typography fontSize="1.8rem" fontFamily="Isamanru-Bold">
                  ✏️ 제안서 초안 정보 입력 (목차 기반)
                </Typography>
                <Typography color="rgba(255,255,255,0.75)" fontFamily="Pretendard4" fontSize="0.95rem">
                  각 목차 섹션별로 핵심 내용을 작성해주세요. 필요시 AI 제안 문장을 참고하거나 수정하여 입력할 수 있습니다.
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                  <Chip
                    label="폼 유형: 목차 기반"
                    sx={{ backgroundColor: 'rgba(255,255,255,0.12)', color: 'white', fontWeight: 500 }}
                  />
                  {(tableOfContents?.source_file || tableOfContents?.source) && (
                    <Chip
                      label={`목차 출처: ${tableOfContents?.source_file || tableOfContents?.source}`}
                      sx={{ backgroundColor: 'rgba(255,255,255,0.12)', color: 'white', fontWeight: 500 }}
                    />
                  )}
                  <Stack direction="row" spacing={1} sx={{ mt: { xs: 1, sm: 0 } }}>
                    <Button variant="outlined" color="inherit" onClick={handleReset}>
                      초기화
                    </Button>
                    <Button variant="contained" color="primary" onClick={handleSaveDraft}>
                      임시 저장
                    </Button>
                  </Stack>
                </Stack>
              </Stack>
            </Paper>

            {formFields.map((field, index) => {
              const key = field.field_id || field.field_name || `field_${index}`
              const section = field.section || {}
              return (
                <Paper
                  key={key}
                  elevation={0}
                  sx={{
                    borderRadius: 3,
                    border: '1px solid #dbe4ff',
                    background: '#ffffff'
                  }}
                >
                  <Stack spacing={2.5} p={{ xs: 3, md: 4 }}>
                    <Stack spacing={0.75}>
                      <Typography fontSize="1.2rem" fontWeight={700} color="#1f3b73">
                        {section.number ? `${section.number}. ${section.title}` : field.field_name}
                        {field.required && <Typography component="span" color="#d4380d"> *</Typography>}
                      </Typography>
                      {section.description && (
                        <Typography fontSize="0.95rem" color="#64748b">
                          {section.description}
                        </Typography>
                      )}
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        <Chip
                          label={field.required ? '필수' : '선택'}
                          size="small"
                          sx={{
                            backgroundColor: field.required ? '#FFF1F0' : '#F6FFED',
                            color: field.required ? '#d4380d' : '#237804'
                          }}
                        />
                        <Chip
                          label="응답 형식: 장문 텍스트"
                          size="small"
                          sx={{ backgroundColor: '#F0F5FF', color: '#1d39c4' }}
                        />
                      </Stack>
                    </Stack>

                    <TextField
                      placeholder={field.placeholder || `${field.field_name || '내용'}을 입력하세요`}
                      variant="outlined"
                      fullWidth
                      multiline
                      minRows={6}
                      value={formValues[key] ?? ''}
                      onChange={handleChange(key)}
                    />
                  </Stack>
                </Paper>
              )
            })}
          </Stack>
        )}

        {/* 첨부 양식 테이블 미리보기 제거 */}

        {/* 목차 기반일 때 섹션 미리보기 */}
        {useTocForm ? (
          <Paper elevation={0} sx={{ p: 4, borderRadius: 3, backgroundColor: 'white' }}>
            <Typography fontSize="1.4rem" fontWeight={700} mb={2}>
              공고 목차 구조
            </Typography>
            <Stack spacing={1.5}>
              {tableOfContents.sections.map(section => (
                <Paper key={section.number} variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
                  <Stack spacing={0.5}>
                    <Typography fontWeight={600}>
                      {section.number} {section.title}
                    </Typography>
                    {section.description && (
                      <Typography fontSize="0.9rem" color="#8C8C8C">
                        {section.description}
                      </Typography>
                    )}
                    <Stack direction="row" spacing={1}>
                      <Chip
                        label={section.required ? '필수' : '선택'}
                        size="small"
                        sx={{
                          backgroundColor: section.required ? '#FFF1F0' : '#F6FFED',
                          color: section.required ? '#d4380d' : '#237804'
                        }}
                      />
                      {tableOfContents.source && (
                        <Chip
                          label={`출처: ${tableOfContents.source}`}
                          size="small"
                          sx={{ backgroundColor: '#E6F4FF', color: '#0958d9' }}
                        />
                      )}
                    </Stack>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          </Paper>
        ) : null}

        {/* 분석 정보 섹션 */}
        <Paper elevation={0} sx={{ p: 4, borderRadius: 3, backgroundColor: 'white' }}>
          <Typography fontSize="1.2rem" fontWeight={700} mb={2}>
            분석 정보
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Stack spacing={0.5}>
                <Typography color="#8C8C8C" fontSize="0.85rem">분석 상태</Typography>
                <Typography fontWeight={600}>{analysisResult.data?.status ?? analysisResult.status ?? 'SUCCESS'}</Typography>
              </Stack>
            </Grid>
            <Grid item xs={12} md={4}>
              <Stack spacing={0.5}>
                <Typography color="#8C8C8C" fontSize="0.85rem">분석 메시지</Typography>
                <Typography fontWeight={600}>{analysisResult.message || '-'}</Typography>
              </Stack>
            </Grid>
            <Grid item xs={12} md={4}>
              <Stack spacing={0.5}>
                <Typography color="#8C8C8C" fontSize="0.85rem">분석 기준 시각</Typography>
                <Typography fontWeight={600}>
                  {analysisResult.data?.extracted_at || analysisResult.data?.timestamp || '-'}
                </Typography>
              </Stack>
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Typography fontSize="0.85rem" color="#8C8C8C">
            🔒 작성한 데이터는 아직 서버에 저장되지 않았습니다. 임시 저장 버튼을 활용하여 초안을 확인하고,
            필요 시 차후 API 연동을 통해 제출 프로세스를 연결하세요.
          </Typography>
        </Paper>

        {/* 2025-11-09 suyeon: 초안 생성 버튼 추가 - 사용자가 입력 완료 후 생성 에이전트로 이동 */}
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
            <Typography fontSize="1.4rem" fontFamily="Isamanru-Bold">
              📄 제안서 초안 생성하기
            </Typography>
            <Typography fontSize="0.95rem" color="rgba(255,255,255,0.9)">
              입력하신 정보를 바탕으로 AI가 제안서 초안을 자동으로 생성합니다.
            </Typography>
            <Box>
              <Button
                variant="contained"
                size="large"
                onClick={handleGenerateDraft}
                sx={{
                  backgroundColor: 'white',
                  color: '#667eea',
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  px: 5,
                  py: 1.5,
                  '&:hover': {
                    backgroundColor: '#f0f0f0'
                  }
                }}
              >
                초안 생성
              </Button>
            </Box>
          </Stack>
        </Paper>
      </Stack>
    </Box>
  )
}
=======
import React, { useState } from "react";
import { Box, Typography, Alert, Snackbar, Button, Stack } from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import EditNoteIcon from "@mui/icons-material/EditNote";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";
import { useNavigate } from "react-router-dom";

import { useDocumentStore } from "../../../store/useDocumentStore";
import { useFileStore } from "../../../store/useFileStore";

const INTRO_DOC = {
  type: "doc",
  content: [
    {
      type: "heading",
      attrs: { level: 1 },
      content: [{ type: "text", text: "AI 제안서 초안을 생성했습니다." }],
    },
    {
      type: "paragraph",
      content: [
        {
          type: "text",
          text: "우측 AI 도우미에서 입력한 정보를 기반으로 초안이 작성됩니다. 편집 모드에서 자유롭게 다듬어 주세요.",
        },
      ],
    },
  ],
};

export default function CreateView() {
  const navigate = useNavigate();
  const [snackbar, setSnackbar] = useState(null);
  const [creating, setCreating] = useState(false);

  const { setDocumentId, setContent } = useDocumentStore();
  const addNodes = useFileStore((s) => s.addUploadedFileNodes);
  const selectNode = useFileStore((s) => s.selectNode);

  const handleCreateDraft = async () => {
    try {
      setCreating(true);
      const draftId = `draft-${Date.now()}`;
      const displayName = `새 제안서 초안 ${new Date().toLocaleString("ko-KR", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })}`;

      const draftNode = {
        id: draftId,
        type: "file",
        name: displayName,
        mime: "text/markdown",
        meta: { isDraft: true, createdAt: new Date().toISOString() },
      };

      addNodes("root-02", [draftNode]);
      selectNode(draftId);

      setDocumentId(draftId);
      setContent(INTRO_DOC);
      setSnackbar({ severity: "success", message: "새 초안이 준비되었습니다. 편집 페이지로 이동합니다." });
      navigate(`/works/edit/${draftId}`);
    } catch (error) {
      console.error("[CreateView] 초안 생성 실패", error);
      setSnackbar({ severity: "error", message: "초안을 생성하지 못했습니다. 다시 시도해 주세요." });
    } finally {
      setCreating(false);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%", bgcolor: "#ffffff" }}>
      <Box sx={{ px: 3, py: 3, borderBottom: "1px solid #e5e7eb" }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          AI 제안서 생성 준비
        </Typography>
        <Typography variant="body2" color="text.secondary">
          프로젝트 정보를 정리한 뒤 초안을 생성하면, 편집 페이지에서 워드/HWP 스타일 에디터를 통해 세부 내용을 다듬을 수 있습니다.
        </Typography>
      </Box>
>>>>>>> dev

      <Box sx={{ flex: 1, minHeight: 0, display: "grid", placeItems: "center", px: 4 }}>
        <Stack spacing={4} alignItems="center" sx={{ maxWidth: 520, textAlign: "center" }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <DescriptionIcon color="primary" fontSize="large" />
            <Typography variant="subtitle1" fontWeight={600}>
              1. 생성 정보를 입력하고 초안을 만드세요.
            </Typography>
          </Stack>
          <Stack direction="row" spacing={2} alignItems="center">
            <EditNoteIcon color="primary" fontSize="large" />
            <Typography variant="subtitle1" fontWeight={600}>
              2. 생성이 완료되면 편집 페이지에서 문서를 다듬습니다.
            </Typography>
          </Stack>
          <Stack direction="row" spacing={2} alignItems="center">
            <RocketLaunchIcon color="primary" fontSize="large" />
            <Typography variant="subtitle1" fontWeight={600}>
              3. 편집된 결과를 저장하고 제출 흐름으로 진행하세요.
            </Typography>
          </Stack>

          <Typography variant="body2" color="text.secondary">
            좌측 목차와 우측 AI 도우미는 초안 생성 후 자동으로 채워집니다. 지금은 새 초안을 만들어 편집 단계로 이동해 보세요.
          </Typography>

          <Button
            variant="contained"
            size="large"
            onClick={handleCreateDraft}
            disabled={creating}
            sx={{ px: 4, py: 1.5 }}
          >
            {creating ? "초안 준비 중..." : "새 초안 생성하고 편집으로 이동"}
          </Button>
        </Stack>
      </Box>

      <Snackbar open={Boolean(snackbar)} autoHideDuration={2500} onClose={() => setSnackbar(null)}>
        {snackbar ? (
          <Alert severity={snackbar.severity} onClose={() => setSnackbar(null)} sx={{ width: "100%" }}>
            {snackbar.message}
          </Alert>
        ) : null}
      </Snackbar>
    </Box>
  );
}