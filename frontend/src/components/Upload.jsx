import useUpload from '../hooks/useUpload'
import { useFileStore } from '../store/useFileStore'
import { filesToNodes } from '../utils/fileToNodes' 
import { useNavigate } from 'react-router-dom'

export default function Upload() {
  const { uploadAsync, isUploading } = useUpload()
  const addNodes   = useFileStore(s => s.addUploadedFileNodes)
  const selectNode = useFileStore(s => s.selectNode)
  const navigate   = useNavigate()

  const projectId = 1      // ✅ DB에 존재하는 값
  const userId    = 1 // 저장 경로에 쓰이는 값
  const rootId    = 'root-01'// 01/02/03 중 어디로 업로드할지

  const onChange = async (e) => {
    const files = e.target.files
    if (!files?.length) return

    // 1) 서버 업로드
    await uploadAsync({ files, rootId, projectId, userId })

    // 2) 트리에 표시할 노드 만들고 추가
    const nodes = filesToNodes({ files, rootId, projectId, userId })
    addNodes(rootId, nodes)

    // 3) 첫 파일 선택 → 에디터가 즉시 표시
    selectNode(nodes[0].id)

    // 4) (옵션) 에디터 페이지로 라우팅
    navigate('/edit')

    e.target.value = ''
  }

  return (
    <label>
      파일 업로드
      <input type="file" multiple onChange={onChange} disabled={isUploading} />
      {isUploading && <span> 업로드 중…</span>}
    </label>
  )
}
