import { BubbleMenu } from '@tiptap/react';

const EditorToolbar = ({ editor }) => {
    if (!editor) return null;

    return (
        <div>
            <button onClick={() => editor.chain().focus().toggleBold().run()}>Bold</button>
            <button onClick={() => editor.chain().focus().toggleItalic().run()}>Italic</button>
        </div>
    );
};

export default EditorToolbar;
