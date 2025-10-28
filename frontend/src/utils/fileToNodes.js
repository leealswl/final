import { toFolderNum } from "./folder"

export function buildPublicPath({ userId, projectId, folderNum, fileName }) {
  return `/uploads/${encodeURIComponent(userId)}/${projectId}/${folderNum}/${encodeURIComponent(fileName)}`
}

export function filesToNodes({ files, rootId, projectId, userId }) {
  const folderNum = toFolderNum(rootId)
  return Array.from(files || []).map((file) => ({
    id: crypto.randomUUID(),  // 트리 노드 고유 ID 생성
    type: 'file', // 노드 유형(파일)
    name: file.name, // 파일 이름 (예: '보고서.hwp')
    mime: file.type || 'application/octet-stream', // 브라우저가 준 MIME, 없으면 기본값
    path: buildPublicPath({ userId, projectId, folderNum, fileName: file.name }), // 백엔드 규칙에 맞춘 공개 경로
    folderNum,
  }))
}

//업로드 훅이 서버에 올린뒤 ui에 표시할수잇도록 클라이언트 메타데이터 생성해줌
//rootId → 실제 저장 폴더 번호(folderNum)로 매핑
//files → 파일명/ MIME 등 클라이언트 노드 메타를 만들기 위해 필요.
//userId / projectId → 경로 규칙이 /uploads/{userId}/{projectId}/{folderNum}/{fileName} 이라서 반드시 필요.
// 메타데이터를 생성해서 ui에 표시할수잇도록 고유id 생성후 리턴함