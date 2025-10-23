import { useMutation } from '@tanstack/react-query'
import api from '../utils/api' 

const toFolderNum = (rootId) => (rootId === 'root-01' ? 1 : rootId === 'root-02' ? 2 : 3)

export default function useUpload() {
    const mutation = useMutation({
        mutationKey: ['upload'],
        mutationFn: async ({ files, rootId, projectId, userId }) => {
        const arr = Array.from(files || [])
        if (!arr.length) return { status: 'skip', message: 'no files' }

        const folderNum = toFolderNum(rootId)
        const fd = new FormData()
        arr.forEach((f) => fd.append('files', f))
        // 🔴 파일 개수만큼 folders 반복 (백엔드 요구사항)
        for (let i = 0; i < arr.length; i++) fd.append('folders', String(folderNum))
        fd.append('projectidx', String(projectId))
        fd.append('userid', userId)

        // '/api/analysis'와 '/api/analysis/' 둘 다 시도
        const tryPost = async (url) => {
            try {
            const r = await api.post(url, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
            return r.data
            } catch (err) {
            // 상세 로그 보기 좋게 가공
            const msg =
                err?.response?.data?.message ||
                err?.response?.data?.error ||
                err?.message ||
                'Upload failed'
            console.error('[upload error]', url, err?.response?.status, err?.response?.data)
            throw new Error(msg)
            }
        }

        try {
            return await tryPost('/api/analysis')
        } catch {
            return await tryPost('/api/analysis/')
        }
        },
    })

    return {
        upload: mutation.mutate,
        uploadAsync: mutation.mutateAsync,
        isUploading: mutation.isPending,
        isSuccess: mutation.isSuccess,
        isError: mutation.isError,
        error: mutation.error,   // <- 여기에 백엔드 메시지가 들어옴
        data: mutation.data,
    }
}
