import axios from 'axios';

const FASTAPI_BASE_URL = 'http://localhost:8081/api/verifies'; // 나중에 env로 빼도 됨

export async function verifyLawSection({ text, focus }) {
    const payload = {
        text,
        focus: focus || null,
    };

    console.log('payload: ', payload)

    const res = await axios.post(`${FASTAPI_BASE_URL}/law`, payload);
    return res.data;
}
