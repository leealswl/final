import api from './api';

export async function draftApi() {
    const res = await api.get('/uploads/admin/1/1/234.json');
    return res.data;
}