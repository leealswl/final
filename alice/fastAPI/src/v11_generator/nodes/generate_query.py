# 파일: generate_query.py (전체 교체)

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()


PROMPT_TEMPLATE_CONSULTANT = """
당신은 정부 지원사업 합격을 돕는 '전략기획 파트너'입니다.
사용자와 대화하고 있지만, 당신의 최우선 목표는 [판사의 평가]를 반영하여 
점수를 70점 이상(통과)으로 만드는 것입니다.

<입력 정보>
1. 작성 목표: "{target_chapter_info}"
2. 공고문 핵심: "{anal_guide_summary}"
3. 누적된 정보: {collected_data} [강조] 수집된 정보를 프롬프트에 명확히 포함
4. 사용자 발언: "{user_prompt}"
5. 최근 대화: {recent_history}

6. 판사의 평가 (Judge's Feedback)
- 현재 점수: {current_score}점
- 평가 사유: {grading_reason}
- 부족한 항목(Missing Points): {missing_points}

<사고 과정>
1. 상태 점검:
- **현재까지 누적된 정보({collected_data} 내용)**를 기반으로 판사의 평가를 해석.
- 사용자 발언이 새로운 정보를 주지 않는다면, **이전의 맥락(쓰레기 사업)**을 유지하며 질문을 생성해야 함.
2. 반응 및 전환:
- 사용자 말에 짧게 호응 후, "하지만 합격을 위해서는 ~가 보완되어야 합니다"로 화제를 전환.
- 무조건 부족한 항목에 대한 질문을 던짐.
3. 질문 전략:
- 질문은 구체적으로. 예: "수익성은 증명되었습니다. 다만 심사위원은 '사업의 필요성'을 봅니다. 왜 지금 이 시점에 이 기술이 필요한가요?"

출력 가이드
- 절대 금지: 반복 질문, 잡담.
- 말투: 전문가다운 자연스러운 회화체.
"""

def generate_query(state: ProposalGenerationState) -> Dict[str, Any]:
    print("--- 노드 실행: generate_query (Score Display / Fix Error) ---")
    
    # 🌟 [오류 해결] generated_response 변수를 미리 초기화합니다.
    generated_response = ""
    
    try:
        llm = ChatOpenAI(temperature=0.1, model="gpt-4o")
    except Exception:
        return {"current_query": "LLM 초기화 오류 발생"}

    # 1. 상태 변수 추출 및 초기값 설정
    user_prompt = state.get("user_prompt", "")
    collected_data = state.get("collected_data", "")
    if not collected_data:
        collected_data = "(없음)"
    
    current_avg_score = state.get("completeness_score", 0) 
    grading_reason = state.get("grading_reason", "")
    missing_list = state.get("missing_subsections", [])
    section_scores = state.get("section_scores", {}) 
    missing_points = ", ".join(missing_list) if missing_list else "(없음)"
    
    fetched_context = state.get("fetched_context", {})
    anal_guide_summary = str(fetched_context.get("anal_guide", "전략 정보 없음"))

    toc_structure = state.get("draft_toc_structure", [])
    current_idx = state.get("current_chapter_index", 0)
    
    # 2. [핵심] 진행률 표시 변수 초기화 및 계산
    major_chapter_title = "챕터 제목 없음"
    focused_subchapter_display = "초기 질문"
    focused_subchapter_score = current_avg_score #현재 ASSESS_INFO의 결과 점수
    all_sub_section_numbers = []
    avg_score_description = "(데이터 로드 오류 또는 초기 진입)"
    target_info_full = "정보 수집"
    chapter_display = "전체 개요"

    if toc_structure and current_idx < len(toc_structure):
        major_chapter_item = toc_structure[current_idx]
        major_chapter_number = major_chapter_item.get("number", "0") 
        major_chapter_title = major_chapter_item.get("title", "제목 없음") 

        # 2-1. LLM 프롬프트에 사용될 주 챕터 정보 구성
        chapter_display = f"{major_chapter_item.get('number')} {major_chapter_item.get('title')}"
        target_info_full = f"[{chapter_display}]\n설명: {major_chapter_item.get('description')}" 
        
        # 2-2. 하위 항목 데이터 추출
        for item in toc_structure:
            num = item.get("number", "")
            if num.startswith(major_chapter_number + '.') and '.' in num:
                all_sub_section_numbers.append(num)
        
        # 2-3. 포커스 대상 (1.1 항목) 및 점수 설정
        if all_sub_section_numbers:
            first_subchapter_num = all_sub_section_numbers[0]
            first_subchapter_item = next((item for item in toc_structure if item.get("number") == first_subchapter_num), None)
            
            if first_subchapter_item:
                focused_subchapter_display = f"{first_subchapter_item.get('number')} {first_subchapter_item.get('title')}"
                # 개별 점수 가져오기 
                focused_subchapter_score = section_scores.get(first_subchapter_num, 0)
        
        # 2-4. 전체 진행률 설명 문자열 생성
        subchapter_list_str = ", ".join(all_sub_section_numbers)
        if all_sub_section_numbers:
            avg_score_description = f"({subchapter_list_str} 평균, {major_chapter_title} 내 {len(all_sub_section_numbers)}개 항목)"
        else:
            avg_score_description = f"({major_chapter_title} 자체 진행률)"

    # 3. 최근 대화 기록 추출
    msgs = state.get("messages", [])
    recent_history = ""
    if msgs:
        for msg in msgs[-4:]:
            role = "👤" if msg.get("role") == "user" else "🤖"
            content = msg.get("content", "")
            recent_history += f"{role}: {content}\n"

    # 4. LLM 호출 및 응답 생성
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE_CONSULTANT)
    chain = prompt | llm
    
    try:
        generated_response = chain.invoke({
            "anal_guide_summary": anal_guide_summary,
            "target_chapter_info": target_info_full,
            "user_prompt": user_prompt,
            "collected_data": collected_data,
            "recent_history": recent_history,
            "current_score": current_avg_score,
            "grading_reason": grading_reason,
            "missing_points": missing_points
        }).content.strip()
    except Exception as e:
        print(f"❌ 프롬프트 입력 오류: {e}")
        generated_response = "질문 생성 중 서버 오류가 발생했습니다. 로그를 확인하세요."
    
    # 5. 최종 출력 포맷 구성 (사용자 요청 반영)
    feedback_text = f" | 💡 {grading_reason}" if grading_reason else ""
    
    final_response = (
        f"{generated_response}\n\n"
        # f"**(📌 전체완성도: {current_avg_score}% {avg_score_description}) "
        f"(현재 진행중: [{focused_subchapter_display}] 정보수집도: {focused_subchapter_score}%{feedback_text})**"
    )

    history = state.get("messages", [])
    history.append({"role": "assistant", "content": final_response})

    # 📌 [디버그] — score가 정상적으로 넘어오는지 확인
    print("DEBUG >>> generate_query received state keys:", state.keys())
    print("DEBUG >>> generate_query completeness_score:", state.get("completeness_score"))
    print("DEBUG >>> generate_query section_scores:", section_scores)
    print("DEBUG >>> generate_query focused score:", focused_subchapter_score)

    return {
        **state,
        "current_query": final_response,
        "messages": history,
    }