import axios from "axios";

const FASTAPI_COMPARE_URL = "http://localhost:8001/compare"; 

export async function compareDraft(projectIdx, draftJson) {
  const payload = {
    project_idx: projectIdx,
    draft_json: draftJson,
  };

  console.log("📤 초안 비교 요청:", payload);

  try {
    const res = await axios.post(`${FASTAPI_COMPARE_URL}/draft`, payload);
    console.log("✅ 초안 비교 응답:", res.data);
    return res.data;
  } catch (error) {
    console.error("❌ 초안 비교 요청 실패:", error.response?.data || error.message);
    throw error;
  }
}
