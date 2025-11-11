import React, { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Divider,
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import RefreshIcon from "@mui/icons-material/Refresh";

const PROPOSAL_ENDPOINT = "http://127.0.0.1:8000/generate-proposal";

const defaultForm = {
  projectTitle: "PALADOC AI 기반 행정 서류 자동화 구축",
  goal:
    "지방자치단체의 공공사업 제안서를 신속하게 작성하고 검토할 수 있도록 AI 기반 작성 도구를 도입합니다.",
  requirements:
    "행정 문체와 규격 준수\n핵심 요구사항(사업 범위/예산/일정) 명확화\n협력 기관 및 추진 일정 제시",
  deliverables: "사업 개요서, 추진 계획, 기대 효과, 비용 추정표",
  tone: "공문체",
  extra: "주요 장점과 기대 효과는 표 형식으로 정리해 주세요.",
};

function formatList(text = "") {
  return text
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function requestProposal(payload) {
  const response = await fetch(PROPOSAL_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `FastAPI 응답 오류 (${response.status})`);
  }

  return response.json();
}

export default function CreateAssistant() {
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [history, setHistory] = useState([]);

  const formPayload = useMemo(() => ({
    project_title: form.projectTitle,
    goal: form.goal,
    requirements: formatList(form.requirements),
    deliverables: formatList(form.deliverables),
    tone: form.tone,
    extra: form.extra,
  }), [form]);

  const handleChange = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleReset = () => {
    setForm(defaultForm);
    setMessage(null);
  };

  const handleInsert = (html, meta) => {
    const editor = window.tiptapEditor;
    if (!editor) {
      setMessage({ type: "warning", text: "Tiptap 에디터가 아직 준비되지 않았습니다." });
      return;
    }

    editor.chain().focus().setContent(html, false).run();
    setMessage({ type: "success", text: "AI 초안을 에디터에 반영했습니다." });
    setHistory((prev) => [{ timestamp: new Date(), meta, html }, ...prev.slice(0, 4)]);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const data = await requestProposal(formPayload);
      const html = data?.proposal_html || `<p>${data?.proposal_text || "AI 초안 생성에 실패했습니다."}</p>`;
      handleInsert(html, data?.meta || formPayload);
    } catch (error) {
      console.error("[CreateAssistant] 제안서 생성 실패", error);
      const fallback = `<h2>제안 개요 (샘플)</h2><p>AI 서버에 연결할 수 없어 기본 샘플 초안을 불러왔습니다.</p><p>사업 목표: ${form.goal || "(미입력)"}</p>`;
      handleInsert(fallback, { error: error.message, payload: formPayload });
      setMessage({ type: "error", text: "AI 생성 중 오류가 발생했습니다. 샘플 초안을 삽입했습니다." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box sx={{ px: 2, py: 2, borderBottom: "1px solid #e5e7eb" }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="subtitle1" fontWeight={600}>
            AI 제안서 생성 도우미
          </Typography>
          <Button
            variant="text"
            size="small"
            startIcon={<RefreshIcon fontSize="small" />}
            onClick={handleReset}
          >
            기본값 불러오기
          </Button>
        </Stack>
        <Typography variant="caption" color="text.secondary">
          프로젝트 정보를 입력하고 "AI 초안 생성"을 누르면 중앙 에디터에 바로 반영됩니다.
        </Typography>
      </Box>

      {loading && <LinearProgress sx={{ height: 2 }} />}

      <Box sx={{ p: 2, flex: 1, overflow: "auto", display: "flex", flexDirection: "column", gap: 2 }}>
        <TextField
          label="프로젝트명"
          value={form.projectTitle}
          onChange={handleChange("projectTitle")}
          fullWidth
        />

        <TextField
          label="추진 목표"
          value={form.goal}
          onChange={handleChange("goal")}
          multiline
          minRows={2}
          fullWidth
        />

        <TextField
          label="핵심 요구사항 (줄바꿈으로 구분)"
          value={form.requirements}
          onChange={handleChange("requirements")}
          multiline
          minRows={3}
          fullWidth
        />

        <TextField
          label="주요 산출물 (줄바꿈으로 구분)"
          value={form.deliverables}
          onChange={handleChange("deliverables")}
          multiline
          minRows={3}
          fullWidth
        />

        <TextField
          label="톤 & 스타일"
          value={form.tone}
          onChange={handleChange("tone")}
          helperText="예: 공문체, 보고서용, 홍보 중심 등"
          fullWidth
        />

        <TextField
          label="추가 요청 사항"
          value={form.extra}
          onChange={handleChange("extra")}
          multiline
          minRows={2}
          fullWidth
        />

        <Button
          variant="contained"
          size="large"
          startIcon={<AutoAwesomeIcon />}
          onClick={handleGenerate}
          disabled={loading}
        >
          AI 초안 생성
        </Button>

        {message && (
          <Alert severity={message.type} onClose={() => setMessage(null)}>
            {message.text}
          </Alert>
        )}

        {history.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Divider sx={{ mb: 1 }}>최근 생성 기록</Divider>
            <Stack spacing={1}>
              {history.map((item, index) => (
                <Typography key={index} variant="caption" color="text.secondary">
                  {item.timestamp.toLocaleTimeString()} · {item.meta?.project_title || form.projectTitle}
                </Typography>
              ))}
            </Stack>
          </Box>
        )}
      </Box>
    </Box>
  );
}

