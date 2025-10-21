import React, { useMemo, useRef, useState } from "react";
import {
  Box,
  Stack,
  Typography,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material";
import { SimpleTreeView, TreeItem } from "@mui/x-tree-view";

import UploadIcon from "@mui/icons-material/Upload";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import FolderIcon from "@mui/icons-material/Folder";
import DescriptionIcon from "@mui/icons-material/Description";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";

import { useFileStore } from "../../../../store/useFileStore";


// ── 파일 아이콘 ──────────────────────────────────────────────────────────────
const FileIcon = ({ mime = "", name = "" }) => {
  const lower = name.toLowerCase();
  if (mime.includes("pdf") || lower.endsWith(".pdf")) return <PictureAsPdfIcon fontSize="small" sx={{ mr: 1 }} />;
  if (mime.startsWith("text/") || mime.includes("markdown") || lower.endsWith(".md") || lower.endsWith(".txt"))
    return <DescriptionIcon fontSize="small" sx={{ mr: 1 }} />;
  if (lower.endsWith(".docx")) return <InsertDriveFileIcon fontSize="small" sx={{ mr: 1 }} />;
  return <InsertDriveFileIcon fontSize="small" sx={{ mr: 1 }} />;
};

// ── 트리에서 id로 노드 찾기 ──────────────────────────────────────────────────
function findNode(nodes, id) {
  for (const n of nodes) {
    if (n.id === id) return n;
    if (n.children) {
      const k = findNode(n.children, id);
      if (k) return k;
    }
  }
  return null;
}

// ── 메인 컴포넌트 ───────────────────────────────────────────────────────────
export default function Sidebar() {
  const {
    tree,
    selectedNodeId,
    selectNode,
    uploadFiles,   // zustand: 프론트 더미 or 백엔드 업로드
    renameNode,    // zustand: 이름 변경
  } = useFileStore();

  // 현재 선택한 노드(폴더면 업로드 위치로 사용)
  const selectedNode = useMemo(
    () => (selectedNodeId ? findNode(tree, selectedNodeId) : null),
    [tree, selectedNodeId]
  );

  // ── 업로드 핸들러 ─────────────────────────────────────────────────────────
  const fileInputRef = useRef(null);
  const onClickUpload = () => fileInputRef.current?.click();

  const onChangeUpload = async (e) => {
    const files = e.target.files;
    if (!files?.length) return;
    const parentId =
      selectedNode?.type === "folder" ? selectedNode.id : tree?.[0]?.id ?? null;
    try {
      await uploadFiles(files, parentId);
    } finally {
      e.target.value = ""; // 같은 파일 다시 선택 가능
    }
  };

  // ── 이름 변경 다이얼로그 ──────────────────────────────────────────────────
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState("");

  const openRename = (node) => {
    setRenameTarget(node);
    setRenameValue(node.name);
    setRenameOpen(true);
  };
  const closeRename = () => setRenameOpen(false);
  const confirmRename = () => {
    if (renameTarget && renameValue.trim()) {
      renameNode(renameTarget.id, renameValue.trim());
    }
    setRenameOpen(false);
  };

  // ── 트리 렌더러 ────────────────────────────────────────────────────────────
  const renderNode = (node) => {
    const isFolder = node.type === "folder";

    const label = (
      <Stack
        direction="row"
        alignItems="center"
        spacing={0.5}
        sx={{ pr: 1, "&:hover .rename-btn": { opacity: 1 } }}
      >
        {isFolder ? (
          <FolderIcon fontSize="small" sx={{ mr: 1, color: "#6b7280" }} />
        ) : (
          <FileIcon mime={node.mime} name={node.name} />
        )}

        <Typography variant="body2" sx={{ flex: 1, minWidth: 0 }}>
          {node.name}
        </Typography>


        {/* 이름 변경 버튼 (호버 시 나타남) */}
        <IconButton
          size="small"
          className="rename-btn"
          sx={{ opacity: 0, transition: "opacity .15s" }}
          onClick={(e) => {
            e.stopPropagation();
            openRename(node);
          }}
          aria-label="rename"
        >
          <EditOutlinedIcon fontSize="inherit" />
        </IconButton>
      </Stack>
    );

    return (
      <TreeItem
        key={node.id}
        itemId={String(node.id)}  // SimpleTreeView는 itemId 사용
        label={label}
        onClick={() => selectNode(node.id)}
      >
        {Array.isArray(node.children) && node.children.map(renderNode)}
      </TreeItem>
    );
  };

  return (
    <Box sx={{ height: "100%", p: 1, overflow: "auto", bgcolor: "background.paper" }}>
      {/* 헤더: 타이틀 + 업로드 버튼 */}
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ px: 1, pb: 1 }}
      >
        <Typography variant="subtitle2" sx={{ color: "#374151" }}>
          제안서 파일
        </Typography>

        <Button size="small" startIcon={<UploadIcon />} onClick={onClickUpload}>
          업로드
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          hidden
          multiple
          accept=".md,.txt,.pdf,.docx,.hwp,.hwpx"
          onChange={onChangeUpload}
        />
      </Stack>

      {/* 트리 */}
      <SimpleTreeView
        slots={{ collapseIcon: ExpandMoreIcon, expandIcon: ChevronRightIcon }}
        selectedItems={selectedNodeId ? [String(selectedNodeId)] : []}
        defaultExpandedItems={(tree || []).map((n) => String(n.id))}
        sx={{
          "& .MuiTreeItem-label": { py: 0.5 },
          "& .MuiTreeItem-content.Mui-selected .MuiTreeItem-label": {
            bgcolor: "rgba(2,132,199,0.10)",
            borderRadius: 1,
          },
        }}
      >
        {(tree || []).map(renderNode)}
      </SimpleTreeView>

      {/* 이름 변경 다이얼로그 */}
      <Dialog open={renameOpen} onClose={closeRename}>
        <DialogTitle>이름 변경</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmRename();
            }}
            placeholder="새 이름을 입력하세요"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeRename}>취소</Button>
          <Button variant="contained" onClick={confirmRename}>
            확인
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
