# 파일명: ai_chat.py

from openai import OpenAI
import json
import os

async def handle_chat_message(user_message, user_id, project_id, openai_api_key):
    print("handle_chat_message (일반 챗봇) 실행")
    
    openai_client = OpenAI(api_key=openai_api_key)
    
    # 일반적인 AI 어시스턴트 역할 정의
    system_content = "당신은 친절하고 지식이 풍부한 AI 어시스턴트입니다."
    
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        
        ai_response_content = completion.choices[0].message.content
        
    except Exception as e:
        print(f"⚠️ GPT 호출 실패: {e}")
        ai_response_content = "⚠️ 챗봇 응답 생성 실패."

    result = {
        "aiResponse": ai_response_content,
        "userIdx": user_id,
        "projectIdx": project_id,
        "userMessage": user_message
    }

    return result