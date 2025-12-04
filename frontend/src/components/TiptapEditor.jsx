import './editor/style/editor.css';
import './editor/style/table.css';

import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Box, Alert, Snackbar } from '@mui/material';
import { EditorContent, ReactNodeViewRenderer, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Heading from '@tiptap/extension-heading';
import TextAlign from '@tiptap/extension-text-align';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableHeader from '@tiptap/extension-table-header';
import TableCell from '@tiptap/extension-table-cell';
import CharacterCount from '@tiptap/extension-character-count';
import Placeholder from '@tiptap/extension-placeholder';
import Image from '@tiptap/extension-image';
import { mergeAttributes } from '@tiptap/core';

import Toolbar from './editor/Toolbar';
import TableToolbar from './editor/TableToolbar';
import ImageNodeView from './editor/nodes/ImageNodeView';
import ChartNodeView from './editor/nodes/ChartNodeView';
import TableContextMenu from './editor/TableContextMenu';
import { Node } from '@tiptap/core';

// ---------------------- Custom Extensions ----------------------
const headingLevels = [1, 2, 3];

const CustomTable = Table.extend({
    addAttributes() {
        return {
            ...this.parent?.(),
            class: {
                default: 'paladoc-table',
                parseHTML: (element) => element.getAttribute('class'),
                renderHTML: (attributes) => ({ class: attributes.class }),
            },
        };
    },
    renderHTML({ HTMLAttributes }) {
        return ['table', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), ['tbody', 0]];
    },
}).configure({
    resizable: true,
    allowTableNodeSelection: true,
    lastColumnResizable: false,
    HTMLAttributes: { class: 'paladoc-table' },
});

const CustomImage = Image.extend({
    addAttributes() {
        return {
            ...this.parent?.(),
            size: {
                default: 'medium',
                parseHTML: (element) => element.getAttribute('data-size') || 'medium',
                renderHTML: (attributes) => ({ 'data-size': attributes.size || 'medium' }),
            },
        };
    },
    addNodeView() {
        return ReactNodeViewRenderer(ImageNodeView);
    },
    configure({ inline }) {
        return this.extend({ inline }).configure({
            allowBase64: true,
            inline: false,
            selectable: true,
            draggable: false,
            HTMLAttributes: { class: 'paladoc-image' },
        });
    },
});

const Chart = Node.create({
    name: 'chart',
    group: 'block',
    atom: true,
    addAttributes() {
        return {
            chartType: {
                default: 'line',
                parseHTML: (element) => element.getAttribute('data-chart-type') || 'line',
                renderHTML: (attributes) => ({ 'data-chart-type': attributes.chartType }),
            },
            title: {
                default: '',
                parseHTML: (element) => element.getAttribute('data-title') || '',
                renderHTML: (attributes) => ({ 'data-title': attributes.title }),
            },
            data: {
                default: { labels: [], datasets: [] },
                parseHTML: (element) => {
                    const dataAttr = element.getAttribute('data-chart-data');
                    return dataAttr ? JSON.parse(dataAttr) : { labels: [], datasets: [] };
                },
                renderHTML: (attributes) => ({
                    'data-chart-data': JSON.stringify(attributes.data),
                }),
            },
            options: {
                default: {},
                parseHTML: (element) => {
                    const optionsAttr = element.getAttribute('data-chart-options');
                    return optionsAttr ? JSON.parse(optionsAttr) : {};
                },
                renderHTML: (attributes) => ({
                    'data-chart-options': JSON.stringify(attributes.options),
                }),
            },
        };
    },
    parseHTML() {
        return [
            {
                tag: 'div[data-type="chart"]',
            },
        ];
    },
    renderHTML({ HTMLAttributes }) {
        // return ['div', { 'data-type': 'chart', ...HTMLAttributes }, 0];
        return ['div', { 'data-type': 'chart', ...HTMLAttributes }];
    },
    addNodeView() {
        return ReactNodeViewRenderer(ChartNodeView);
    },
});

// ---------------------- Default Extensions ----------------------
const defaultExtensions = [
    StarterKit.configure({
        heading: false,
        inputRules: false,
        bulletList: { keepMarks: true, keepAttributes: false },
        orderedList: { keepMarks: true, keepAttributes: false },
        blockquote: false,
        codeBlock: false,
    }),
    Heading.configure({ levels: headingLevels }),
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    CustomTable,
    TableRow,
    TableHeader,
    TableCell.configure({ resizable: true }),
    CustomImage,
    Chart,
    // CharacterCount.configure({ limit: 100000 }),
    Placeholder.configure({ placeholder: '내용을 입력하거나 AI 초안을 생성해 보세요…' }),
];

// ---------------------- Helper ----------------------
function slugify(text) {
    return (
        text
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9가-힣\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-') || 'heading'
    );
}

