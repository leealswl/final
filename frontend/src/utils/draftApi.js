import api from './api';

export async function draftApi(filePath) {
    console.log(filePath);
    const res = await api.get(filePath);
    return res.data;
}
