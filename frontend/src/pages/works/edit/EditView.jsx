import React, { useEffect, useState } from 'react';
import { useFileStore } from '../../../store/useFileStore';
//import { useDocumentStore } from '../../../store/useDocumentStore';
import { useTocStore } from '../../../store/useTocStore';
import { useParams } from 'react-router';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Box, Divider, Typography } from '@mui/material';
import ChatBotMUI from './ChatBotMUI';
import TiptapEditor from '../../../components/TiptapEditor';
import Editor from './Editor';
import { useDocumentStore } from '../../../store/useDocumentStore';

/**
 * 2025-11-17 수정:
 * EditView는 이제 2분할 레이아웃만 관리
 * 좌측 목차는 Layout.jsx에서 관리하도록 변경
 * - 중앙: TipTap Editor (항상 표시)
 * - 우측: AI Chatbot
 */

const toAbs = (p) => (p?.startsWith('http') ? p : `http://localhost:8081${p}`);

export default function EditView() {
    const params = useParams();
    const docId = params.docId ?? null;
    const isExistingDoc = !!docId;
    const { reloadTrigger, filePath } = useFileStore();

    //const { docId } = useParams();
    const getById = useFileStore((s) => s.getById);
    const setSelectedFile = useFileStore((s) => s.setSelectedFile);
    const currentProjectIdx = useFileStore((s) => s.currentProjectId);

    //const { setDocumentId, content: docContent, setContent: setDocumentContent } = useDocumentStore();
    const {
        content: docContent, // TipTap 내용(JSON)
        setContent: setDocumentContent, // onContentChange에서 호출
        setMeta,
        projectIdx,
        documentIdx, // projectIdx, documentIdx, fileName 설정
    } = useDocumentStore();

    const setEditorInstance = useTocStore((s) => s.setEditorInstance);
    const [initialContent, setInitialContent] = useState();

    console.log('[EditView] useParams:', params);
    console.log('[EditView] docId:', docId);
    console.log('[EditView] docSaveStore 상태:', { projectIdx, documentIdx });

    // URL의 docId → 전역 선택(단방향 동기화)
    useEffect(() => {
        const tmpProjectIdx = currentProjectIdx ?? 1;
        console.log('tmpProjectIdx: ', tmpProjectIdx);
        // 🔹 1) docId 없는 경우: 새 문서 모드
        if (!isExistingDoc) {
            console.log('[EditView] 새 문서 모드(/edit) – docId 없음');

            setMeta({
                projectIdx: tmpProjectIdx,
                documentIdx: null, // 아직 문서 row 없음
                fileName: '제안서_초안',
                filePath: filePath ?? '/uploads/admin/1/1/234.json',
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
                projectIdx: f.projectIdx ?? f.project_idx ?? f.projectId ?? f.project_id ?? currentProjectIdx ?? 1,
                documentIdx: f.documentIdx ?? f.document_idx ?? f.id ?? docId ?? 1,
                fileName: f.fileName ?? f.name ?? f.label ?? '제안서_초안',
                filePath: filePath ?? '/uploads/admin/1/1/234.json',
            });
        } else {
            console.warn('[EditView] getById로 파일을 찾지 못했습니다.', { docId });
            setMeta({
                projectIdx: currentProjectIdx ?? 1,
                documentIdx: docId, // 일단 라우트에서 온 값 넣어둠
                fileName: '제안서_초안',
                filePath: filePath ?? '/uploads/admin/1/1/234.json',
            });
        }
    }, [isExistingDoc, docId, getById, setSelectedFile, setMeta, currentProjectIdx, filePath]);

    useEffect(() => {
        fetch(toAbs('/uploads/admin/1/1/234.json'))
            .then(async (res) => {
                if (!res.ok) throw new Error(res.statusText || 'JSON 파일을 불러오지 못했습니다.');
                const jsonData = await res.json(); // JSON 파싱
                console.log('jsondata: ', jsonData);
                // 이미 언마운트된 경우 무시
                setInitialContent(jsonData);
                setDocumentContent(jsonData, false);
            })
            .catch((error) => {
                console.warn('[Editor] JSON 로드 실패', error);
                // 에러 발생 시 빈 문서로 시작
                const emptyDoc = { type: 'doc', content: [] };
                setInitialContent(emptyDoc);
                setDocumentContent(emptyDoc);
            });
        // cleanup 함수: 컴포넌트 언마운트 시 중단
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [reloadTrigger, setDocumentContent]);

    return (
        <Box display="flex" flex={1} height="100vh">
            <PanelGroup direction="horizontal" style={{ display: 'flex', width: '100%' }}>
                {/* 중앙: TipTap Editor Panel */}
                <Panel defaultSize={70} minSize={40}>
                    <Box display="flex" flexDirection="column" height="100%" bgcolor="white">
                        <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                            <TiptapEditor initialContent={initialContent} contentKey={docId || 'default'} onContentChange={setDocumentContent} readOnly={false} registerEditor={setEditorInstance} />
                            {/* <Editor /> */}
                        </Box>
                        <Box sx={{ px: 2, py: 1, borderTop: '1px solid #e5e7eb', bgcolor: '#fafafa' }}>
                            <Typography variant="caption" color="text.secondary">
                                📋 좌측 목차를 클릭하면 해당 섹션으로 이동합니다. Heading 레벨, 목록, 표 삽입이 지원됩니다.
                            </Typography>
                        </Box>
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

                {/* 우측: AI Chatbot Panel */}
                <Panel defaultSize={30} minSize={20}>
                    <Box height="100%" bgcolor="grey.100" p={1} overflow="auto">
                        <ChatBotMUI />
                    </Box>
                </Panel>
            </PanelGroup>
        </Box>
    );
}
