from openai import OpenAI
import json
import os

async def generate_proposal(user_message, user_id, project_id, openai_api_key):
    print("generate_proposal 실행")
    # OpenAI 키 설정
    openai_client = OpenAI(api_key=openai_api_key)
    llm_prompt = f"사용자 요청: {user_message}"

    print(11111)
    completion = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7
    )
    print("try 실행 전")
    try:
        # GPT 응답 추출
        print("try 실행")
        plan_json = completion.choices[0].message.content
    except Exception:
        plan_json = "⚠️ AI 응답 파싱 실패"

    print('plan_json: ', plan_json)

    result = {
        "aiResponse123": plan_json,
        "aiResponse": any(phrase in user_message for phrase in ["에디터에 추가", "문서 생성", "플랜 반영"])
    }

    print('result: ', result)

    return result