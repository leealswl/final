import React, { useEffect, useMemo, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useFileStore } from '../../../store/useFileStore';
import { useDocumentStore } from '../../../store/useDocumentStore';
import { useTocStore } from '../../../store/useTocStore';
import TiptapEditor from '../../../components/TiptapEditor';

const toAbs = (p) => (p?.startsWith('http') ? p : `http://localhost:8081${p}`);

function Center({ children }) {
    return <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>{children}</Box>;
}

function Pad({ children }) {
    return <Box sx={{ p: 2, color: 'text.secondary' }}>{children}</Box>;
}

function pickKind(file) {
    if (!file) return 'empty';
    if (file.type === 'folder') return 'folder';
    const name = (file.name || '').toLowerCase();
    const mime = (file.mime || '').toLowerCase();
    if (
        name.endsWith('.doc') ||
        name.endsWith('.docx') ||
        name.endsWith('.odt') ||
        name.endsWith('.rtf') ||
        name.endsWith('.hwp') ||
        name.endsWith('.hwpx') ||
        name.endsWith('.xls') ||
        name.endsWith('.xlsx') ||
        name.endsWith('.ppt') ||
        name.endsWith('.pptx')
    )
        return 'office';
    if (name.endsWith('.md') || name.endsWith('.txt') || mime.startsWith('text/') || mime.includes('markdown')) return 'text';
    if (name.endsWith('.pdf') || mime.includes('pdf')) return 'pdf';
    if (name.endsWith('.json')) return 'json';
    return 'unknown';
}

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function textToHtml(text = '') {
    const lines = escapeHtml(text).split(/\n/g);
    if (!lines.length) return '<p></p>';
    return lines.map((line) => (line.trim() ? `<p>${line}</p>` : '<p><br /></p>')).join('');
}

function PdfView({ file }) {
    if (!file?.path) return <Pad>PDF 경로가 없습니다.</Pad>;
    const url = toAbs(file.path);
    return (
        <Box sx={{ width: '100%', height: '100%' }}>
            <iframe title="pdf" src={url} style={{ border: 'none', width: '100%', height: '100%' }} />
        </Box>
    );
}

export default function Editor() {
    const { selectedFile } = useFileStore();
    const file = useMemo(() => selectedFile || null, [selectedFile]);
    const kind = pickKind(file);

    const { setDocumentId, content: docContent, setContent: setDocumentContent } = useDocumentStore();
    const setEditorInstance = useTocStore((s) => s.setEditorInstance);

    const [initialContent, setInitialContent] = useState('<p></p>');
    const [loading, setLoading] = useState(false);
    const [loadError, setLoadError] = useState(null);

    useEffect(() => {
        if (!file || file.type === 'folder') {
            setInitialContent('<p></p>');
            setDocumentContent(null);
            setLoading(false);
            setLoadError(null);
            return;
        }

        setDocumentId(file.id);

        if (file.meta?.isDraft) {
            const draftContent = docContent || '<p></p>';
            setInitialContent(draftContent);
            setDocumentContent(draftContent);
            setLoading(false);
            setLoadError(null);
            return;
        }

        if (kind === 'pdf' || kind === 'unknown') {
            setInitialContent('<p></p>');
            setDocumentContent(null);
            setLoading(false);
            setLoadError(null);
            return;
        }

        if (!file.path || kind === 'office') {
            setInitialContent('<p></p>');
            setDocumentContent(null);
            setLoading(false);
            setLoadError(null);
            return;
        }

        if (kind === 'json') {
            setLoading(true);
            setLoadError(null);
            let cancelled = false;

            fetch(toAbs(file.path))
                .then(async (res) => {
                    if (!res.ok) throw new Error(res.statusText || 'JSON 파일을 불러오지 못했습니다.');
                    const jsonData = await res.json(); // JSON 파싱
                    if (!cancelled) {
                        setInitialContent(jsonData);
                        setDocumentContent(jsonData);
                    }
                })
                .catch((error) => {
                    console.warn('[Editor] JSON 로드 실패', error);
                    if (!cancelled) {
                        const emptyDoc = { type: 'doc', content: [] };
                        setInitialContent(emptyDoc);
                        setDocumentContent(emptyDoc);
                        setLoadError('JSON 파일 로드를 실패했습니다. 빈 문서로 시작합니다.');
                    }
                })
                .finally(() => {
                    if (!cancelled) setLoading(false);
                });

            return () => {
                cancelled = true;
            };
        }

        let cancelled = false;
        setLoading(true);
        setLoadError(null);

        fetch(toAbs(file.path))
            .then(async (res) => {
                if (!res.ok) throw new Error(res.statusText || '파일을 불러오지 못했습니다.');
                const txt = await res.text();
                if (!cancelled) {
                    const html = textToHtml(txt);
                    setInitialContent(html);
                    setDocumentContent(html);
                }
            })
            .catch((error) => {
                console.warn('[Editor] 콘텐츠 로드 실패', error);
                if (!cancelled) {
                    const emptyHtml = '<p></p>';
                    setInitialContent(emptyHtml);
                    setDocumentContent(emptyHtml);
                    setLoadError('파일 내용을 불러오지 못했습니다. 빈 문서로 시작합니다.');
                }
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [file, kind, setDocumentId, setDocumentContent]);

    if (!file) return <Pad>왼쪽에서 파일을 선택하세요.</Pad>;
    if (file.type === 'folder') return <Pad>폴더가 아니라 파일을 선택해 주세요.</Pad>;

    if (kind === 'pdf') return <PdfView file={file} />;

    if (kind === 'unknown')
        return (
            <Pad>
                미지원 형식입니다. (권장: DOCX / MD / TXT / PDF)
                <Box sx={{ mt: 1, fontSize: 12 }}>
                    선택된 파일: <b>{file.name}</b> ({file.mime || 'unknown'})
                </Box>
                {file.path && (
                    <Box sx={{ mt: 1 }}>
                        <a href={toAbs(file.path)} target="_blank" rel="noreferrer">
                            원본 열기
                        </a>
                    </Box>
                )}
            </Pad>
        );

    return (
        <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
            {loading && (
                <Center>
                    <CircularProgress size={24} />
                </Center>
            )}
            {!loading && loadError && <Box sx={{ px: 2, py: 1, bgcolor: '#fff4e5', color: '#8a6d3b', borderBottom: '1px solid #f0deb4' }}>{loadError}</Box>}
            <Box sx={{ flex: 1, minHeight: 0 }}>
                <TiptapEditor 
                    initialContent={initialContent} 
                    contentKey={file.id} 
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
    );
}
