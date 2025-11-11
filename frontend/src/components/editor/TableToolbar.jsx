import React from "react";
import { Box, IconButton, Tooltip } from "@mui/material";
import TableColumnsIcon from "@mui/icons-material/ViewColumn";
import TableRowsIcon from "@mui/icons-material/ViewAgenda";
import TableRowsDeleteIcon from "@mui/icons-material/HorizontalRule";
import TableColumnsDeleteIcon from "@mui/icons-material/Remove";
import TableChartIcon from "@mui/icons-material/TableChart";
import DeleteIcon from "@mui/icons-material/Delete";
import PaletteIcon from "@mui/icons-material/Palette";
import MergeTypeIcon from "@mui/icons-material/MergeType";
import CallSplitIcon from "@mui/icons-material/CallSplit";

const setBackground = (editor, color) => {
  editor.chain().focus().setCellAttribute("style", color ? `--paladoc-cell-bg:${color}` : null).run();
};

export default function TableToolbar({ editor }) {
  if (!editor) return null;

  const commands = {
    addColumnBefore: () => editor.chain().focus().addColumnBefore().run(),
    addColumnAfter: () => editor.chain().focus().addColumnAfter().run(),
    deleteColumn: () => editor.chain().focus().deleteColumn().run(),
    addRowBefore: () => editor.chain().focus().addRowBefore().run(),
    addRowAfter: () => editor.chain().focus().addRowAfter().run(),
    deleteRow: () => editor.chain().focus().deleteRow().run(),
    toggleHeaderRow: () => editor.chain().focus().toggleHeaderRow().run(),
    deleteTable: () => editor.chain().focus().deleteTable().run(),
    mergeCells: () => editor.chain().focus().mergeCells().run(),
    splitCell: () => editor.chain().focus().splitCell().run(),
  };

  return (
    <Box
      className="table-toolbar"
      sx={{
        position: "absolute",
        right: 24,
        top: 120,
        background: "#fff",
        border: "1px solid #CBD5F5",
        borderRadius: 1,
        boxShadow: "0 2px 8px rgba(15,23,42,0.12)",
        zIndex: 5,
        display: "grid",
        gap: 0.5,
        p: 1,
      }}
    >
      <Box sx={{ display: "flex", gap: 0.5 }}>
        <Tooltip title="셀 병합">
          <IconButton size="small" onClick={commands.mergeCells}>
            <MergeTypeIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="셀 분할">
          <IconButton size="small" onClick={commands.splitCell}>
            <CallSplitIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Box sx={{ display: "flex", gap: 0.5 }}>
        <Tooltip title="열 추가">
          <IconButton size="small" onClick={commands.addColumnAfter}>
            <TableColumnsIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="열 삭제">
          <IconButton size="small" onClick={commands.deleteColumn}>
            <TableColumnsDeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="행 추가">
          <IconButton size="small" onClick={commands.addRowAfter}>
            <TableRowsIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="행 삭제">
          <IconButton size="small" onClick={commands.deleteRow}>
            <TableRowsDeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="머리글 토글">
          <IconButton size="small" onClick={commands.toggleHeaderRow}>
            <TableChartIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="표 삭제">
          <IconButton size="small" onClick={commands.deleteTable}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Box sx={{ display: "flex", gap: 0.5 }}>
        <Tooltip title="머리글 색">
          <IconButton
            size="small"
            onClick={() => setBackground(editor, "#e2e8f0")}
            sx={{ border: "1px solid #cbd5f5", bgcolor: "#e2e8f0" }}
          />
        </Tooltip>
        <Tooltip title="본문 음영">
          <IconButton
            size="small"
            onClick={() => setBackground(editor, "#f8fafc")}
            sx={{ border: "1px solid #cbd5f5", bgcolor: "#f8fafc" }}
          />
        </Tooltip>
        <Tooltip title="색 지우기">
          <IconButton size="small" onClick={() => setBackground(editor, null)}>
            <PaletteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}

