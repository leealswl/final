import axios from 'axios';

const api = axios.create({
    baseURL: '/backend',
    withCredentials: true,
    timeout: 3000000, // 2025-11-10 수정: AI 분석은 시간이 오래 걸릴 수 있으므로 10분으로 증가 (백엔드 타임아웃과 동일하게 설정)
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * 2025-11-17: 프로젝트의 분석 결과 목차(TOC) 조회
 * FastAPI의 result.json에서 sections 정보를 가져옴
 * 
 * @param {number} projectIdx - 프로젝트 ID
 * @returns {Promise} 목차 데이터 (sections 배열 포함)
 */
export const getToc = async (projectIdx) => {
    try {
        const response = await api.get('/api/analysis/toc', {
            params: { projectIdx }
        });
        return response.data;
    } catch (error) {
        console.error('목차 조회 실패:', error);
        throw error;
    }
};

export default api;
