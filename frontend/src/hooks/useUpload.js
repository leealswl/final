// src/hooks/useLoad.js
import { useMutation } from '@tanstack/react-query'
import api from '../utils/api'
import { useFileStore } from '../store/useFileStore'

const toFolderNum = (rootId) => (rootId === 'root-01' ? 1 : rootId === 'root-02' ? 2 : 3)

export default function useLoad() {
  const projectId = useFileStore(s => s.currentProjectId)
  const userId    = useFileStore(s => s.currentUserId)

  const mutation = useMutation({
    mutationKey: ['upload'],
    mutationFn: async ({ files, rootId }) => {
      if (!projectId || !userId) throw new Error('프로젝트/유저 컨텍스트가 없습니다.')
      const arr = Array.from(files || [])
      if (!arr.length) return { status: 'skip', message: 'no files' }

      const folderNum = toFolderNum(rootId)
      const fd = new FormData()
      arr.forEach((f) => fd.append('files', f))
      // folders 키는 파일 개수만큼 반복
      for (let i = 0; i < arr.length; i++) fd.append('folders', String(folderNum))
      fd.append('projectidx', String(projectId))
      fd.append('userid', userId)

      // /api/analysis 와 /api/analysis/ 모두 시도 (서버 매핑 여유)
      const tryPost = async (url) => {
        try {
          const r = await api.post(url, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
          return r.data
        } catch (err) {
          const msg = err?.response?.data?.message || err?.response?.data?.error || err?.message || 'Upload failed'
          console.error('[upload error]', url, err?.response?.status, err?.response?.data)
          throw new Error(msg)
        }
      }
      try { return await tryPost('/api/analysis') }
      catch { return await tryPost('/api/analysis/') }
    },
  })

  return {
    upload: mutation.mutate,
    uploadAsync: mutation.mutateAsync,
    isUploading: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    data: mutation.data,
  }
}
