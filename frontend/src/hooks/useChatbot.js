import { useMutation } from "@tanstack/react-query";
import api from "../utils/api";

// export default function useChatbot() {
//     return useMutation({
//         mutationKey: ['chatbot', 'message'],
//         mutationFn: async {{ message}} => {
//             const res = await.api.post('/api/chat')
//         }
//     })
// }