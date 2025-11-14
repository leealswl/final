import openai
import json

async def generate_proposal(user_message, user_id, project_id, openai_api_key):
    # OpenAI 키 설정
    openai.api_key = openai_api_key

    llm_prompt = f"사용자 요청: {user_message}"

    completion = await openai.chat.completions.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": llm_prompt}],
    )

    try:
        # GPT 응답 추출
        plan_json = completion.choices[0].message.content
    except Exception:
        plan_json = "⚠️ AI 응답 파싱 실패"

    result = {
        "plan": plan_json,
        "showEditorButton": any(phrase in user_message for phrase in ["에디터에 추가", "문서 생성", "플랜 반영"])
    }

    return result