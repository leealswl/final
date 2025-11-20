import React, { useRef, forwardRef, useImperativeHandle } from 'react';
import useUpload from '../hooks/useUpload';
import { useFileStore } from '../store/useFileStore';
import { filesToNodes } from '../utils/fileToNodes';
import { useNavigate } from 'react-router-dom';
import { Button } from '@mui/material';
import { useAuthStore } from '../store/useAuthStore';
import { useProjectStore } from '../store/useProjectStore';

// forwardRef로 감싸고 내부 input 클릭을 외부로 노출
const Upload = forwardRef(function Upload({ rootId, asButton = true, onUploadComplete }, ref) {
    const fileInputRef = useRef(null);
    const { uploadAsync, isUploading } = useUpload();
    const addNodes = useFileStore((s) => s.addUploadedFileNodes);
    const selectNode = useFileStore((s) => s.selectNode);
    // const projectId = useFileStore((s) => s.currentProjectId);
    const project = useProjectStore((s) => s.project);
    const user = useAuthStore((s) => s.user);
    // const userId = useFileStore((s) => s.currentUserId);
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
        if (!project.projectIdx || !user.userId) {
            alert('컨텍스트가 없습니다.');
            e.target.value = '';
            return;
        }

        try {
            // 1) 서버 업로드 (Backend에서 파일 정보 받기)
            const response = await uploadAsync({ files, rootId, userId: String(user.userId) });

            // 2) Backend에서 반환한 파일 정보를 트리 노드로 변환
            // response.files 구조: [{ id, name, path, folder, size }, ...]
            let nodes;
            if (response?.files && response.files.length > 0) {
                // Backend가 파일 정보를 반환했을 때
                nodes = response.files.map((fileInfo) => ({
                    id: `file-${fileInfo.id}`, // file-123 형태
                    type: 'file',
                    name: fileInfo.name,
                    path: fileInfo.path, // 서버에서 받은 파일 경로 저장
                    size: fileInfo.size,
                    children: undefined,
                }));
            } else {
                // Fallback: 기존 방식 (파일 정보가 없을 때)
                nodes = filesToNodes({ files, rootId, projectId: project.projectIdx, userId: String(user.userId) });
            }

            // 3) 트리에 노드 추가
            addNodes(rootId, nodes);

            // 4) 첫 파일 선택 → 에디터가 즉시 표시
            selectNode(nodes[0].id);

            // 5) 에디터 페이지로 라우팅
            navigate('/works/analyze');

            // 6) 콜백 호출
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
