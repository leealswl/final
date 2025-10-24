 import React, { useMemo, useRef, useState } from "react";
import {
  Box, Stack, Typography, Button, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
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
import useUpload from "../../../../hooks/useUpload";
import { filesToNodes } from "../../../../utils/fileToNodes";

const FileIcon = ({ mime = "", name = "" }) => {
  const lower = (name || "").toLowerCase();
  if (mime.includes("pdf") || lower.endsWith(".pdf")) return <PictureAsPdfIcon fontSize="small" sx={{ mr: 1 }} />;
  if (mime.startsWith("text/") || mime.includes("markdown") || lower.endsWith(".md") || lower.endsWith(".txt"))
    return <DescriptionIcon fontSize="small" sx={{ mr: 1 }} />;
  if (lower.endsWith(".docx")) return <InsertDriveFileIcon fontSize="small" sx={{ mr: 1 }} />;
  return <InsertDriveFileIcon fontSize="small" sx={{ mr: 1 }} />;
};

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
const resolveRootId = (selectedNode, tree) =>
  selectedNode?.type === "folder" && /^root-\d{2}$/.test(selectedNode.id)
    ? selectedNode.id
    : (tree?.[0]?.id ?? "root-01");

export default function Sidebar() {
  const { tree, selectedNodeId, selectNode, addUploadedFileNodes, renameNode } = useFileStore();
  const projectId = useFileStore(s => s.currentProjectId);
  const userId    = useFileStore(s => s.currentUserId);
  const { uploadAsync, isUploading } = useUpload();

  const [expandedItems, setExpandedItems] = useState(() => (tree || []).map(n => String(n.id)));
  const selectedNode = useMemo(
    () => (selectedNodeId ? findNode(tree, selectedNodeId) : null),
    [tree, selectedNodeId]
  );

  // 업로드
  const fileInputRef = useRef(null);
  const onClickUpload = () => fileInputRef.current?.click();
  const onChangeUpload = async (e) => {
    const files = e.target.files;
    if (!files?.length) return;
    if (!projectId || !userId) { alert('컨텍스트가 없습니다.'); e.target.value = ''; return; }

    const rootId = resolveRootId(selectedNode, tree);
    try {
      await uploadAsync({ files, rootId }); // projectId/userId는 훅 내부에서 스토어로
      const nodes = filesToNodes({ files, rootId, projectId, userId });
      addUploadedFileNodes(rootId, nodes);
      setExpandedItems(prev => Array.from(new Set([...prev, String(rootId)])));
      selectNode(nodes[0].id);
    } catch (err) {
      alert(`업로드 실패: ${err?.message || err}`);
    } finally {
      e.target.value = "";
    }
  };

  // 이름 변경
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const openRename = (node) => { setRenameTarget(node); setRenameValue(node.name); setRenameOpen(true); };
  const closeRename = () => setRenameOpen(false);
  const confirmRename = () => {
    if (renameTarget && renameValue.trim()) renameNode(renameTarget.id, renameValue.trim());
    setRenameOpen(false);
  };

  const renderNode = (node) => {
    const isFolder = node.type === "folder";
    const label = (
      <Stack direction="row" alignItems="center" spacing={0.5} sx={{ pr: 1, "&:hover .rename-btn": { opacity: 1 } }}>
        {isFolder ? (
          <FolderIcon fontSize="small" sx={{ mr: 1, color: "#6b7280" }} />
        ) : (
          <FileIcon mime={node.mime} name={node.name} />
        )}
        <Typography variant="body2" sx={{ flex: 1, minWidth: 0 }}>{node.name}</Typography>
        {!isFolder && (
          <IconButton
            size="small"
            className="rename-btn"
            sx={{ opacity: 0, transition: "opacity .15s" }}
            onClick={(e) => { e.stopPropagation(); openRename(node); }}
            aria-label="rename"
          >
            <EditOutlinedIcon fontSize="inherit" />
          </IconButton>
        )}
      </Stack>
    );

    return (
      <TreeItem key={node.id} itemId={String(node.id)} label={label}>
        {Array.isArray(node.children) && node.children.map(renderNode)}
      </TreeItem>
    );
  };

  return (
    <Box sx={{ height: "100%", p: 1, overflow: "auto", bgcolor: "background.paper" }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ px: 1, pb: 1 }}>
        <Typography variant="subtitle2" sx={{ color: "#374151" }}>제안서 파일</Typography>
        <Button size="small" startIcon={<UploadIcon />} onClick={onClickUpload} disabled={isUploading}>
          업로드
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          hidden
          multiple
          accept=".md,.txt,.pdf,.docx,.hwp,.hwpx,.xlsx,.pptx"
          onChange={onChangeUpload}
        />
      </Stack>

      <SimpleTreeView
        slots={{ collapseIcon: ExpandMoreIcon, expandIcon: ChevronRightIcon }}
        selectedItems={selectedNodeId ? [String(selectedNodeId)] : []}
        expandedItems={expandedItems}
        onExpandedItemsChange={(_e, items) => setExpandedItems(items)}
        onItemClick={(_e, itemId) => selectNode(itemId)}
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

      <Dialog open={renameOpen} onClose={closeRename}>
        <DialogTitle>이름 변경</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus fullWidth
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") confirmRename(); }}
            placeholder="새 이름을 입력하세요"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeRename}>취소</Button>
          <Button variant="contained" onClick={confirmRename}>확인</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
