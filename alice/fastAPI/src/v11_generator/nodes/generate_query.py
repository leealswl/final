from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

# ✅ API 키 로드 (안전장치)
load_dotenv()

# ------------------------------------------------------------------
# [Context-Aware 컨설턴트 프롬프트]
# ------------------------------------------------------------------
PROMPT_TEMPLATE_CONSULTANT = """
당신은 정부 지원사업 합격을 돕는 **'전략기획 파트너'**입니다.
사용자와 대화하고 있지만, 당신의 최우선 목표는 **[판사의 평가]를 반영하여 점수를 80점이상(통과)으로 만드는 것**입니다.

<입력 정보>
1. **작성 목표**: "{target_chapter_info}"
2. **공고문 핵심**: "{anal_guide_summary}"
3. **누적된 정보**: {collected_data}
4. **사용자 발언**: "{user_prompt}"
5. **최근 대화**: {recent_history}

##### 6. [🚨 핵심] 판사의 평가 (Judge's Feedback) #####
- **현재 점수**: {current_score}점
- **평가 사유**: {grading_reason}
- **부족한 항목(Missing Points)**: {missing_points}
#######################################################

<사고 과정 (Think Process)>
1. **상태 점검**: 
   - 만약 [부족한 항목]이 존재한다면, 현재 사용자가 엉뚱한 이야기(이미 충분한 이야기)를 하고 있는지 확인하세요.
   - 예: 이미 ROI는 충분한데 계속 ROI를 말하고 있다면, 화제를 [부족한 항목]으로 돌려야 합니다.

2. **반응 및 전환**:
   - 사용자의 말에 **짧게 호응**("훌륭한 수치입니다")한 뒤, **"하지만 합격을 위해서는 ~가 보완되어야 합니다"**라며 화제를 전환하세요.
   - **무조건 [부족한 항목]에 대한 질문을 던지세요.**

3. **질문 전략**:
   - 질문은 구체적이어야 합니다. 
   - 예: "수익성은 증명되었습니다. (전환) 다만 심사위원은 **'사업의 필요성'**을 봅니다. 왜 **지금 이 시점**에 이 기술이 필요한가요?"

<출력 가이드>
- **절대 금지**: 했던 질문 반복하기, 점수가 깎인 원인을 무시하고 잡담 이어가기.
- **말투**: 전문가다운 자연스러운 회화체.
"""
# 대화가 100마디가 넘어갔을 때, messages 전체를 LLM에게 다 던져주면 토큰 비용이 폭발하고
# AI가 헷갈려 합니다. 그래서 **"최근 4마디([-4:])만 잘라서 보여주자"**라고 만든 것이
#  recent_history입니다.

def generate_query(state: ProposalGenerationState) -> Dict[str, Any]: 
    print("--- 노드 실행: generate_query (Score Display / Fix Error) ---")

    try:
        llm = ChatOpenAI(temperature=0.1, model="gpt-4o")
    except Exception:
        return {"current_query": "오류 발생"}

    # 1. 데이터 매핑
    user_prompt = state.get("user_prompt", "")
    collected_data = state.get("collected_data", "")
    if not collected_data: collected_data = "(없음)"
    
    current_score = state.get("completeness_score", 0) # 점수
    grading_reason = state.get("grading_reason", "")  # 이유
    missing_points = ", ".join(state.get("missing_subsections", []))
    fetched_context = state.get("fetched_context", {})
    anal_guide_summary = str(fetched_context.get("anal_guide", "전략 정보 없음"))

    # 2. [핵심] 현재 진행 중인 챕터 정보 정확히 가져오기
    toc_structure = state.get("draft_toc_structure", [])
    current_idx = state.get("current_chapter_index", 0)
    chapter_title = "전체 개요"
    target_info_full = "정보 수집"
    
    if toc_structure and current_idx < len(toc_structure):
        item = toc_structure[current_idx]
        # 예: "1.1 사업 배경"
        chapter_display = f"{item.get('number')} {item.get('title')}"
        target_info_full = f"[{chapter_display}]\n설명: {item.get('description')}"
    
    # 4. 히스토리 (recent_history)
    msgs = state.get("messages", []) # 내가 저장해놓은 전체족보 다가져옴
    recent_history = ""
    if msgs:
        for msg in msgs[-4:]:  # 최근 4개만뽑음
            role = "👤" if msg.get('role') == 'user' else "🤖"
            content = msg.get('content', '')
            recent_history += f"{role}: {content}\n" #문자열에 담음
    
    # State에서 부족한 항목 리스트를 가져옴
    missing_list = state.get("missing_subsections", [])
    # 리스트를 사용자 친화적인 문자열로 변환함.
    missing_points = ", ".join(missing_list) if missing_list else "(없음)" 

    # 5. LLM 실행
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE_CONSULTANT)
    chain = prompt | llm
    
    try:
        #  준비한 변수들을 딕셔너리로 묶어서 던져줌
        generated_response = chain.invoke({
            "anal_guide_summary": anal_guide_summary,
            "target_chapter_info": target_info_full,
            "user_prompt": user_prompt,
            "collected_data": collected_data,
            "recent_history": recent_history,
            "current_score": current_score,
            "grading_reason": grading_reason,
            "missing_points": missing_points
        }).content.strip()

    except Exception as e:
        print(f"❌ 프롬프트 입력 오류: {e}")
        generated_response = "질문 생성 중 변수 매핑 오류가 발생했습니다."
    
    # 6. 피드백 텍스트 생성
    feedback_text = ""  
    if grading_reason:
        feedback_text = f" | 💡 {grading_reason}"
    
    # [핵심] "현재 1.1번 진행 중입니다"를 명확히 표시
    final_response = f"{generated_response}\n\n**(📌 현재 진행중: [{chapter_display}] 완성도: {current_score}%{feedback_text})**"

    # 7. 히스토리 저장
    history = state.get("messages", [])
    history.append({"role": "assistant", "content": final_response})

    return {
        "current_query": final_response,
        "messages": history
    }