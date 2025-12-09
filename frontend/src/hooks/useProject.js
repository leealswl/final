import { useMutation } from '@tanstack/react-query';
import api from '../utils/api';
import { useProjectStore } from '../store/useProjectStore';
import { useFileStore } from '../store/useFileStore';

/**
 * 2025-11-23 수정: 새 프로젝트 생성 시 파일 트리 초기화
 * 문제: 이전 프로젝트의 파일이 새 프로젝트에도 표시되는 문제
 * 해결: 새 프로젝트 생성 시 useFileStore의 resetTree() 호출하여 파일 트리 초기화
 */
export default function UseProject(opts = {}) {
    const setProject = useProjectStore((s) => s.setProject);
    //const setFileProjectIdx = useFileStore((s) => s.setProjectIdx);
    // const resetTree = useFileStore((s) => s.resetTree);

    return useMutation({
        mutationKey: ['user', 'project'],
        mutationFn: async ({ userIdx }) => {
            const res = await api.post('/api/project/insert', { userIdx }, { withCredentials: true });
            return res.data;
        },
        onSuccess: async (data) => {
            // 새 프로젝트 생성 시 파일 트리 초기화
            // console.log('🆕 새 프로젝트 생성: 파일 트리 초기화');
            // resetTree();
            
            // 프로젝트 정보 저장
            setProject(data);
            //setFileProjectIdx(data.projectIdx);
            opts.onSuccess?.(data);
        },
        onError: (err) => {
            const msg = err?.status === 401 ? '넌 실패했다' : err?.message || '넌 실패했다';
            opts.onError?.(msg);
        },
    });
}
// 새프로젝트 생성했을때 데이터베이스 추가되는 훅입니다