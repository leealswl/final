import React, { useState } from 'react';
import { Box, Paper, IconButton } from '@mui/material';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

import LeftNav from './LeftNav';
import Sidebar from './Sidebar';
import Assistant from './Assistant';

import { Outlet } from 'react-router-dom';

export default function Layout() {
    const NAV_W = 64; // 왼쪽 얇은 네비 레일
    const SIDEBAR_W = 280; // 프로젝트 트리
    const ASSIST_W = 360; // 우측 어시스턴트 (열렸을 때)

    // 데스크톱 우측 패널 열림 상태
    const [assistOpen, setAssistOpen] = useState(true);

    // 패널 열고닫을 때 에디터가 즉시 리사이즈되도록 resize 이벤트 발행
    const fireResize = () => window.dispatchEvent(new Event('resize'));

    return (
        <Box sx={{ height: '100vh', bgcolor: '#ffffff' }}>
            {/* 메인 3분할/Drawer 영역 */}
            <Box
                sx={{
                    height: '100dvh',
                    display: 'flex',
                    overflow: 'hidden',
                    bgcolor: '#ffffff',
                    minHeight: 0,
                }}
            >
                {/* 왼쪽 네비 레일 (분석/생성/편집/검증) */}
                <Box
                    component="nav"
                    sx={{
                        width: NAV_W,
                        minWidth: NAV_W,
                        borderRight: '1px solid #e5e7eb',
                        bgcolor: '#fff',
                    }}
                >
                    <LeftNav width={NAV_W} />
                </Box>

                {/* 프로젝트 사이드바 */}
                <Paper
                    square
                    elevation={0}
                    sx={{
                        width: SIDEBAR_W,
                        bgcolor: '#fafafa',
                        borderRight: '1px solid #e5e7eb',
                        overflow: 'hidden',
                    }}
                >
                    <Sidebar />
                </Paper>

                {/* Editor: 항상 중앙 */}
                <Box
                    sx={{
                        flex: 1,
                        minWidth: 0,
                        minHeight: 0,
                        height: '100%',
                        bgcolor: '#ffffff',
                        overflow: 'hidden',
                        position: 'relative',
                    }}
                >
                    <Outlet />
                    {/* <Editor /> */}
                    {/* 어시스턴트가 닫혀 있을 때만, 에디터 오른쪽 상단에 "열기" 핸들(‹) */}
                    {!assistOpen && (
                    <IconButton
                      onClick={() => {
                        setAssistOpen(true);
                        // 열자마자 한 프레임 뒤에 리사이즈 신호
                        requestAnimationFrame(fireResize);
                      }}
                      aria-label="어시스턴트 열기"
                      sx={{
                        position: "absolute",
                        right: 8,
                        top: 16,
                        zIndex: 0,
                        bgcolor: "#fff",
                        border: "1px solid #e5e7eb",
                        boxShadow: "0 1px 3px rgba(0,0,0,.06)",
                        "&:hover": { bgcolor: "#fff" },
                      }}
                    >
                      <ChevronLeftIcon />
                    </IconButton>
                  )}
                </Box>

        {/* 오른쪽 어시스턴트 — 열고/닫기 토글만 지원 */}
        <Box
          component="aside"
          sx={{
            width: assistOpen ? ASSIST_W : 0,
            minWidth: assistOpen ? ASSIST_W : 0,
            transition: "width .25s ease",
            bgcolor: "#fafafa",
            borderLeft: assistOpen ? "1px solid #e5e7eb" : "none",
            // overflow: "hidden",
            position: "relative",
          }}
          onTransitionEnd={fireResize}
        >
          {assistOpen && <Assistant />}

          {/* 패널 안쪽 왼쪽 가장자리: "접기" 핸들(›) */}
          <IconButton
            size="small"
            onClick={() => setAssistOpen(false)}
            aria-label="어시스턴트 접기"
            sx={{
              position: "absolute",
              left: -16,
              top: 16,
              zIndex: 3,
              bgcolor: "#fff",
              border: "1px solid #e5e7eb",
              boxShadow: "0 1px 3px rgba(0,0,0,.06)",
              "&:hover": { bgcolor: "#fff" },
            }}
          >
            <ChevronRightIcon />
          </IconButton>
        </Box>
      </Box>
      </Box>
    );
}
