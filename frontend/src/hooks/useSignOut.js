import { useMutation } from '@tanstack/react-query';
import api from '../utils/api';
import { useAuthStore } from '../store/useAuthStore';
// import { useQueryClient } from '@tanstack/react-query';

export default function useSignOut(opts = {}) {
    // const qc = useQueryClient();
    const clear = useAuthStore((s) => s.clear);

    return useMutation({
        mutationKey: ['user', 'logout'],
        mutationFn: async () => {
            await api.post('/api/user/logout');
        },
        onSuccess: async () => {
            clear();
            //   await qc.invalidateQueries({ queryKey: ["auth", "me"] });
            opts.onSuccess?.();
        },
    });
}
