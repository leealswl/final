import { BookOpen, Video, MessageCircleQuestion } from 'lucide-react';
import { useState } from 'react';
import { Box, Typography } from '@mui/material';

export function HelpSection() {
    const [isExpanded, setIsExpanded] = useState(false);

    const helpItems = [
        {
            icon: <BookOpen size={20} style={{ color: '#1a73e8' }} />,
            title: '시작 가이드',
            description: 'Palaodc의 기본 기능을 알아보세요',
        },
        {
            icon: <Video size={20} style={{ color: '#1a73e8' }} />,
            title: '비디오 튜토리얼',
            description: '단계별 동영상 가이드를 확인하세요',
        },
        {
            icon: <MessageCircleQuestion size={20} style={{ color: '#1a73e8' }} />,
            title: '자주 묻는 질문',
            description: '일반적인 질문에 대한 답변을 찾아보세요',
        },
    ];

    return (
        <Box
            mt={6}
            p={3}
            border={1}
            borderColor="var(--nb-border)"
            borderRadius="var(--card-radius)"
            bgcolor="var(--nb-card-bg)"
            sx={{
                maxHeight: isExpanded ? 400 : 150,
                opacity: isExpanded ? 1 : 0.5,
                overflow: 'hidden',
                transition: 'all 0.3s',
                '&:hover': {
                    opacity: 1,
                },
            }}
            onMouseEnter={() => setIsExpanded(true)}
            onMouseLeave={() => setIsExpanded(false)}
        >
            <Typography variant="h6" mb={2} sx={{ color: '#202124' }}>
                도움말 및 가이드
            </Typography>

            <Box display="flex" flexDirection="column" gap={1.5}>
                {helpItems.map((item, index) => (
                    <Box
                        key={index}
                        display="flex"
                        alignItems="flex-start"
                        gap={2}
                        p={2}
                        borderRadius={2}
                        sx={{
                            cursor: 'pointer',
                            transition: 'background-color 0.3s',
                            '&:hover': { bgcolor: 'var(--nb-background)' },
                        }}
                    >
                        {item.icon}
                        <Box>
                            <Typography variant="body2" mb={0.5} sx={{ color: '#202124' }}>
                                {item.title}
                            </Typography>
                            <Typography variant="caption" sx={{ color: '#5f6368' }}>
                                {item.description}
                            </Typography>
                        </Box>
                    </Box>
                ))}
            </Box>
        </Box>
    );
}
