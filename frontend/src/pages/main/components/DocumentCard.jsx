import React from 'react';
import { Card, CardContent, Box, IconButton, Typography, Paper } from '@mui/material';
import { FileText, Clock, MoreVertical } from 'lucide-react';


export function DocumentCard({ title, description, lastEdited, icon, image }) {
    return (
        <Card
            variant="outlined"
            sx={{
                borderRadius: 3,
                bgcolor: '#f7f9fa',
                borderColor: '#dadce0',
                cursor: 'pointer',
                overflow: 'hidden',
                transition: 'all 0.2s ease',
                '&:hover': {
                    bgcolor: '#ffffff',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
                },
            }}
        >

            <CardContent sx={{ p: 3, height: '198px' }}>
                {/* 아이콘 및 메뉴 버튼 영역 */}
                {!image && (
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                        <Paper
                            elevation={0}
                            sx={{
                                p: 1,
                                borderRadius: 2,
                                bgcolor: '#e8f0fe',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            {icon || <FileText size={20} style={{ color: '#1a73e8' }} />}
                        </Paper>

                        <IconButton
                            size="small"
                            sx={{
                                opacity: 0,
                                transition: 'opacity 0.2s ease',
                                '&:hover': { bgcolor: '#f7f9fa' },
                                '.MuiCard-root:hover &': { opacity: 1 },
                            }}
                        >
                            <MoreVertical size={18} style={{ color: '#5f6368' }} />
                        </IconButton>
                    </Box>
                )}

                {image && (
                    <Box display="flex" justifyContent="flex-end" mb={1}>
                        <IconButton
                            size="small"
                            sx={{
                                opacity: 0,
                                transition: 'opacity 0.2s ease',
                                '&:hover': { bgcolor: '#f7f9fa' },
                                '.MuiCard-root:hover &': { opacity: 1 },
                            }}
                        >
                            <MoreVertical size={18} style={{ color: '#5f6368' }} />
                        </IconButton>
                    </Box>
                )}

                {/* 제목 */}
                <Typography variant="subtitle1" fontWeight={600} color="#202124" gutterBottom>
                    {title}
                </Typography>

                {/* 설명 */}
                <Typography variant="body2" color="#5f6368" mb={2}>
                    {description}
                </Typography>

                {/* 수정 날짜 */}
                <Box display="flex" alignItems="center" gap={0.5} color="#5f6368">
                    <Clock size={14} />
                    <Typography variant="caption">{lastEdited}</Typography>
                </Box>
            </CardContent>
        </Card>
    );
}
