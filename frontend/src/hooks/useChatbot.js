import { useMutation } from "@tanstack/react-query";
import api from "../utils/api";

export default function useChatbot() {
    return useMutation({
        mutationKey: ['chatbot', 'message'],
        mutationFn: async ({userMessage}) => {
            const res = await api.post('/api/ai-chat/response',{ userMessage})
            return res.data;
        }
    })
}