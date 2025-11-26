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

/**
 * 중앙 정렬 컨테이너 컴포넌트
 */
function Center({ children }) {
    return <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>{children}</Box>;
}

/**
 * 패딩과 색상이 적용된 컨테이너 컴포넌트
 */
function Pad({ children }) {
    return <Box sx={{ p: 2, color: 'text.secondary' }}>{children}</Box>;
}

/**
 * 파일의 종류를 판별하는 함수
 * @param {Object} file - 파일 객체
 * @returns {string} - 'empty', 'folder', 'office', 'text', 'pdf', 'json', 'unknown' 중 하나
 */
// function pickKind(file) {
//     // 파일이 없으면 'empty' 반환
//     if (!file) return 'empty';
//     // 폴더면 'folder' 반환
//     if (file.type === 'folder') return 'folder';

//     const name = (file.name || '').toLowerCase();
//     const mime = (file.mime || '').toLowerCase();

//     // Office 문서 확장자 확인 (워드, 엑셀, 파워포인트, 한글 등)
//     if (
//         name.endsWith('.doc') ||
//         name.endsWith('.docx') ||
//         name.endsWith('.odt') ||
//         name.endsWith('.rtf') ||
//         name.endsWith('.hwp') ||
//         name.endsWith('.hwpx') ||
//         name.endsWith('.xls') ||
//         name.endsWith('.xlsx') ||
//         name.endsWith('.ppt') ||
//         name.endsWith('.pptx')
//     )
//         return 'office';

//     // 텍스트 파일 확인 (마크다운, 일반 텍스트)
//     if (name.endsWith('.md') || name.endsWith('.txt') || mime.startsWith('text/') || mime.includes('markdown')) return 'text';

//     // PDF 파일 확인
//     if (name.endsWith('.pdf') || mime.includes('pdf')) return 'pdf';

//     // JSON 파일 확인
//     if (name.endsWith('.json')) return 'json';

//     // 알 수 없는 형식
//     return 'unknown';
// }

/**
 * HTML 특수문자를 이스케이프 처리 (XSS 방지)
 * @param {string} text - 원본 텍스트
 * @returns {string} - HTML 엔티티로 변환된 안전한 텍스트
 */
// function escapeHtml(text) {
//     return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
// }

/**
 * 일반 텍스트를 HTML로 변환
 * @param {string} text - 원본 텍스트
 * @returns {string} - 각 줄을 <p> 태그로 감싼 HTML
 */
// function textToHtml(text = '') {
//     // 텍스트를 이스케이프 처리하고 줄바꿈으로 분리
//     const lines = escapeHtml(text).split(/\n/g);
//     if (!lines.length) return '<p></p>';
//     // 각 줄을 <p> 태그로 감싸되, 빈 줄은 <br />로 처리
//     return lines.map((line) => (line.trim() ? `<p>${line}</p>` : '<p><br /></p>')).join('');
// }

/**
 * PDF 파일을 iframe으로 보여주는 컴포넌트
//  */
// function PdfView({ file }) {
//     if (!file?.path) return <Pad>PDF 경로가 없습니다.</Pad>;
//     const url = toAbs(file.path);
//     return (
//         <Box sx={{ width: '100%', height: '100%' }}>
//             <iframe title="pdf" src={url} style={{ border: 'none', width: '100%', height: '100%' }} />
//         </Box>
//     );
// }

/**
 * 파일 편집기 메인 컴포넌트
 * 선택된 파일의 종류에 따라 적절한 뷰어/에디터를 보여줌
 */
