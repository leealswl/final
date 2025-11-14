import React from "react";
import { Box, List, ListItemButton, ListItemText, Typography } from "@mui/material";

import { useCreateStore } from "../../store/useCreateStore";
import { useNavigate } from "react-router";

const levelIndent = {
  1: 1,
  2: 2,
  3: 3,
};

export default function CreateTocSidebar() {
  const toc = useCreateStore((s) => s.toc);
  const activeId = useCreateStore((s) => s.activeHeadingId);
  const setActive = useCreateStore((s) => s.setActiveHeading);

  const handleClick = (item) => {
    setActive(item.id);
    const editor = window.tiptapEditor;
    if (!editor) return;

    const targetPos = Math.min(item.from + 1, item.to - 1);
    editor
      .chain()
      .focus()
      .setTextSelection({ from: targetPos, to: targetPos })
      .scrollIntoView()
      .run();
  };

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column", bgcolor: "#f8fafc" }}>
      <Box sx={{ px: 2, py: 2, borderBottom: "1px solid #e5e7eb" }}>
        <Typography variant="subtitle2" fontWeight={600} color="text.primary">
          제안서 목차
        </Typography>
        <Typography variant="caption" color="text.secondary">
          중앙 문서의 제목(Heading)을 자동으로 불러와 섹션 간 이동을 도와줍니다.
        </Typography>
      </Box>

      <Box sx={{ flex: 1, overflow: "auto" }}>
        {toc.length === 0 ? (
          <Box sx={{ px: 2, py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              아직 생성된 제목이 없습니다. AI 초안 생성 후 자동으로 채워집니다.
            </Typography>
          </Box>
        ) : (
          <List dense disablePadding>
            {toc.map((item) => (
              <ListItemButton
                key={item.id}
                selected={activeId === item.id}
                onClick={() => handleClick(item)}
                sx={{
                  pl: (levelIndent[item.level] || 1) * 2,
                  py: 1,
                  '&.Mui-selected': {
                    bgcolor: "rgba(2,132,199,0.12)",
                    '&:hover': { bgcolor: "rgba(2,132,199,0.18)" },
                  },
                }}
              >
                <ListItemText
                  primaryTypographyProps={{
                    variant: item.level === 1 ? "subtitle2" : "body2",
                    fontWeight: item.level === 1 ? 700 : 500,
                    sx: { whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
                  }}
                  primary={item.text}
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </Box>
    </Box>
  );
}

