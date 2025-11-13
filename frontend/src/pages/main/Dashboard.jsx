import React, { useEffect, useState } from 'react';
import { Grid, Box, Typography, Button } from '@mui/material';
import { DashboardHeader } from './components/DashboardHeader';
import { DocumentCard } from './components/DocumentCard';
import { NewDocumentCard } from './components/NewDocumentCard';
import { HelpSection } from './components/HelpSection';
import { FileText, Microscope } from 'lucide-react';
import api from '../../utils/api';
import { useAuthStore } from '../../store/useAuthStore';

function Dashboard() {
    const [visibleCount, setVisibleCount] = useState(3); // 처음 4개만 보여줌
    const handleShowMore = () => {
        setVisibleCount((prev) => prev + 4); // 4개씩 더 보기
        // setVisibleCount((prev) => recentDocuments.length); // 전체 보기
    };
    const user = useAuthStore((state) => state.user);

    useEffect(() => {
        const getProjects = async () => {
            try {
                const res = await api.get(`/api/project/list/${user.idx}`);
                console.log(res.data);
            } catch (err) {
                console.error(err);
            }
        };

        if (user?.idx) {
            getProjects();
        }
    }, [user]);

    const recentDocuments = [
        {
            title: 'mRNA 백신 효능 분석',
            description: '3상 임상 시험 결과 요약',
            lastEdited: '5시간 전',
            icon: <FileText style={{ color: '#1a73e8' }} />,
        },
        {
            title: '재생 에너지 타당성 연구',
            description: '태양광 발전 효율성 데이터',
            lastEdited: '1일 전',
            icon: <FileText style={{ color: '#1a73e8' }} />,
        },
        {
            title: '나노입자 합성 프로토콜',
            description: '금 나노입자 제조 및 특성 분석',
            lastEdited: '2일 전',
            icon: <Microscope style={{ color: '#1a73e8' }} />,
        },
        {
            title: '나노입자 합성 프로토콜',
            description: '금 나노입자 제조 및 특성 분석',
            lastEdited: '2일 전',
            icon: <Microscope style={{ color: '#1a73e8' }} />,
        },
        {
            title: '나노입자 합성 프로토콜',
            description: '금 나노입자 제조 및 특성 분석',
            lastEdited: '2일 전',
            icon: <Microscope style={{ color: '#1a73e8' }} />,
        },
        {
            title: '나노입자 합성 프로토콜',
            description: '금 나노입자 제조 및 특성 분석',
            lastEdited: '2일 전',
            icon: <Microscope style={{ color: '#1a73e8' }} />,
        },
        {
            title: '나노입자 합성 프로토콜',
            description: '금 나노입자 제조 및 특성 분석',
            lastEdited: '2일 전',
            icon: <Microscope style={{ color: '#1a73e8' }} />,
        },
        {
            title: '나노입자 합성 프로토콜',
            description: '금 나노입자 제조 및 특성 분석',
            lastEdited: '2일 전',
            icon: <Microscope style={{ color: '#1a73e8' }} />,
        },
    ];

    return (
        <Box
            sx={{
                minHeight: '100vh',
                bgcolor: 'white',
            }}
        >
            <DashboardHeader />

            <Box component="main" sx={{ maxWidth: 1400, mx: 'auto', px: 3, py: 5 }}>
                {/* 최근 작업 문서 섹션 */}
                <Box mb={6}>
                    <Typography variant="h5" component="h2" mb={3} sx={{ color: '#202124' }}>
                        최근 작업 문서
                    </Typography>
                    <Grid container spacing={3}>
                        <Grid item size={3}>
                            <NewDocumentCard />
                        </Grid>
                        {recentDocuments.slice(0, visibleCount).map((doc, index) => (
                            <Grid item size={3} key={index}>
                                <DocumentCard {...doc} />
                            </Grid>
                        ))}
                    </Grid>

                    {visibleCount < recentDocuments.length && (
                        <Box textAlign="center" mt={3}>
                            <Button
                                variant="outlined"
                                onClick={handleShowMore}
                                sx={{
                                    borderRadius: 2,
                                    color: '#1a73e8',
                                    borderColor: '#1a73e8',
                                    '&:hover': {
                                        bgcolor: '#1a73e8',
                                        color: 'white',
                                    },
                                }}
                            >
                                더보기
                            </Button>
                        </Box>
                    )}
                </Box>

                {/* 도움말 섹션 */}
                <HelpSection />
            </Box>
        </Box>
    );
}

export default Dashboard;
