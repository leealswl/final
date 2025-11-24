import React, { useEffect, useState } from 'react';
import { useFileStore } from '../../../store/useFileStore';
import { useDocumentStore } from '../../../store/useDocumentStore';
import { useTocStore } from '../../../store/useTocStore';
import { useParams } from 'react-router';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Box, Divider, Typography } from '@mui/material';
import ChatBotMUI from './ChatBotMUI';
import TiptapEditor from '../../../components/TiptapEditor';
import Editor from './Editor';

/**
 * 2025-11-17 수정:
 * EditView는 이제 2분할 레이아웃만 관리
 * 좌측 목차는 Layout.jsx에서 관리하도록 변경
 * - 좌측: AI Chatbot
 * - 우측: TipTap Editor (항상 표시)
 */
export default function EditView() {
    const { docId } = useParams();
    const getById = useFileStore((s) => s.getById);
    const setSelectedFile = useFileStore((s) => s.setSelectedFile);
    
    const { setDocumentId, content: docContent, setContent: setDocumentContent } = useDocumentStore();
    const setEditorInstance = useTocStore((s) => s.setEditorInstance);
    
    const [initialContent, setInitialContent] = useState('<p>제안서 작성을 시작하세요...</p>');

    // URL의 docId → 전역 선택(단방향 동기화)
    useEffect(() => {
        if (!docId) return;
        const f = getById(docId);
        if (f) {
            setSelectedFile(f);
            setDocumentId(f.id);
        }
    }, [docId, getById, setSelectedFile, setDocumentId]);

    // 문서 ID 변경 시 초기 컨텐츠 설정
    useEffect(() => {
        if (docContent) {
            setInitialContent(docContent);
        } else {
            setInitialContent('<p>제안서 작성을 시작하세요...</p>');
        }
    }, [docContent]);

    return (
        <Box display="flex" flex={1} height="100vh">
            <PanelGroup direction="horizontal" style={{ display: 'flex', width: '100%' }}>
                {/* 좌측: AI Chatbot Panel */}
                <Panel defaultSize={50} minSize={30}>
                    <Box height="100%" bgcolor="grey.100" p={1} overflow="auto">
                        <ChatBotMUI />
                    </Box>
                </Panel>

                {/* Resizer Handle */}
                <PanelResizeHandle>
                    <Divider
                        orientation="vertical"
                        sx={{
                            cursor: 'col-resize',
                            bgcolor: 'grey.300',
                            '&:hover': { bgcolor: 'primary.main' },
                            width: 4,
                        }}
                    />
                </PanelResizeHandle>

                {/* 우측: TipTap Editor Panel */}
                <Panel defaultSize={50} minSize={30}>
                    <Box display="flex" flexDirection="column" height="100%" bgcolor="white">
                        <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                            {/* <TiptapEditor 
                                initialContent={initialContent} 
                                contentKey={docId || 'default'} 
                                onContentChange={setDocumentContent} 
                                readOnly={false}
                                registerEditor={setEditorInstance}
                            /> */}
                            <Editor />
                        </Box>
                        <Box sx={{ px: 2, py: 1, borderTop: '1px solid #e5e7eb', bgcolor: '#fafafa' }}>
                            <Typography variant="caption" color="text.secondary">
                                📋 좌측 목차를 클릭하면 해당 섹션으로 이동합니다. Heading 레벨, 목록, 표 삽입이 지원됩니다.
                            </Typography>
                        </Box>
                    </Box>
                </Panel>
            </PanelGroup>
        </Box>
    );
}