export default function Editor() {
    // 파일 스토어에서 선택된 파일 가져오기
    const { reloadTrigger, filePath } = useFileStore();
    // const file = useMemo(() => selectedFile || null, [selectedFile]);
    // 파일 종류 판별
    // const kind = pickKind(file);

    // 문서 스토어에서 문서 관련 상태 및 함수 가져오기
    const { setDocumentId, content: docContent, setContent: setDocumentContent } = useDocumentStore();
    const setEditorInstance = useTocStore((s) => s.setEditorInstance);

    // 에디터 초기 콘텐츠 상태
    const [initialContent, setInitialContent] = useState('<p></p>');
    // 로딩 상태
    const [loading, setLoading] = useState(false);
    // 로드 에러 메시지
    const [loadError, setLoadError] = useState(null);

    // const [filePath, setFilePath] = useState('/uploads/admin/1/1/234.json');
    /**
     * 파일이 변경될 때마다 파일 내용을 로드하는 effect
     */
    useEffect(() => {
        // // 파일이 없거나 폴더인 경우: 초기화하고 종료
        // if (!file || file.type === 'folder') {
        //     setInitialContent('<p></p>');
        //     setDocumentContent(null);
        //     setLoading(false);
        //     setLoadError(null);
        //     return;
        // }

        // // 문서 ID 설정
        // setDocumentId(file.id);

        // // 임시저장(draft) 파일인 경우: 스토어의 콘텐츠 사용
        // if (file.meta?.isDraft) {
        //     const draftContent = docContent || '<p></p>';
        //     setInitialContent(draftContent);
        //     setDocumentContent(draftContent);
        //     setLoading(false);
        //     setLoadError(null);
        //     return;
        // }

        // // PDF나 알 수 없는 형식인 경우: 에디터에 빈 내용 설정
        // if (kind === 'pdf' || kind === 'unknown') {
        //     setInitialContent('<p></p>');
        //     setDocumentContent(null);
        //     setLoading(false);
        //     setLoadError(null);
        //     return;
        // }

        // // Office 파일이거나 경로가 없는 경우: 빈 내용 설정
        // if (!file.path || kind === 'office') {
        //     setInitialContent('<p></p>');
        //     setDocumentContent(null);
        //     setLoading(false);
        //     setLoadError(null);
        //     return;
        // }

        // // JSON 파일인 경우: JSON을 파싱해서 로드
        // if (kind === 'json') {
        //     setLoading(true);
        //     setLoadError(null);
        //     let cancelled = false; // 컴포넌트 언마운트 시 중단 플래그

        //     fetch(toAbs(file.path))
        //         .then(async (res) => {
        //             if (!res.ok) throw new Error(res.statusText || 'JSON 파일을 불러오지 못했습니다.');
        //             const jsonData = await res.json(); // JSON 파싱
        //             // 이미 언마운트된 경우 무시
        //             if (!cancelled) {
        //                 setInitialContent(jsonData);
        //                 setDocumentContent(jsonData);
        //             }
        //         })
        //         .catch((error) => {
        //             console.warn('[Editor] JSON 로드 실패', error);
        //             if (!cancelled) {
        //                 // 에러 발생 시 빈 문서로 시작
        //                 const emptyDoc = { type: 'doc', content: [] };
        //                 setInitialContent(emptyDoc);
        //                 setDocumentContent(emptyDoc);
        //                 setLoadError('JSON 파일 로드를 실패했습니다. 빈 문서로 시작합니다.');
        //             }
        //         })
        //         .finally(() => {
        //             if (!cancelled) setLoading(false);
        //         });

        //     // cleanup 함수: 컴포넌트 언마운트 시 중단
        //     return () => {
        //         cancelled = true;
        //     };
        // }

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

    // 파일이 선택되지 않은 경우
    // if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
    // 폴더가 선택된 경우
    // if (file.type === 'folder') return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

    // PDF 파일인 경우: PDF 뷰어 표시
    // if (kind === 'pdf') return <PdfView file={file} />;

    // 지원하지 않는 파일 형식인 경우
    // if (kind === 'unknown')
    //     return (
    //         <Pad>
    //             미지원 형식입니다. (권장: DOCX / MD / TXT / PDF)
    //             <Box sx={{ mt: 1, fontSize: 12 }}>
    //                 선택된 파일: <b>{file.name}</b> ({file.mime || 'unknown'})
    //             </Box>
    //             {file.path && (
    //                 <Box sx={{ mt: 1 }}>
    //                     <a href={toAbs(file.path)} target="_blank" rel="noreferrer">
    //                         원본 열기
    //                     </a>
    //                 </Box>
    //             )}
    //         </Pad>
    //     );

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
