import React from 'react';
import { Box, Tooltip, IconButton, Typography } from '@mui/material';
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined'; // 분석
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined'; // 생성
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined'; // 검증
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined';

const ITEMS = [
    { key: 'home', label: '홈', Icon: HomeOutlinedIcon },
    { key: 'analyze', label: '분석', Icon: InsightsOutlinedIcon },
    { key: 'create', label: '생성', Icon: EditNoteOutlinedIcon },
    { key: 'edit', label: '편집', Icon: EditOutlinedIcon },
    { key: 'verify', label: '검증', Icon: FactCheckOutlinedIcon },
];

export default function LeftNav({ width = 64 }) {
    const nav = useNavigate();
    const { pathname } = useLocation();
    const { docId } = useParams(); // 편집 모드에서만 의미 있음

    // key -> 목적지 경로
    const toPath = (key) => {
        if (key === 'edit') return `/works/edit${docId ? `/${docId}` : ''}`;
        return `/works/${key}`;
    };
    // key -> 선택 여부
    const isSelected = (key) => pathname.startsWith(`/works/${key}`);

    return (
        <Box
            component="nav"
            sx={{
                width,
                minWidth: width,
                borderRight: '1px solid #e5e7eb',
                bgcolor: '#fff',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                py: 1.5,
                gap: 0.5,
            }}
        >
            {ITEMS.map(({ key, label, path, Icon }) => {
                const selected = pathname.startsWith(path);
                return (
                    <Tooltip key={key} title={label} placement="right">
                        <Box
                            onClick={() => nav(toPath(key))}
                            sx={{
                                width: '100%',
                                display: 'grid',
                                placeItems: 'center',
                                py: 1,
                                cursor: 'pointer',
                                bgcolor: selected ? 'rgba(99,102,241,0.08)' : 'transparent',
                                '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' },
                                transition: 'background-color .15s',
                            }}
                        >
                            <IconButton size="small" color={selected ? 'primary' : 'default'}>
                                <Icon />
                            </IconButton>
                            <Typography
                                variant="caption"
                                sx={{
                                    mt: 0.5,
                                    fontWeight: 600,
                                    color: selected ? 'primary.main' : 'text.secondary',
                                    lineHeight: 1.1,
                                }}
                            >
                                {label}
                            </Typography>
                        </Box>
                    </Tooltip>
                );
            })}
        </Box>
    );
}
