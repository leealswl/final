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
      // 1) 서버 업로드
      await uploadAsync({ files, rootId, userId: String(userId) })

      // 2) 트리에 표시할 노드 만들고 추가
      const nodes = filesToNodes({ files, rootId, projectId, userId: String(userId)})
      addNodes(rootId, nodes)

      // 3) 첫 파일 선택 → 에디터가 즉시 표시
      selectNode(nodes[0].id)

      // 4) (옵션) 에디터 페이지로 라우팅
      navigate('/edit')

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
