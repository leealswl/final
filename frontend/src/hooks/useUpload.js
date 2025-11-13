import { useMutation } from '@tanstack/react-query';
import api from '../utils/api';
import { useFileStore } from '../store/useFileStore';
import { toFolderNum } from '../utils/folder';

export default function useUpload() {
    const projectId = useFileStore((state) => state.currentProjectId); //전역에서  project 읽기
    const userId = useFileStore((s) => s.currentUserId);

    const mutation = useMutation({
        mutationKey: ['upload', projectId, userId],
        mutationFn: async ({ files, rootId }) => {
            if (projectId == null) throw new Error('프로젝트 컨텍스트가 없습니다.');
            if (userId == null || String(userId) === '') throw new Error('유저 컨텍스트가 없습니다.');
            const arr = Array.from(files || []);
            if (!arr.length) return { status: 'skip', message: 'no files' };

            const folderNum = toFolderNum(rootId);
            const formdata = new FormData();
            arr.forEach((f) => formdata.append('files', f));
            // folders 키는 파일 개수만큼 반복
            for (let i = 0; i < arr.length; i++) formdata.append('folders', String(folderNum));
            formdata.append('projectidx', String(projectId));
            formdata.append('userid', String(userId));

            // /api/analysis 와 /api/analysis/ 모두 시도
            const tryPost = async (url) => {
                try {
                    const r = await api.post(url, formdata, { headers: { 'Content-Type': 'multipart/form-data' } });
                    console.log(r.data);
                    return r.data;
                } catch (err) {
                    const msg = err?.response?.data?.message || err?.response?.data?.error || err?.message || 'Upload failed';
                    console.error('[upload error]', url, err?.response?.status, err?.response?.data);
                    throw new Error(msg);
                }
            };

            try {
                return await tryPost('/api/analysis');
            } catch {
                return await tryPost('/api/analysis/');
            }
        },
    });

    return {
        upload: mutation.mutate,
        uploadAsync: mutation.mutateAsync,
        isUploading: mutation.isPending,
        isSuccess: mutation.isSuccess,
        isError: mutation.isError,
        error: mutation.error,
        data: mutation.data,
    };
}
//전역에서 project 읽고 폼데이터를 만들어서 api/analysis로 업로드. 리턴으로 usemutaion 반환
//전역에서 projectId, userId 읽어 컨텍스트 검증, 폼데이터구성
//file 은 upload 컴포넌트에서 받음
// 업로드는 서버상태 변경이기 떄문에 usemutation 사용
