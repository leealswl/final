import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import { Plus } from 'lucide-react';

export function NewDocumentCard() {
    const works = () => {
        window.location.href = 'works';
    };
    return (
        <Box
            onClick={works}
            sx={{
                p: 3,
                border: 1,
                borderStyle: 'dashed',
                borderColor: '#dadce0',
                borderRadius: 3,
                bgcolor: 'white',
                minHeight: 200,
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.3s',
                '&:hover': {
                    borderColor: '#1a73e8',
                    bgcolor: '#f7f9fa',
                },
            }}
        >
            <Box
                sx={{
                    mb: 2,
                    p: 2,
                    borderRadius: '50%',
                    bgcolor: '#f7f9fa',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'background-color 0.3s',
                    '&:hover': { bgcolor: '#e8f0fe' },
                }}
            >
                <Plus size={24} style={{ color: '#5f6368' }} />
            </Box>
            <Typography variant="body2" sx={{ color: '#5f6368' }}>
                새 문서 생성
            </Typography>
        </Box>
    );
}
