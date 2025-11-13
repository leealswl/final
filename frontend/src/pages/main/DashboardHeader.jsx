import React from 'react';
import { Box, Button, Typography, Stack, IconButton } from '@mui/material';
import { FileText, Grid3x3, List, ChevronDown } from 'lucide-react';

export function DashboardHeader() {
    const works = () => {
        window.location.href = 'works/analyze';
    };
    return (
        <Box
            component="header"
            sx={{
                position: 'sticky',
                top: 0,
                zIndex: 1100,
                px: 3,
                py: 2,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: 1,
                borderColor: '#dadce0',
                bgcolor: 'white',
            }}
        >
            {/* 왼쪽: 로고 + 네비게이션 */}
            <Stack direction="row" spacing={3} alignItems="center">
                <Stack direction="row" spacing={1} alignItems="center">
                    <FileText size={24} style={{ color: '#1a73e8' }} />
                    <Typography variant="h6" sx={{ color: '#202124' }}>
                        Paladoc
                    </Typography>
                </Stack>

                <Stack direction="row" spacing={1}>
                    <Button
                        // variant="contained"
                        sx={{
                            borderRadius: '999px',
                            bgcolor: '#f7f9fa',
                            color: '#202124',
                            textTransform: 'none',
                            // '&:hover': { bgcolor: '#f7f9fa' },
                        }}
                    >
                        홈
                    </Button>
                    <Button
                        variant="text"
                        sx={{
                            borderRadius: '999px',
                            color: '#5f6368',
                            textTransform: 'none',
                            '&:hover': { bgcolor: '#f7f9fa' },
                        }}
                    >
                        프로젝트
                    </Button>
                    {/* <Button
                        variant="text"
                        sx={{
                            borderRadius: '999px',
                            color: '#5f6368',
                            textTransform: 'none',
                            '&:hover': { bgcolor: '#f7f9fa' },
                        }}
                    >
                        팀
                    </Button> */}
                </Stack>
            </Stack>

            {/* 오른쪽: 새로 만들기 + 보기 전환 + 메뉴 */}
            <Stack direction="row" spacing={1} alignItems="center">
                <Button
                    variant="contained"
                    onClick={works}
                    sx={{
                        borderRadius: '999px',
                        textTransform: 'none',
                        '&:hover': { boxShadow: '0 2px 8px rgba(0,0,0,0.2)' },
                    }}
                >
                    + 새로 만들기
                </Button>

                <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{
                        px: 1,
                        py: 0.5,
                        border: 1,
                        borderColor: '#dadce0',
                        borderRadius: '12px',
                    }}
                >
                    <IconButton
                        size="small"
                        sx={{
                            '&:hover': { bgcolor: '#f7f9fa' },
                        }}
                    >
                        <Grid3x3 size={16} style={{ color: '#5f6368' }} />
                    </IconButton>
                    <IconButton
                        size="small"
                        sx={{
                            '&:hover': { bgcolor: '#f7f9fa' },
                        }}
                    >
                        <List size={16} style={{ color: '#5f6368' }} />
                    </IconButton>
                </Stack>

                <IconButton
                    size="small"
                    sx={{
                        borderRadius: '999px',
                        '&:hover': { bgcolor: '#f7f9fa' },
                    }}
                >
                    <ChevronDown size={20} style={{ color: '#5f6368' }} />
                </IconButton>
            </Stack>
        </Box>
    );
}
