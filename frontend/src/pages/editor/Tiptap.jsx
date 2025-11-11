// src/Tiptap.tsx
import { useEditor, EditorContent, EditorContext, useCurrentEditor } from '@tiptap/react';
import { FloatingMenu, BubbleMenu } from '@tiptap/react/menus';
import StarterKit from '@tiptap/starter-kit';
import { useMemo } from 'react';

const Tiptap = () => {
    const EditorJSONPreview = () => {
        const { editor } = useCurrentEditor();

        return <pre>{JSON.stringify(editor.getJSON(), null, 2)}</pre>;
    };

    const editor = useEditor({
        extensions: [StarterKit], // define your extension array
        content: '<p>Hello World!</p>', // initial content
    });

    // Memoize the provider value to avoid unnecessary re-renders
    const providerValue = useMemo(() => ({ editor }), [editor]);

    return (
        <EditorContext.Provider value={providerValue}>
            <EditorContent editor={editor} />
            <FloatingMenu editor={editor}>This is the floating menu</FloatingMenu>
            <BubbleMenu editor={editor}>This is the bubble menu</BubbleMenu>
        </EditorContext.Provider>
    );
};

export default Tiptap;
