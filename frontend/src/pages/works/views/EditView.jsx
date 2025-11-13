import React, { useEffect } from 'react';
import { useFileStore } from '../../../store/useFileStore';
import Editor from '../Editor';
import { useParams } from 'react-router';
import { ChatBot } from '../Chatbot';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Box, Divider } from '@mui/material';
import ChatBotMUI from '../ChatBotMUI';

export default function EditView() {
    const { docId } = useParams(); // /works/edit/:docId
    const getById = useFileStore((s) => s.getById);
    const setSelectedFile = useFileStore((s) => s.setSelectedFile);

    // URL의 docId → 전역 선택(단방향 동기화)
    useEffect(() => {
        if (!docId) return;
        const f = getById(docId);
        if (f) setSelectedFile(f);
    }, [docId, getById, setSelectedFile]);

    return (
        <Box display="flex" flex={1} height="100vh">
            <PanelGroup direction="horizontal" style={{ display: 'flex', width: '100%' }}>
                {/* AI Chatbot Panel */}
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

                {/* Document Editor Panel */}
                {/* <Panel defaultSize={50} minSize={30}>
                    <Box height="100%" bgcolor="grey.50" p={1} overflow="auto">
                        <Editor />
                    </Box>
                </Panel> */}
                <Panel defaultSize={50} minSize={30}>
                    <Box display="flex" flexDirection="column" height="100%" bgcolor="grey.50" p={1}>
                        <Box flex={1} overflow="auto">
                            <Editor />
                        </Box>
                    </Box>
                </Panel>
            </PanelGroup>
        </Box>
    );
}
