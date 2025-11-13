import axios from 'axios';

const api = axios.create({
    baseURL: '/backend',
    withCredentials: true,
    timeout: 300000, // 2025-11-09 수연 수정: AI 분석은 시간이 오래 걸릴 수 있으므로 5분으로 증가
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;
