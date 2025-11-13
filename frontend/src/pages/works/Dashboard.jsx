import React, { useEffect, useState } from 'react';
import { Grid, Box, Typography, Button } from '@mui/material';
import { DashboardHeader } from './DashboardHeader';
import { DocumentCard } from './DocumentCard';
import { NewDocumentCard } from './NewDocumentCard';
import { HelpSection } from './HelpSection';
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
        const projects = async () => {
            try {
                const res = await api.get(`/api/project/list/${user.idx}`);
                console.log(res.data);
            } catch (err) {
                console.error(err);
            }
        };

        if (user?.idx) {
            projects();
        }
    }, [user]);
    // const recommendedProposals = [
    //     {
    //         title: '신약 개발 프로젝트 제안서',
    //         description: 'AI 기반 분자 설계 및 임상 시험 계획',
    //         lastEdited: '2시간 전',
    //         image: 'https://images.unsplash.com/photo-1618053238059-cc7761222f2a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsYWJvcmF0b3J5JTIwc2NpZW5jZSUyMHJlc2VhcmNofGVufDF8fHx8MTc2MjcwODA4Nnww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    //     },
    //     {
    //         title: '기후 변화 연구 보고서',
    //         description: '2025년 탄소 배출 데이터 분석 및 예측 모델',
    //         lastEdited: '어제',
    //         image: 'https://images.unsplash.com/photo-1704793027965-da6e888e89fd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjbGltYXRlJTIwZW52aXJvbm1lbnQlMjBkYXRhfGVufDF8fHx8MTc2Mjc2MTQ1Nnww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    //     },
    //     {
    //         title: '양자 컴퓨팅 연구 계획',
    //         description: '큐비트 안정성 개선을 위한 실험 설계',
    //         lastEdited: '3일 전',
    //         image: 'https://images.unsplash.com/photo-1752451399416-faef5f9fe572?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxxdWFudHVtJTIwY29tcHV0aW5nJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjI2ODA2MjB8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    //     },
    //     {
    //         title: '유전자 치료 연구',
    //         description: 'CRISPR 기술을 활용한 유전자 편집 프로토콜',
    //         lastEdited: '5일 전',
    //         image: 'https://images.unsplash.com/photo-1531956656798-56686eeef3d4?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkbmElMjBnZW5ldGljcyUyMGJpb2xvZ3l8ZW58MXx8fHwxNzYyNzYxNDU3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    //     },
    // ];

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
                {/* 추천 제안서 섹션 */}
                {/* <Box mb={8}>
                    <Typography variant="h5" component="h2" mb={3} sx={{ color: '#202124' }}>
                        추천 제안서
                    </Typography>
                    <Grid container spacing={3}>
                        {recommendedProposals.map((doc, index) => (
                            <Grid item xs={12} sm={6} md={3} key={index}>
                                <DocumentCard {...doc} />
                            </Grid>
                        ))}
                    </Grid>
                </Box> */}

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
