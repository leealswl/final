import api from "./api";

/** OnlyOffice DocEditor config + JWT 가져오기 */
export async function fetchOnlyOfficeConfig(fileId) {
  const { data } = await api.get(`/onlyoffice/config/${fileId}`);
  // data: { config, token }
  return data;
}

/** (옵션) 콜백 수신 상태를 서버에서 확인하고 싶을 때 */
export async function pingOnlyOffice() {
  // 서버 상태 확인용 임시 엔드포인트가 있다면 여기에…
  return true;
}

/** (텍스트 파일) 내용 읽기 */
export async function getTextContent(fileId) {
  const res = await api.get(`/files/${fileId}/content`, { responseType: "text" });
  return typeof res.data === "string" ? res.data : "";
}

/** (텍스트 파일) 내용 저장 */
export async function saveTextContent(fileId, text) {
  await api.put(`/files/${fileId}/content`, text, {
    headers: { "Content-Type": "text/plain;charset=utf-8" },
  });
}

/** (옵션) 업로드 (사이드바에서 사용할 수도) */
export async function uploadFiles(projectId, parentId, files) {
  const form = new FormData();
  [...files].forEach(f => form.append("file", f));
  form.append("projectId", projectId);
  if (parentId) form.append("parentId", parentId);

  const { data } = await api.post(`/files/upload`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // 생성된 노드(들)
}
