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