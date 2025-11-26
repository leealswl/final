import axios from 'axios';

const FASTAPI_BASE_URL = 'http://localhost:8001'; // 나중에 env로 빼도 됨

export async function verifyLawSection({ text, focus }) {
    const payload = {
        text,
        focus: focus || null,
    };

    const res = await axios.post(`${FASTAPI_BASE_URL}/verify/law`, payload);
    return res.data;
}