// ---------------------- Component ----------------------
export default function TiptapEditor({ initialContent, contentKey, onContentChange, onHeadingsChange, onActiveHeadingChange, readOnly = false, registerEditor }) {
    const [snackbar, setSnackbar] = useState(null);
    const [tableMenu, setTableMenu] = useState(null);
    const hydrateKeyRef = useRef(null);
    const headingsRef = useRef([]);
    const extensions = useMemo(() => defaultExtensions, []);

    const editor = useEditor({
        extensions,
        content: initialContent || undefined,
        editable: !readOnly,
        editorProps: {
            attributes: {
                class: 'editor-page',
                style: 'overflow-y: auto; max-height: 1011px;',
            },
            handleDOMEvents: {
                contextmenu: (_view, event) => {
                    const target = event.target;
                    if (target instanceof HTMLElement && target.closest('table')) {
                        event.preventDefault();
                        setTableMenu({
                            mouseX: event.clientX + 2,
                            mouseY: event.clientY - 6,
                        });
                        return true; // 브라우저 기본 메뉴 막기
                    }
                    return false;
                },
            },
        },
        onUpdate: ({ editor }) => {
            const json = editor.getJSON();
            console.log('onUpdate json: ', json);
            onContentChange(json);
            emitHeadings(editor);
            emitActive(editor);
        },
    });

    // 2025-11-17: 에디터 인스턴스를 외부에 등록 (목차 스크롤 기능을 위해)
    useEffect(() => {
        if (editor && registerEditor) {
            registerEditor(editor);
        }
    }, [editor, registerEditor]);

    // ---------------------- A4 페이지 실제 분할 (CSS 기반 - 높이 고정) ----------------------
    // useEffect(() => {
    //     if (!editor) return;

    //     const PAGE_CONTENT_HEIGHT = 1011; // A4 내용 영역 높이 (1123 - 112)
    //     const PAGE_FULL_HEIGHT = 1123; // A4 전체 높이
    //     const PAGE_GAP = 40;

    //     const updatePageLayout = () => {
    //         const editorElement = editor.view.dom;
    //         if (!editorElement) return;

    //         const proseMirror = editorElement.querySelector('.ProseMirror');
    //         if (!proseMirror) return;

    //         // 현재 내용의 실제 높이 측정
    //         const contentHeight = proseMirror.scrollHeight;
    //         const pagesNeeded = Math.max(1, Math.ceil(contentHeight / PAGE_CONTENT_HEIGHT));

    //         // 페이지 컨테이너 찾기 또는 생성
    //         let container = editorElement.querySelector('.editor-pages-container');
    //         const existingPage = editorElement.querySelector('.editor-page');

    //         if (!container && pagesNeeded > 1) {
    //             container = document.createElement('div');
    //             container.className = 'editor-pages-container';
    //             container.style.cssText = `
    //                 display: flex;
    //                 flex-direction: column;
    //                 gap: ${PAGE_GAP}px;
    //                 width: 100%;
    //             `;

    //             // 기존 페이지를 컨테이너로 이동
    //             if (existingPage && existingPage.parentNode) {
    //                 existingPage.parentNode.insertBefore(container, existingPage);
    //                 container.appendChild(existingPage);
    //             }
    //         }

    //         // 여러 페이지가 필요한 경우 추가 페이지 생성
    //         if (container && pagesNeeded > 1) {
    //             const existingPages = container.querySelectorAll('.editor-page');
    //             const currentPageCount = existingPages.length;

    //             // 페이지가 부족하면 추가
    //             if (pagesNeeded > currentPageCount) {
    //                 for (let i = currentPageCount; i < pagesNeeded; i++) {
    //                     const page = document.createElement('div');
    //                     page.className = 'editor-page';
    //                     page.style.cssText = `
    //                         width: 794px;
    //                         height: ${PAGE_FULL_HEIGHT}px;
    //                         min-height: ${PAGE_FULL_HEIGHT}px;
    //                         max-height: ${PAGE_FULL_HEIGHT}px;
    //                         margin: 0 auto ${PAGE_GAP}px;
    //                         padding: 56px;
    //                         background: #ffffff;
    //                         box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.05), 0 2px 8px rgba(0, 0, 0, 0.1), 0 4px 16px rgba(0, 0, 0, 0.05);
    //                         position: relative;
    //                         page-break-after: always;
    //                         break-after: page;
    //                         overflow: hidden;
    //                         display: flex;
    //                         flex-direction: column;
    //                     `;
    //                     container.appendChild(page);
    //                 }
    //             }

    //             // 불필요한 페이지 제거
    //             if (currentPageCount > pagesNeeded) {
    //                 const pages = container.querySelectorAll('.editor-page');
    //                 for (let i = pagesNeeded; i < pages.length; i++) {
    //                     pages[i].remove();
    //                 }
    //             }
    //         } else if (container && pagesNeeded === 1) {
    //             // 한 페이지만 필요하면 컨테이너 제거
    //             const firstPage = container.querySelector('.editor-page');
    //             if (firstPage && firstPage.parentNode) {
    //                 firstPage.parentNode.insertBefore(firstPage, container);
    //                 container.remove();
    //             }
    //         }
    //     };

    //     const handleUpdate = () => {
    //         setTimeout(updatePageLayout, 100);
    //     };

    //     editor.on('update', handleUpdate);

    //     // 초기 실행
    //     setTimeout(updatePageLayout, 200);

    //     return () => {
    //         editor.off('update', handleUpdate);
    //     };
    // }, [editor]);

    // ---------------------- 파일/JSON 변경 즉시 반영 ----------------------
    useEffect(() => {
        if (!editor) return;

        if (!initialContent) return;

        let contentToSet = initialContent;

        // if (hydrateKeyRef.current === contentKey) return;

        // string이면 JSON인지 HTML인지 확인
        if (typeof initialContent === 'string') {
            console.log('????');
            try {
                contentToSet = JSON.parse(initialContent);
            } catch {
                contentToSet = initialContent;
            }
        }

        editor.commands.setContent(contentToSet, false);

        editor.commands.updateAttributes('table', { class: 'paladoc-table' });

        // hydrateKeyRef 갱신
        hydrateKeyRef.current = contentKey;
    }, [editor, initialContent, contentKey]);

    // ---------------------- Headings 추출 ----------------------
    const emitHeadings = useCallback(
        (instance) => {
            if (!instance) return;
            const doc = instance.state.doc;
            const items = [];
            const slugCount = {};
            doc.descendants((node, pos) => {
                if (node.type.name === 'heading') {
                    const text = node.textContent.trim() || '(제목 없음)';
                    const level = node.attrs.level || 1;
                    const base = slugify(text);
                    const count = (slugCount[base] || 0) + 1;
                    slugCount[base] = count;
                    const id = `${base}-${count}`;
                    const from = pos;
                    const to = pos + node.nodeSize;

                    items.push({ id, text, level, from, to });

                    try {
                        const dom = instance.view.nodeDOM(from);
                        if (dom instanceof HTMLElement) {
                            dom.setAttribute('data-heading-id', id);
                            dom.setAttribute('id', id);
                        }
                    } catch {}
                }
            });

            headingsRef.current = items;
            onHeadingsChange?.(items);
        },
        [onHeadingsChange],
    );

    // ---------------------- 현재 활성 heading ----------------------
    const emitActive = useCallback(
        (instance) => {
            const sel = instance.state.selection;
            const active = headingsRef.current.find((item) => sel.from >= item.from && sel.from <= item.to);
            onActiveHeadingChange?.(active ? active.id : null);
        },
        [onActiveHeadingChange],
    );

    // ---------------------- Render ----------------------
    return (
        <Box
            className="editor-root"
            sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                fontFamily: '"Pretendard", "Noto Sans KR", sans-serif',
            }}
        >
            {editor && <Toolbar editor={editor} />}

            <Box
                className="editor-wrapper"
                sx={{
                    flex: 1,
                    px: 3,
                    py: 3,
                    minHeight: 'calc(100vh - 200px)',
                    lineHeight: 1.6,
                    outline: 'none',
                    '& p': {
                        m: 0,
                        mb: 2,
                    },
                    '& h1, & h2, & h3': {
                        fontWeight: 700,
                        mt: 3,
                        mb: 1,
                    },
                    '& ul, & ol': {
                        pl: 3,
                        mb: 2,
                    },
                    '& table': {
                        borderCollapse: 'collapse',
                        my: 2,
                        width: '100%',
                        '& th, & td': {
                            border: '1px solid #d1d5db',
                            p: 1,
                            textAlign: 'left',
                            fontSize: 14,
                        },
                        '& th': {
                            backgroundColor: '#f3f4f6',
                            fontWeight: 600,
                        },
                    },
                }}
            >
                <EditorContent editor={editor} />
            </Box>

            {editor?.isActive('table') && <TableToolbar editor={editor} />}
            <TableContextMenu anchor={tableMenu} onClose={() => setTableMenu(null)} editor={editor} />
            <Snackbar open={Boolean(snackbar)} autoHideDuration={3000} onClose={() => setSnackbar(null)}>
                {snackbar && (
                    <Alert onClose={() => setSnackbar(null)} severity={snackbar.severity} sx={{ width: '100%' }}>
                        {snackbar.message}
                    </Alert>
                )}
            </Snackbar>
        </Box>
    );
}
