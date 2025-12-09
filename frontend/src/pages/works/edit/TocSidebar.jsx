import React, { useEffect, useState } from 'react';
import { Box, List, ListItemButton, ListItemText, Typography, Chip, Alert, CircularProgress } from '@mui/material';
import { getToc } from '../../../utils/api';
import { useProjectStore } from '../../../store/useProjectStore';
import { useTocStore } from '../../../store/useTocStore';

/**
 * 2025-11-17: 동적 목차(TOC) 사이드바
 * FastAPI의 result.json에서 분석된 목차를 표시
 * 목차 클릭 시 해당 섹션으로 스크롤
 */
export default function TocSidebar() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Store에서 상태 가져오기
    const sections = useTocStore((s) => s.sections);
    const setSections = useTocStore((s) => s.setSections);
    const activeSection = useTocStore((s) => s.activeSection);
    const scrollToSection = useTocStore((s) => s.scrollToSection);
    const tocMetadata = useTocStore((s) => s.tocMetadata);
    const setTocMetadata = useTocStore((s) => s.setTocMetadata);

    /**
     * 2025-11-23 수정: 프로젝트 ID 가져오기
     * useProjectStore의 'project' 필드를 사용하여 현재 프로젝트 정보 조회
     * 주의: 'currentProject' 필드는 존재하지 않으므로 'project'를 사용해야 함
     * 
     * @see useProjectStore.js - store 구조 확인
     * @see AnalyzeView.jsx, Upload.jsx - 동일한 패턴 사용
     */
    const project = useProjectStore((s) => s.project);
    const projectIdx = project?.projectIdx; // 프로젝트가 없으면 undefined (기본값 제거)

    /**
     * 프로젝트별 목차 데이터 로드
     * - projectIdx가 변경될 때마다 백엔드 API(/api/analysis/toc)를 호출하여 목차 조회
     * - Oracle DB에서 해당 프로젝트의 table_of_contents 데이터를 가져옴
     * - 성공 시 sections와 메타데이터를 store에 저장
     * 
     * 주의: projectIdx가 없으면 목차를 로드하지 않음 (기본값 1 사용 안 함)
     */
    useEffect(() => {
        // 프로젝트 ID가 없으면 목차를 로드하지 않음
        if (!projectIdx) {
            console.log('⚠️ 프로젝트 ID가 없어 목차를 로드하지 않습니다.');
            setSections([]);
            setLoading(false);
            return;
        }

        const loadToc = async () => {
            try {
                setLoading(true);
                setError(null);
                
                console.log('📚 목차 데이터 로딩 시작... projectIdx:', projectIdx);
                console.log('📋 현재 프로젝트 정보:', project);
                const response = await getToc(projectIdx);
                
                if (response.status === 'success' && response.data) {
                    const { sections: sectionData, source_file, source, total_sections } = response.data;
                    setSections(sectionData || []);
                    setTocMetadata({
                        sourceFile: source_file || source || '분석 결과',
                        totalSections: total_sections || sectionData?.length || 0,
                    });
                    console.log('✅ 목차 로드 완료: projectIdx=' + projectIdx + ', 섹션 수=' + (sectionData?.length || 0));
                } else {
                    throw new Error(response.message || '목차 데이터를 불러올 수 없습니다.');
                }
            } catch (err) {
                console.error('❌ 목차 로드 실패:', err);
                setError(err.message || '목차를 불러오는 중 오류가 발생했습니다.');
                setSections([]);
            } finally {
                setLoading(false);
            }
        };

        loadToc();
    }, [projectIdx, project, setSections, setTocMetadata]);

    // 목차 항목 클릭 핸들러
    const handleSectionClick = (section) => {
        console.log('🔍 섹션 선택:', section.number, section.title);
        scrollToSection(section.number, section.title);
    };

    // 들여쓰기 레벨 계산 (number 필드 기반)
    const getIndentLevel = (sectionNumber) => {
        if (!sectionNumber) return 0;
        const parts = String(sectionNumber).split('.');
        return Math.min(parts.length - 1, 3); // 최대 3단계
    };

    if (loading) {
        return (
            <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#f8fafc' }}>
                <CircularProgress size={24} />
            </Box>
        );
    }

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#f8fafc' }}>
            {/* 헤더 */}
            <Box sx={{ px: 2, py: 2, borderBottom: '1px solid #e5e7eb' }}>
                <Typography variant="subtitle2" fontWeight={600} color="text.primary">
                    📋 제안서 목차
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    분석된 양식 구조를 기반으로 생성되었습니다.
                </Typography>
                {tocMetadata.sourceFile && (
                    <Box sx={{ mt: 1 }}>
                        <Chip 
                            label={tocMetadata.sourceFile} 
                            size="small" 
                            sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                    </Box>
                )}
            </Box>

            {/* 에러 표시 */}
            {error && (
                <Box sx={{ px: 2, py: 2 }}>
                    <Alert severity="warning" sx={{ fontSize: '0.85rem' }}>
                        {error}
                    </Alert>
                </Box>
            )}

            {/* 목차 리스트 */}
            <Box sx={{ flex: 1, overflow: 'auto' }}>
                {sections.length === 0 ? (
                    <Box sx={{ px: 2, py: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                            아직 분석된 목차가 없습니다. 분석을 먼저 실행해주세요.
                        </Typography>
                    </Box>
                ) : (
                    <List dense disablePadding>
                        {sections.map((section, index) => {
                            const indentLevel = getIndentLevel(section.number);
                            const isActive = activeSection === section.number;
                            
                            return (
                                <ListItemButton
                                    key={`${section.number}-${index}`}
                                    selected={isActive}
                                    onClick={() => handleSectionClick(section)}
                                    sx={{
                                        pl: 2 + indentLevel * 1.5,
                                        py: 0.75,
                                        borderLeft: isActive ? '3px solid #0284c7' : '3px solid transparent',
                                        '&.Mui-selected': {
                                            bgcolor: 'rgba(2,132,199,0.08)',
                                            '&:hover': { bgcolor: 'rgba(2,132,199,0.12)' },
                                        },
                                        '&:hover': {
                                            bgcolor: 'rgba(0,0,0,0.04)',
                                        },
                                    }}
                                >
                                    <ListItemText
                                        primary={
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Typography
                                                    variant="body2"
                                                    fontWeight={indentLevel === 0 ? 600 : 400}
                                                    sx={{
                                                        fontSize: indentLevel === 0 ? '0.9rem' : '0.85rem',
                                                        color: isActive ? '#0284c7' : 'text.primary',
                                                    }}
                                                >
                                                    {section.number ? `${section.number}. ` : ''}
                                                    {section.title}
                                                </Typography>
                                                {section.required && (
                                                    <Chip 
                                                        label="필수" 
                                                        size="small" 
                                                        sx={{ 
                                                            height: 16, 
                                                            fontSize: '0.65rem',
                                                            bgcolor: '#fef2f2',
                                                            color: '#dc2626',
                                                        }} 
                                                    />
                                                )}
                                            </Box>
                                        }
                                        secondary={
                                            section.description && indentLevel === 0 ? (
                                                <Typography
                                                    variant="caption"
                                                    sx={{
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: 2,
                                                        WebkitBoxOrient: 'vertical',
                                                        overflow: 'hidden',
                                                        fontSize: '0.75rem',
                                                        color: 'text.secondary',
                                                        mt: 0.5,
                                                    }}
                                                >
                                                    {section.description}
                                                </Typography>
                                            ) : null
                                        }
                                        primaryTypographyProps={{
                                            sx: { 
                                                whiteSpace: 'normal',
                                                wordBreak: 'keep-all',
                                            },
                                        }}
                                    />
                                </ListItemButton>
                            );
                        })}
                    </List>
                )}
            </Box>

            {/* 푸터 정보 */}
            {sections.length > 0 && (
                <Box sx={{ px: 2, py: 1.5, borderTop: '1px solid #e5e7eb', bgcolor: '#ffffff' }}>
                    <Typography variant="caption" color="text.secondary">
                        총 {tocMetadata.totalSections || sections.length}개 섹션
                    </Typography>
                </Box>
            )}
        </Box>
    );
}

