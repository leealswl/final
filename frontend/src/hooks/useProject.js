import { useMutation } from '@tanstack/react-query';
import api from '../utils/api';
import { useProjectStore } from '../store/useProjectStore';

export default function UseProject(opts = {}) {
    const setProject = useProjectStore((s) => s.setProject);

    return useMutation({
        mutationKey: ['use', 'project'],
        mutationFn: async ({ userIdx }) => {
            const res = await api.post('/api/project/insert', { userIdx }, { withCredentials: true });
            return res.data;
        },
        onSuccess: async (data) => {
            setProject(data);
            opts.onSuccess?.(data);
        },
        onError: (err) => {
            const msg = err?.status === 401 ? '넌 실패했다' : err?.message || '넌 실패했다';
            opts.onError?.(msg);
        },
    });
}
