import axios from 'axios';

const FASTAPI_BASE_URL = 'http://localhost:8081/api/verifies'; // 나중에 env로 빼도 됨
const FASTAPI_DIRECT_BASE_URL = "http://localhost:8001";

export async function verifyLawSection({ text, focus }) {
    const payload = {
        text,
        focus: focus || null,
    };

    console.log('payload: ', payload)

    const res = await axios.post(`${FASTAPI_BASE_URL}/law`, payload);
    let law = res.data;

  // 1차 래핑: { status, data: {...} }
  if (law && typeof law === "object" && "data" in law) {
    law = law.data;
  }

  // 2차 래핑까지 있을 경우: { status, data: { status, data: {...} } }
  if (law && typeof law === "object" && "data" in law) {
    law = law.data;
  }

  // law 가 이제 진짜 law_rag 결과여야 함
  console.log("[verifyLawSection] flattened law:", law);

  return law;
}

// 🔹 공고 평가기준 자가진단
export async function evaluateNoticeCriteria({ projectIdx, text }) {
  const payload = {
    project_idx: projectIdx,
    draft_text: text,
    // 🔥 혹시 alias를 camelCase로 써뒀을 수도 있으니 둘 다 보내기
    projectIdx,
    draftText: text,
  };

  console.log("[evaluateNoticeCriteria] payload:", payload);

  const res = await axios.post(
    `${FASTAPI_DIRECT_BASE_URL}/evaluate/notice-criteria`,
    payload
  );

  const data = res.data;
  console.log("[evaluateNoticeCriteria] raw response:", data);

  return data; // { status, message, data } 형태라고 가정
}