import React, { useEffect, useMemo, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useFileStore } from '../../../store/useFileStore';
import { useDocumentStore } from '../../../store/useDocumentStore';
import { useTocStore } from '../../../store/useTocStore';
import TiptapEditor from '../../../components/TiptapEditor';

/**
 * 상대 경로를 절대 URL로 변환
 * @param {string} p - 경로
 * @returns {string} - http로 시작하면 그대로, 아니면 localhost:8081을 앞에 붙임
 */
const toAbs = (p) => (p?.startsWith('http') ? p : `http://localhost:8081${p}`);

function Center({ children }) {
    return <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>{children}</Box>;
}

// function Pad({ children }) {
//     return <Box sx={{ p: 2, color: 'text.secondary' }}>{children}</Box>;
// }


/**
 * 파일 편집기 메인 컴포넌트
 * 선택된 파일의 종류에 따라 적절한 뷰어/에디터를 보여줌
 */
export default function Editor() {
    // 파일 스토어에서 선택된 파일 가져오기
    const { reloadTrigger, filePath } = useFileStore();

    // 문서 스토어에서 문서 관련 상태 및 함수 가져오기
    const { setDocumentId, content: docContent, setContent: setDocumentContent } = useDocumentStore();
    const setEditorInstance = useTocStore((s) => s.setEditorInstance);

    // 에디터 초기 콘텐츠 상태
    const [initialContent, setInitialContent] = useState('<p></p>');
    // 로딩 상태
    const [loading, setLoading] = useState(false);
    // 로드 에러 메시지
    const [loadError, setLoadError] = useState(null);

    useEffect(() => {
        
        // 일반 텍스트 파일인 경우: 텍스트를 HTML로 변환해서 로드
        let cancelled = false; // 컴포넌트 언마운트 시 중단 플래그
        setLoading(true);
        setLoadError(null);

        // fetch(toAbs(filePath))
        //     .then(async (res) => {
        //         if (!res.ok) throw new Error(res.statusText || '파일을 불러오지 못했습니다.');
        //         const txt = await res.text(); // 텍스트로 읽기
        //         // 이미 언마운트된 경우 무시
        //         if (!cancelled) {
        //             const html = textToHtml(txt); // 텍스트를 HTML로 변환
        //             setInitialContent(html);
        //             setDocumentContent(html);
        //         }
        //     })
        //     .catch((error) => {
        //         console.warn('[Editor] 콘텐츠 로드 실패', error);
        //         if (!cancelled) {
        //             // 에러 발생 시 빈 문서로 시작
        //             const emptyHtml = '<p></p>';
        //             setInitialContent(emptyHtml);
        //             setDocumentContent(emptyHtml);
        //             setLoadError('파일 내용을 불러오지 못했습니다. 빈 문서로 시작합니다.');
        //         }
        //     })
        //     .finally(() => {
        //         if (!cancelled) setLoading(false);
        //     });

        // // cleanup 함수: 컴포넌트 언마운트 시 중단
        // return () => {
        //     cancelled = true;
        // };

        const url = `${toAbs(filePath)}?t=${Date.now()}`;

        fetch(url)
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
                if (!cancelled) {
                    // 에러 발생 시 빈 문서로 시작
                    const emptyDoc = { type: 'doc', content: [] };
                    setInitialContent(emptyDoc);
                    setDocumentContent(emptyDoc);
                    setLoadError('JSON 파일 로드를 실패했습니다. 빈 문서로 시작합니다.');
                }
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        // cleanup 함수: 컴포넌트 언마운트 시 중단
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [setDocumentId, setDocumentContent, reloadTrigger, filePath]);

    // 지원하는 파일 형식인 경우: TiptapEditor 표시
    return (
        <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* 로딩 중일 때 스피너 표시 */}
            {loading && (
                <Center>
                    <CircularProgress size={24} />
                </Center>
            )}
            {/* 로드 에러가 있을 때 경고 메시지 표시 */}
            {!loading && loadError && <Box sx={{ px: 2, py: 1, bgcolor: '#fff4e5', color: '#8a6d3b', borderBottom: '1px solid #f0deb4' }}>{loadError}</Box>}
            {/* Tiptap 에디터 영역 */}
            <Box sx={{ flex: 1, minHeight: 0 }}>
                {/* <TiptapEditor initialContent={initialContent} contentKey={file.id} onContentChange={setDocumentContent} readOnly={false} registerEditor={setEditorInstance} /> */}
                <TiptapEditor initialContent={initialContent} onContentChange={setDocumentContent} contentKey={'default'} readOnly={false} registerEditor={setEditorInstance} />
            </Box>
            {/* 하단 안내 메시지 */}
            <Box sx={{ px: 2, py: 1, borderTop: '1px solid #e5e7eb', bgcolor: '#fafafa' }}>
                <Typography variant="caption" color="text.secondary">
                    📋 좌측 목차를 클릭하면 해당 섹션으로 이동합니다. Heading 레벨, 목록, 표 삽입이 지원됩니다.
                </Typography>
            </Box>
        </Box>
    );
}
