// MyEditor.jsx
import React, { useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

const MyEditor = () => {
    const [content, setContent] = useState('<p>Hello Tiptap!</p>');

    const editor = useEditor({
        extensions: [StarterKit],
        content,
        onUpdate: ({ editor }) => setContent(editor.getHTML()),
    });

    if (!editor) return null; // editor가 생성될 때까지 대기

    return (
        <div>
            {/* 툴바 */}
            <div style={{ marginBottom: '1rem' }}>
                <button onClick={() => editor.chain().focus().toggleBold().run()} style={{ fontWeight: editor.isActive('bold') ? 'bold' : 'normal' }}>
                    Bold
                </button>
                <button onClick={() => editor.chain().focus().toggleItalic().run()} style={{ fontStyle: editor.isActive('italic') ? 'italic' : 'normal' }}>
                    Italic
                </button>
            </div>

            {/* 에디터 영역 */}
            <EditorContent editor={editor} style={{ border: '1px solid #ccc', padding: '10px', minHeight: '150px' }} />
        </div>
    );
};

export default MyEditor;
