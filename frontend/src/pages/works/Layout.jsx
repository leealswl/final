import React, { useState } from 'react';
import { Box, Paper, IconButton } from '@mui/material';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

import LeftNav from './LeftNav';
import Sidebar from './Sidebar';

import CreateTocSidebar from './CreateTocSidebar';
import TocSidebar from './edit/TocSidebar';

import { Outlet, useLocation } from 'react-router-dom';
import { useLayoutStore } from '../../store/useLayoutStore';

export default function Layout() {
    const NAV_W = 64; // 왼쪽 얇은 네비 레일
    const SIDEBAR_W = 280; // 프로젝트 트리
    const ASSIST_W = 360; // 우측 어시스턴트 (열렸을 때)

    // 사이드바 토글 상태
    const sidebarOpen = useLayoutStore((s) => s.sidebarOpen);

    // 데스크톱 우측 패널 열림 상태
    const [assistOpen, setAssistOpen] = useState(true);
    const location = useLocation();
    const isCreateMode = location.pathname.startsWith('/works/create');
    const isEditMode = location.pathname.startsWith('/works/edit');

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
                        display: 'flex',
                        width: NAV_W,
                        minWidth: NAV_W,
                        borderRight: '1px solid #e5e7eb',
                        bgcolor: '#fff',
                    }}
                >
                    <LeftNav width={NAV_W} />
                </Box>

                {/* 프로젝트 사이드바 / 목차 사이드바 (토글 가능) */}
                <Paper
                    square
                    elevation={0}
                    sx={{
                        width: sidebarOpen ? SIDEBAR_W : 0,
                        minWidth: sidebarOpen ? SIDEBAR_W : 0,
                        bgcolor: '#fafafa',
                        borderRight: sidebarOpen ? '1px solid #e5e7eb' : 'none',
                        overflow: 'hidden',
                        transition: 'width 0.3s ease, min-width 0.3s ease',
                    }}
                    onTransitionEnd={fireResize}
                >
                    {sidebarOpen && (
                        <>
                            {isEditMode ? (
                                <TocSidebar />
                            ) : isCreateMode ? (
                                <CreateTocSidebar />
                            ) : (
                                <Sidebar />
                            )}
                        </>
                    )}
                </Paper>

                {/* Editor: 항상 중앙 */}
                <Box
                    sx={{
                        flex: 1,
                        minWidth: 0,
                        minHeight: 0,
                        height: '100%',
                        bgcolor: '#ffffff',
                        position: 'relative',
                        overflow: 'hidden',
                    }}
                >
                    <Box
                        sx={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            overflowY: 'auto',
                            overflowX: 'hidden',
                            bgcolor: '#f5f7fa',
                        }}
                    >
                        <Outlet />
                    </Box>
                    {/* <Editor /> */}
                    {/* 어시스턴트가 닫혀 있을 때만, 에디터 오른쪽 상단에 "열기" 핸들(‹) */}
                    {/* {!assistOpen && (
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
          )} */}
                </Box>

                {/* 오른쪽 어시스턴트 — 열고/닫기 토글만 지원 */}
                {/* <Box
                    component="aside"
                    sx={{
                        width: assistOpen ? ASSIST_W : 0,
                        minWidth: assistOpen ? ASSIST_W : 0,
                        transition: 'width .25s ease',
                        bgcolor: '#fafafa',
                        borderLeft: assistOpen ? '1px solid #e5e7eb' : 'none',
                        // overflow: "hidden",
                        position: 'relative',
                    }}
                    onTransitionEnd={fireResize}
                >
                    {isCreateMode ? <CreateAssistant /> : <Assistant />} */}

                {/* 패널 안쪽 왼쪽 가장자리: "접기" 핸들(›) */}
                {/* <IconButton
                        size="small"
                        onClick={() => {
                            setAssistOpen((prev) => {
                                const next = !prev;
                                if (next) {
                                    // 창이 열릴 때만 fireResize 실행
                                    requestAnimationFrame(fireResize);
                                }
                                return next;
                            });
                        }}
                        aria-label="어시스턴트 접기"
                        sx={{
                            position: 'absolute',
                            ...(assistOpen
                                ? { left: -16, right: undefined } // 열린 상태
                                : { left: undefined, right: 8 }), // 닫힌 상태
                            top: 16,
                            zIndex: 1,
                            bgcolor: '#fff',
                            border: '1px solid #e5e7eb',
                            boxShadow: '0 1px 3px rgba(0,0,0,.06)',
                            '&:hover': { bgcolor: '#fff' },
                        }}
                    >
                        {assistOpen ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                    </IconButton>
                </Box> */}
            </Box>
        </Box>
    );
}
