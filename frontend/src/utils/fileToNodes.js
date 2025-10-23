export const toFolderNum = (rootId) =>
  rootId === 'root-01' ? 1 : rootId === 'root-02' ? 2 : 3

export function buildPublicPath({ userId, projectId, folderNum, fileName }) {
  return `/uploads/${encodeURIComponent(userId)}/${projectId}/${folderNum}/${encodeURIComponent(fileName)}`
}

export function filesToNodes({ files, rootId, projectId, userId }) {
  const folderNum = toFolderNum(rootId)
  return Array.from(files || []).map((f) => ({
    id: crypto.randomUUID(),
    type: 'file',
    name: f.name,
    mime: f.type || 'application/octet-stream',
    path: buildPublicPath({ userId, projectId, folderNum, fileName: f.name }),
    folderNum,
  }))
}
