import React, { useState } from "react";
import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  Paper,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import HistoryIcon from "@mui/icons-material/History";
import DashboardIcon from "@mui/icons-material/Dashboard";
import AssessmentIcon from "@mui/icons-material/Assessment";
import SaveOutlinedIcon from "@mui/icons-material/SaveOutlined";

import Sidebar from "./Sidebar";
import Editor from "./Editor";
import Assistant from "./Assistant";

export default function Layout() {
  const theme = useTheme();
  const mdUp = useMediaQuery(theme.breakpoints.up("md"));

  const APPBAR_H = 56;

  // 반응형 폭
  const SIDEBAR_W = { xs: "75vw", sm: 260, md: 280, lg: 300 };
  const ASSIST_W  = { xs: "85vw", sm: 300, md: 360, lg: 380 };

  // 모바일 Drawer 제어
  const [leftOpen, setLeftOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(false);

  return (
    <Box sx={{ height: "100dvh", bgcolor: "#ffffff" }}>
      {/* 상단 AppBar (라이트) */}
      <AppBar
        position="static"
        elevation={0}
        color="default"
        sx={{ bgcolor: "#ffffff", borderBottom: "1px solid #e5e7eb" }}
      >
        <Toolbar sx={{ minHeight: APPBAR_H, px: 1, gap: 1 }}>
          {/* md 미만: 좌측 Drawer 열기 */}
          {!mdUp && (
            <IconButton onClick={() => setLeftOpen(true)}>
              <MenuIcon />
            </IconButton>
          )}

          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
            정부과제 솔루션 제안
          </Typography>

          <Divider flexItem orientation="vertical" sx={{ mx: 2, borderColor: "#e5e7eb" }} />
          <Box sx={{ flex: 1 }} />

          {/* 상단 컨트롤 */}
          <Stack direction="row" spacing={1} alignItems="center">
            <Button variant="contained" size="small" startIcon={<AssessmentIcon />}>
              AI 분석
            </Button>
            <Button variant="contained" size="small">
              예상 점수
            </Button>
            <Button variant="outlined" size="small" startIcon={<SaveOutlinedIcon />}>
              저장
            </Button>

            <Divider flexItem orientation="vertical" sx={{ mx: 1, borderColor: "#e5e7eb" }} />
            <IconButton onClick={() => {/* TODO: 히스토리 */}}>
              <HistoryIcon />
            </IconButton>
            <IconButton onClick={() => {/* TODO: 대시보드 */}}>
              <DashboardIcon />
            </IconButton>

            {/* md 미만: 우측 Drawer(Assistant) 열기 */}
            {!mdUp && (
              <IconButton onClick={() => setRightOpen(true)}>
                <ChatBubbleOutlineIcon />
              </IconButton>
            )}
          </Stack>
        </Toolbar>
      </AppBar>

      {/* 메인 3분할/Drawer 영역 */}
      <Box
        sx={{
          height: `calc(100dvh - ${APPBAR_H}px)`,
          display: "flex",
          overflow: "hidden",
          bgcolor: "#ffffff",
        }}
      >
        {/* Sidebar: md 이상 고정, md 미만 Drawer */}
        {mdUp ? (
          <Paper
            square
            elevation={0}
            sx={{
              width: SIDEBAR_W,
              bgcolor: "#fafafa",
              borderRight: "1px solid #e5e7eb",
              overflow: "hidden",
            }}
          >
            <Sidebar />
          </Paper>
        ) : (
          <Drawer
            open={leftOpen}
            onClose={() => setLeftOpen(false)}
            anchor="left"
            PaperProps={{ sx: { width: SIDEBAR_W, bgcolor: "#fafafa" } }}
          >
            <Sidebar />
          </Drawer>
        )}

        {/* Editor: 항상 중앙 */}
        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            bgcolor: "#ffffff",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <Editor />
        </Box>

        {/* Assistant: md 이상 고정, md 미만 Drawer */}
        {mdUp ? (
          <Paper
            square
            elevation={0}
            sx={{
              width: ASSIST_W,
              bgcolor: "#fafafa",
              borderLeft: "1px solid #e5e7eb",
              overflow: "hidden",
            }}
          >
            <Assistant />
          </Paper>
        ) : (
          <Drawer
            open={rightOpen}
            onClose={() => setRightOpen(false)}
            anchor="right"
            PaperProps={{ sx: { width: ASSIST_W, bgcolor: "#fafafa" } }}
          >
            <Assistant />
          </Drawer>
        )}
      </Box>
    </Box>
  );
}
