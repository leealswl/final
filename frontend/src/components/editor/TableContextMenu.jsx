import React from "react";
import {
  Divider,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import TableRowsIcon from "@mui/icons-material/ViewAgenda";
import TableRowsDeleteIcon from "@mui/icons-material/HorizontalRule";
import TableColumnsIcon from "@mui/icons-material/ViewColumn";
import TableColumnsDeleteIcon from "@mui/icons-material/Remove";
import TableChartIcon from "@mui/icons-material/TableChart";
import MergeTypeIcon from "@mui/icons-material/MergeType";
import CallSplitIcon from "@mui/icons-material/CallSplit";
import DeleteIcon from "@mui/icons-material/Delete";

export default function TableContextMenu({ anchor, onClose, editor }) {
  const open = Boolean(anchor);
  const anchorPosition = anchor
    ? { top: Math.round(anchor.mouseY), left: Math.round(anchor.mouseX) }
    : undefined;

  const runCommand = (callback) => {
    if (!editor) return;
    callback?.(editor.chain().focus());
    onClose();
  };

  const can = editor?.can?.();

  const items = [
    {
      label: "행 추가 (위)",
      icon: <TableRowsIcon fontSize="small" />,
      enabled: can?.addRowBefore?.(),
      action: () => runCommand((chain) => chain.addRowBefore().run()),
    },
    {
      label: "행 추가 (아래)",
      icon: <TableRowsIcon fontSize="small" />,
      enabled: can?.addRowAfter?.(),
      action: () => runCommand((chain) => chain.addRowAfter().run()),
    },
    {
      label: "행 삭제",
      icon: <TableRowsDeleteIcon fontSize="small" />,
      enabled: can?.deleteRow?.(),
      action: () => runCommand((chain) => chain.deleteRow().run()),
    },
    "divider",
    {
      label: "열 추가 (왼쪽)",
      icon: <TableColumnsIcon fontSize="small" />,
      enabled: can?.addColumnBefore?.(),
      action: () => runCommand((chain) => chain.addColumnBefore().run()),
    },
    {
      label: "열 추가 (오른쪽)",
      icon: <TableColumnsIcon fontSize="small" />,
      enabled: can?.addColumnAfter?.(),
      action: () => runCommand((chain) => chain.addColumnAfter().run()),
    },
    {
      label: "열 삭제",
      icon: <TableColumnsDeleteIcon fontSize="small" />,
      enabled: can?.deleteColumn?.(),
      action: () => runCommand((chain) => chain.deleteColumn().run()),
    },
    "divider",
    {
      label: "셀 병합",
      icon: <MergeTypeIcon fontSize="small" />,
      enabled: can?.mergeCells?.(),
      action: () => runCommand((chain) => chain.mergeCells().run()),
    },
    {
      label: "셀 분할",
      icon: <CallSplitIcon fontSize="small" />,
      enabled: can?.splitCell?.(),
      action: () => runCommand((chain) => chain.splitCell().run()),
    },
    {
      label: "머리글 행 토글",
      icon: <TableChartIcon fontSize="small" />,
      enabled: can?.toggleHeaderRow?.(),
      action: () => runCommand((chain) => chain.toggleHeaderRow().run()),
    },
    "divider",
    {
      label: "표 삭제",
      icon: <DeleteIcon fontSize="small" color="error" />,
      enabled: can?.deleteTable?.(),
      action: () => runCommand((chain) => chain.deleteTable().run()),
      color: "error.main",
    },
  ];

  return (
    <Menu
      open={open}
      onClose={onClose}
      anchorReference="anchorPosition"
      anchorPosition={anchorPosition}
      transformOrigin={{ horizontal: "left", vertical: "top" }}
    >
      <Typography sx={{ px: 2, py: 1, fontSize: 12, color: "#475569" }}>
        표 도구
      </Typography>
      <Divider />
      {items.map((item, index) =>
        item === "divider" ? (
          <Divider key={`divider-${index}`} sx={{ my: 0.5 }} />
        ) : (
          <MenuItem
            key={item.label}
            disabled={!item.enabled}
            onClick={item.action}
            sx={{ color: item.color || "inherit" }}
          >
            <ListItemIcon sx={{ minWidth: 32 }}>{item.icon}</ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontSize: 14 }}>
              {item.label}
            </ListItemText>
          </MenuItem>
        )
      )}
    </Menu>
  );
}
