import { useMutation } from '@tanstack/react-query';
import api from '../utils/api';
import { useAuthStore } from '../store/useAuthStore';

export default function useSignIn(opts = {}) {
    const setUser = useAuthStore((s) => s.setUser);

    return useMutation({
        mutationKey: ['user', 'login'],
        mutationFn: async ({ userId, userPw }) => {
            const res = await api.post('/api/user/login', { userId, userPw }, { withCredentials: true });
            return res.data; // { userId, username }
        },
        onSuccess: async (data) => {
            setUser(data);
            opts.onSuccess?.(data);
        },
        onError: (err) => {
            const msg = err?.status === 401 ? '아이디 또는 비밀번호가 올바르지 않습니다.' : err?.message || '로그인 실패';
            opts.onError?.(msg);
        },
    });
}
