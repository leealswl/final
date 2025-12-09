import { useMutation } from '@tanstack/react-query';
import api from '../utils/api';

export default function useChatbot() {
    return useMutation({
        mutationKey: ['chatbot', 'message'],
        mutationFn: async ({ userMessage, userIdx, projectIdx, userId, threadId }) => {
            const res = await api.post('/api/ai-chat/response', { userMessage, userIdx, projectIdx, userId, threadId }, { withCredentials: true });
            return res.data;
        },
    });
}
