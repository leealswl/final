// src/components/figma/ImageWithFallback.jsx
import React, { useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

export function ImageWithFallback({ src, alt, fallback }) {
    const [error, setError] = useState(false);
    const [loading, setLoading] = useState(true);

    if (error) {
        return (
            <Box
                sx={{
                    width: '100%',
                    height: '100%',
                    bgcolor: 'var(--nb-card-bg, #f5f5f5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                {fallback || (
                    <Typography variant="body2" color="var(--nb-text-secondary, #777)" sx={{ textAlign: 'center', p: 1 }}>
                        이미지를 불러올 수 없습니다
                    </Typography>
                )}
            </Box>
        );
    }

    return (
        <Box
            sx={{
                position: 'relative',
                width: '100%',
                height: '100%',
                bgcolor: 'var(--nb-card-bg, #f5f5f5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}
        >
            {/* 로딩 스피너 */}
            {loading && (
                <CircularProgress
                    size={40}
                    sx={{
                        color: 'var(--nb-primary, #1976d2)',
                        position: 'absolute',
                    }}
                />
            )}

            {/* 이미지 */}
            <Box
                component="img"
                src={src}
                alt={alt}
                onError={() => setError(true)}
                onLoad={() => setLoading(false)}
                sx={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    display: loading ? 'none' : 'block',
                    transition: 'opacity 0.3s ease',
                    borderRadius: 0,
                }}
            />
        </Box>
    );
}
