import React, { useState, useMemo } from "react";
import { NodeViewWrapper } from "@tiptap/react";
import {
  Box,
  Button,
  Divider,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import PhotoSizeSelectSmallIcon from "@mui/icons-material/PhotoSizeSelectSmall";

const IMAGE_SIZE_OPTIONS = [
  { value: "small", label: "40%" },
  { value: "medium", label: "60%" },
  { value: "large", label: "80%" },
  { value: "full", label: "100%" },
];

export default function ImageNodeView({ node, updateAttributes, deleteNode, getPos, editor, selected }) {
  const [menuState, setMenuState] = useState(null);

  const sizeLabel = useMemo(() => {
    const current = IMAGE_SIZE_OPTIONS.find((option) => option.value === node.attrs.size);
    return current?.label ?? "맞춤";
  }, [node.attrs.size]);

  const openContextMenu = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const position = { mouseX: event.clientX + 2, mouseY: event.clientY - 6 };
    setMenuState(position);
    const pos = getPos?.();
    if (typeof pos === "number") {
      editor?.chain().setNodeSelection(pos).run();
    }
  };

  const closeContextMenu = () => setMenuState(null);

  const handleResize = (size) => {
    updateAttributes({ size });
    closeContextMenu();
  };

  const handleDelete = () => {
    deleteNode();
    closeContextMenu();
  };

  return (
    <NodeViewWrapper
      className={`paladoc-image-wrapper${selected ? " selected" : ""}`}
      data-drag-handle
    >
      <div className="paladoc-image-inner" onContextMenu={openContextMenu}>
        <img
          src={node.attrs.src}
          alt={node.attrs.alt || "이미지"}
          data-size={node.attrs.size || "medium"}
          className="paladoc-image"
          draggable={false}
        />
        {selected ? (
          <>
            <span className="paladoc-image-handle handle-tl" />
            <span className="paladoc-image-handle handle-tr" />
            <span className="paladoc-image-handle handle-bl" />
            <span className="paladoc-image-handle handle-br" />
          </>
        ) : null}
      </div>

      <Menu
        open={Boolean(menuState)}
        onClose={closeContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          menuState
            ? { top: menuState.mouseY, left: menuState.mouseX }
            : undefined
        }
      >
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography variant="caption" sx={{ color: "#475569" }}>
            이미지 크기 ({sizeLabel})
          </Typography>
          <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
            {IMAGE_SIZE_OPTIONS.map((option) => (
              <Button
                key={option.value}
                size="small"
                variant={node.attrs.size === option.value ? "contained" : "outlined"}
                startIcon={<PhotoSizeSelectSmallIcon fontSize="inherit" />}
                onClick={() => handleResize(option.value)}
                sx={{ textTransform: "none", fontSize: 12, minWidth: 88 }}
              >
                {option.label}
              </Button>
            ))}
          </Box>
        </Box>
        <Divider sx={{ my: 0.5 }} />
        <MenuItem onClick={handleDelete}>
          <DeleteOutlineIcon fontSize="small" sx={{ mr: 1 }} /> 삭제
        </MenuItem>
      </Menu>
    </NodeViewWrapper>
  );
}
