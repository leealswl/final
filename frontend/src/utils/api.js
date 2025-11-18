import axios from 'axios';

const api = axios.create({
    baseURL: '/backend',
    withCredentials: true,
    timeout: 600000, // 2025-11-10 수정: AI 분석은 시간이 오래 걸릴 수 있으므로 10분으로 증가 (백엔드 타임아웃과 동일하게 설정)
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;
