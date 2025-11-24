import React, { useEffect, useState } from 'react';
import { useFileStore } from '../../../store/useFileStore';
//import { useDocumentStore } from '../../../store/useDocumentStore';
import { useTocStore } from '../../../store/useTocStore';
import { useParams } from 'react-router';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Box, Divider, Typography } from '@mui/material';
import ChatBotMUI from './ChatBotMUI';
import TiptapEditor from '../../../components/TiptapEditor';
import { useDocumentSaveStore } from '../../../store/useDocumentSaveStore';

/**
 * 2025-11-17 수정:
 * EditView는 이제 2분할 레이아웃만 관리
 * 좌측 목차는 Layout.jsx에서 관리하도록 변경
 * - 좌측: AI Chatbot
 * - 우측: TipTap Editor (항상 표시)
 */
export default function EditView() {
    const params = useParams();
    const docId = params.docId ?? null; 
    const isExistingDoc = !!docId;

    //const { docId } = useParams();
    const getById = useFileStore((s) => s.getById);
    const setSelectedFile = useFileStore((s) => s.setSelectedFile);
    const currentProjectIdx = useFileStore((s) => s.currentProjectId);
    
    //const { setDocumentId, content: docContent, setContent: setDocumentContent } = useDocumentStore();
    const {
    content: docContent,          // TipTap 내용(JSON)
    setContent: setDocumentContent, // onContentChange에서 호출
    setMeta,
    projectIdx,
    documentIdx,                    // projectIdx, documentIdx, fileName 설정
    } = useDocumentSaveStore();

    const setEditorInstance = useTocStore((s) => s.setEditorInstance);
    const [initialContent, setInitialContent] = useState();

    console.log('[EditView] useParams:', params);
    console.log('[EditView] docId:', docId);
    console.log('[EditView] docSaveStore 상태:', { projectIdx, documentIdx });

    // URL의 docId → 전역 선택(단방향 동기화)
    useEffect(() => {
        const tmpProjectIdx = currentProjectIdx ?? 1;
    // 🔹 1) docId 없는 경우: 새 문서 모드
    if (!isExistingDoc) {
        console.log('[EditView] 새 문서 모드(/edit) – docId 없음');

        setMeta({
            projectIdx: tmpProjectIdx,
            documentIdx: null, // 아직 문서 row 없음
            fileName: '제안서_초안',
        });

        // 새 문서일 땐 굳이 파일 트리에서 찾을 게 없으니 바로 리턴
        return;
        }

        // 🔹 2) docId 있는 경우: 기존 문서 모드
        const f = getById(docId);
        console.log('[EditView] 기존 문서 모드(/edit/:docId) – f:', f);

        if (f) {
        setSelectedFile(f);

        setMeta({
            projectIdx:
            f.projectIdx ??
            f.project_idx ??
            f.projectId ??
            f.project_id ??
            currentProjectIdx ??
            null,
            documentIdx:
            f.documentIdx ??
            f.document_idx ??
            f.id ??
            docId,
            fileName: f.fileName ?? f.name ?? f.label ?? '제안서_초안',
        });
        } else {
        console.warn('[EditView] getById로 파일을 찾지 못했습니다.', { docId });
        setMeta({
            projectIdx: currentProjectIdx ?? null,
            documentIdx: docId, // 일단 라우트에서 온 값 넣어둠
            fileName: '제안서_초안',
        });
        }
    }, [isExistingDoc, docId, getById, setSelectedFile, setMeta, currentProjectIdx]);

    useEffect(() => {
  if (docContent) {
    // 1) 이미 JSON 객체인 경우 (Tiptap에서 직접 온 경우)
    if (typeof docContent === 'object') {
      setInitialContent(docContent);
      return;
    }

    // 2) 문자열인 경우 (DB에서 읽어온 JSON 문자열 or HTML)
    if (typeof docContent === 'string') {
        try {
            const parsed = JSON.parse(docContent);   // JSON 문자열이면 여기서 객체 됨
            setInitialContent(parsed);
        } catch (e) {
            console.error(
            '[EditView] 문서 content JSON 파싱 실패, 문자열 그대로 사용 (HTML일 수 있음)',
            e,
            );
            // 만약 예전에 HTML을 저장한 적이 있다면, 그냥 HTML로 Tiptap에 넘겨도 됨
            setInitialContent(docContent);
        }
        return;
        }

        // 혹시 다른 타입이면 기본값
        console.warn('[EditView] 예상치 못한 docContent 타입:', typeof docContent);
        setInitialContent({
        type: 'doc',
        content: [
            {
            type: 'paragraph',
            attrs: { textAlign: null },
            content: [{ type: 'text', text: '제안서 작성을 시작하세요...' }],
            },
        ],
        });
    } else {
        // docContent가 비어있는 경우 = 새 문서
        setInitialContent({
        type: 'doc',
        content: [
            {
            type: 'paragraph',
            attrs: { textAlign: null },
            content: [{ type: 'text', text: '제안서 작성을 시작하세요...' }],
            },
        ],
        });
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
                            <TiptapEditor 
                                initialContent={initialContent} 
                                contentKey={docId || 'default'} 
                                onContentChange={setDocumentContent} 
                                readOnly={false}
                                registerEditor={setEditorInstance}
                            />
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
