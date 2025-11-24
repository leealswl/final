// 파일명: TiptapEditor.jsx
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
import TableContextMenu from './editor/TableContextMenu';

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
    CharacterCount.configure({ limit: 100000 }),
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
    const [tableSelection, setTableSelection] = useState(null);

    const extensions = useMemo(() => defaultExtensions, []);

    const editor = useEditor({
        extensions,
        content: initialContent || undefined,
        editable: !readOnly,
        editorProps: { attributes: { class: 'editor-page' } },
        onUpdate: ({ editor }) => {
            onContentChange?.(editor.getJSON());
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

    // ---------------------- 파일/JSON 변경 즉시 반영 ----------------------
    useEffect(() => {
        if (!editor) return;
        if (!initialContent) return;

        let contentToSet = initialContent;

        // string이면 JSON인지 HTML인지 확인
        if (typeof initialContent === 'string') {
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
        // <Box className="editor-root">
        //   {editor && <Toolbar editor={editor} />}
        //   <Box className="editor-wrapper">
        //     <EditorContent editor={editor} />
        //   </Box>
        //   {tableSelection ? <TableToolbar editor={editor} selection={tableSelection} /> : null}
        //   <TableContextMenu anchor={tableMenu} onClose={() => setTableMenu(null)} editor={editor} />
        //   <Snackbar
        //     open={Boolean(snackbar)}
        //     autoHideDuration={3000}
        //     onClose={() => setSnackbar(null)}
        //   >
        //     {snackbar ? (
        //       <Alert onClose={() => setSnackbar(null)} severity={snackbar.severity} sx={{ width: "100%" }}>
        //         {snackbar.message}
        //       </Alert>
        //     ) : null}
        //   </Snackbar>
        // </Box>
        // TiptapEditor.jsx (CSS를 MUI sx로 변환)
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
                    overflowY: 'auto',
                    px: 3, // padding-left, right
                    py: 3, // padding-top, bottom
                    minHeight: 'calc(100vh - 200px)',
                    lineHeight: 1.6,
                    outline: 'none',
                    '& p': {
                        m: 0,
                        mb: 2, // margin-bottom 1em
                    },
                    '& h1, & h2, & h3': {
                        fontWeight: 700,
                        mt: 3, // margin-top 1.5em
                        mb: 1, // margin-bottom 0.5em
                    },
                    '& ul, & ol': {
                        pl: 3, // padding-left: 24px
                        mb: 2,
                    },
                    '& table': {
                        borderCollapse: 'collapse',
                        my: 2, // margin-top/bottom 16px
                        width: '100%',
                        '& th, & td': {
                            border: '1px solid #d1d5db',
                            p: 1, // padding 8px
                            textAlign: 'left',
                            fontSize: 14,
                        },
                        '& th': {
                            backgroundColor: '#f3f4f6',
                            fontWeight: 600,
                        },
                    },
                    '&:focus-within': {
                        boxShadow: 'inset 0 0 0 2px #1976d2',
                    },
                }}
            >
                <EditorContent editor={editor} />
            </Box>

            {tableSelection && <TableToolbar editor={editor} selection={tableSelection} />}
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
