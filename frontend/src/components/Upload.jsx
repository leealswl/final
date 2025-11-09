import useUpload from '../hooks/useUpload'
import { useFileStore } from '../store/useFileStore'
import { filesToNodes } from '../utils/fileToNodes' 
import { useNavigate } from 'react-router-dom'
import { Button } from "@mui/material";

export default function Upload({ rootId }) {
  const { uploadAsync, isUploading } = useUpload()
  const addNodes   = useFileStore(s => s.addUploadedFileNodes)
  const selectNode = useFileStore(s => s.selectNode)
  const navigate   = useNavigate()
  const projectId = useFileStore(s => s.currentProjectId)
  const userId    = useFileStore(s => s.currentUserId)

  const onChange = async (e) => {
    const files = e.target.files
    if (!files?.length) return
    if (!projectId || !userId) { alert('컨텍스트가 없습니다.'); e.target.value = ''; return; }

     try {
      // 1) 서버 업로드 (2025-11-09 수연 수정: 파일 정보 받기)
      const response = await uploadAsync({ files, rootId, userId: String(userId) })

      // 2) Backend에서 반환한 파일 정보를 트리 노드로 변환
      // response.files 구조: [{ id, name, path, folder, size }, ...]
      let nodes
      if (response?.files && response.files.length > 0) {
        // Backend가 파일 정보를 반환했을 때
        nodes = response.files.map(fileInfo => ({
          id: `file-${fileInfo.id}`, // file-123 형태
          type: 'file',
          name: fileInfo.name,
          path: fileInfo.path, // 2025-11-09 수연: 파일 경로 저장
          size: fileInfo.size,
          children: undefined
        }))
      } else {
        // Fallback: 기존 방식 (파일 정보가 없을 때)
        nodes = filesToNodes({ files, rootId, projectId, userId: String(userId)})
      }

      // 3) 트리에 노드 추가
      addNodes(rootId, nodes)

      // 4) 첫 파일 선택 → 에디터가 즉시 표시
      selectNode(nodes[0].id)

      // 5) (옵션) 에디터 페이지로 라우팅
      navigate('edit')

    } catch (err) {
      alert(`업로드 실패: ${err?.message || err}`);
    } finally {
      e.target.value = '';
    }
  };

  return (
    <Button
      size="small"
      variant="outlined"
      disabled={isUploading}
      component="label" // ✅ 버튼 클릭으로 파일 선택
      startIcon={/* 원하면 아이콘 넣기 */ undefined}
    >
      파일 업로드
      <input
        type="file"
        hidden
        multiple
        accept=".md,.txt,.pdf,.docx,.hwp,.hwpx,.xlsx,.pptx"
        onChange={onChange}
      />
    </Button>
  )
}

// useUpload 훅으로 FormData 만들어 /api/analysis 업로드
// 업로드가 성공하면 filesToNodes로 UI 트리용 노드 메타데이터 생성
// addUploadedFileNodes(rootId, nodes)로 사이드바 트리에 즉시 반영
// 방금 올린 첫 파일을 selectNode로 선택 → 에디터가 바로 표시
// /edit로 이동
