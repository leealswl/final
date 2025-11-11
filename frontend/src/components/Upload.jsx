import React, { useRef, forwardRef, useImperativeHandle } from 'react';
import useUpload from '../hooks/useUpload';
import { useFileStore } from '../store/useFileStore';
import { filesToNodes } from '../utils/fileToNodes';
import { useNavigate } from 'react-router-dom';
import { Button } from '@mui/material';

// forwardRef로 감싸고 내부 input 클릭을 외부로 노출
const Upload = forwardRef(function Upload({ rootId, asButton = true, onUploadComplete }, ref) {
    const fileInputRef = useRef(null);
    const { uploadAsync, isUploading } = useUpload();
    const addNodes = useFileStore((s) => s.addUploadedFileNodes);
    const selectNode = useFileStore((s) => s.selectNode);
    const projectId = useFileStore((s) => s.currentProjectId);
    const userId = useFileStore((s) => s.currentUserId);
    const navigate = useNavigate();

    // 외부에서 사용할 수 있도록 API 노출
    useImperativeHandle(
        ref,
        () => ({
            // 외부에서 uploadRef.current.click() 호출 가능
            click: () => {
                fileInputRef.current?.click();
            },
            // 필요하면 input 엘리먼트 자체도 반환
            getInput: () => fileInputRef.current,
        }),
        [],
    );

    const onChange = async (e) => {
        const files = e.target.files;
        if (!files?.length) return;
        if (!projectId || !userId) {
            alert('컨텍스트가 없습니다.');
            e.target.value = '';
            return;
        }

        try {
            await uploadAsync({ files, rootId, userId: String(userId) });
            const nodes = filesToNodes({ files, rootId, projectId, userId: String(userId) });
            addNodes(rootId, nodes);
            selectNode(nodes[0].id);
            // navigate('/works/edit');
            onUploadComplete?.(nodes);
        } catch (err) {
            alert(`업로드 실패: ${err?.message || err}`);
        } finally {
            e.target.value = '';
        }
    };

    return (
        <>
            <input type="file" ref={fileInputRef} hidden multiple accept=".md,.txt,.pdf,.docx,.hwp,.hwpx,.xlsx,.pptx,.zip,.rar" onChange={onChange} />

            {asButton && (
                <Button size="small" variant="outlined" disabled={isUploading} onClick={() => fileInputRef.current?.click()}>
                    파일 업로드
                </Button>
            )}
        </>
    );
});

export default Upload;
