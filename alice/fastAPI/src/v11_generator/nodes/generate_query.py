# 파일: generate_query.py (전체 교체)

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()


PROMPT_TEMPLATE_CONSULTANT = """
당신은 정부 지원사업 기획서 작성을 돕는 AI 컨설턴트입니다.
사용자가 제공한 정보를 바탕으로 부족한 항목을 파악하고, 구체적이고 명확한 질문을 생성합니다.

======================================================================
📌 <입력 정보>
1. 작성 대상 목차: "{target_chapter_info}"
2. 현재까지 수집된 정보: {collected_data}
3. 사용자 메시지: "{user_prompt}"
4. 대화 히스토리: {recent_history}
5. 부족한 점 분석: {grading_reason}
======================================================================

🎯 <역할 및 의사결정 원칙>
1. {grading_reason}을 기반으로 부족한 요소를 분석합니다.
2. 수집된 정보({collected_data})에서 이미 존재하는 것 vs 부족한 요소를 분리합니다.
3. 부족한 요소를 보완하기 위한 **핵심 항목**을 구체적으로 나열합니다.
4. 이미 히스토리에서 질문했거나 답변되었던 내용은 절대 다시 묻지 않습니다.
5. 사용자가 바로 이해하고 답변할 수 있도록 간결하고 명확하게 작성합니다.

======================================================================
📝 <출력 형식>
아래 형식을 반드시 준수하십시오. 형식 변경 금지.

[추가 정보 요청]

아래 항목이 더 필요해요!

- (부족한 항목 1: 구체적으로 명시, 예: "해외 투자 유치 목표 금액")
- (부족한 항목 2: 구체적으로 명시, 예: "현지법인 설립 시점 및 예상 비용")
- (부족한 항목 3: 필요시 더 추가, 최대 3-5개)

📌 예시
(구체적인 예시를 2-3줄로 작성. 각 항목에 대한 실제 답변 예시를 보여주세요. 예: "2024년까지 해외 투자 50억 원 유치\n2025년 미국 법인 설립(예상 비용: 10억 원)\n매출 30% 증가, 글로벌 고객사 20곳 확보")

🙌 위처럼 알려주시면 바로 다음 단계로 진행할게요!

⚠️ 중요:
- 부족한 항목은 {grading_reason}을 기반으로 구체적으로 나열하세요 (최대 3-5개)
- 예시는 반드시 실제 답변 형식으로 2-3줄 작성하세요
- 심사 기준, 점수, 평가 내용 등은 절대 포함하지 마세요 (내부 참고용)
- 사용자가 바로 이해하고 답변할 수 있도록 간결하고 명확하게 작성하세요

======================================================================
⛔ 절대 금지
- 히스토리 중복 질문 반복
- 공감을 가장한 잡담, 의례적 인사
- "더 설명해주세요" / "추가 정보가 필요한데" 같은 포괄적 표현
- 심사 기준, 점수, 평가 내용 등 내부 정보 노출
- 부족한 항목을 너무 많게 나열 (3-5개 이내)
- 긴 설명이나 불필요한 배경 설명


"""

def generate_query(state: ProposalGenerationState) -> ProposalGenerationState:
    print("--- 노드 실행: generate_query (Score Display / Fix Error) ---")
    
    # 🌟 [오류 해결] generated_response 변수를 미리 초기화합니다.
    generated_response = ""
    
    try:
        llm = ChatOpenAI(temperature=0.1, model="gpt-4o-mini")
    except Exception:
        return {"current_query": "LLM 초기화 오류 발생"}

    # 1. 상태 변수 추출 및 초기값 설정
    user_prompt = state.get("user_prompt", "")
    collected_data = state.get("collected_data", "")
    if not collected_data:
        collected_data = "(없음)"
    
    current_avg_score = state.get("completeness_score", 0) 
    grading_reason = state.get("grading_reason", "")
    # missing_list = state.get("missing_subsections", [])
    section_scores = state.get("section_scores", {}) 
    # missing_points = ", ".join(missing_list) if missing_list else "(없음)"
    
    fetched_context = state.get("fetched_context", {})
    anal_guide_summary = str(fetched_context.get("anal_guide", "전략 정보 없음"))

    toc_structure = state.get("draft_toc_structure", [])
    current_idx = state.get("current_chapter_index", 0)
    
    # 2. [핵심] 진행률 표시 변수 초기화 및 계산
    major_chapter_title = "챕터 제목 없음"
    focused_subchapter_display = "초기 질문"
    focused_subchapter_score = current_avg_score #현재 ASSESS_INFO의 결과 점수
    all_sub_section_numbers = []
    # avg_score_description = "(데이터 로드 오류 또는 초기 진입)"
    target_info_full = "정보 수집"
    chapter_display = "전체 개요"

    if toc_structure and current_idx < len(toc_structure):
        major_chapter_item = toc_structure[current_idx]
        major_chapter_number = major_chapter_item.get("number", "0") 
        major_chapter_title = major_chapter_item.get("title", "제목 없음") 

        # 2-1. LLM 프롬프트에 사용될 주 챕터 정보 구성
        chapter_display = f"{major_chapter_item.get('number')} {major_chapter_item.get('title')}"
        target_info_full = f"[{chapter_display}]\n설명: {major_chapter_item.get('description')}" 

        print('target_info_full: ', target_info_full)
        
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
        for msg in msgs:
            role = "👤" if msg.get("role") == "user" else "🤖"
            content = msg.get("content", "")
            recent_history += f"{role}: {content}\n"

    # 4. LLM 호출 및 응답 생성
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE_CONSULTANT)
    chain = prompt | llm
    
    try:
        generated_response = chain.invoke({
            "target_chapter_info": target_info_full,
            "user_prompt": user_prompt,
            "collected_data": collected_data,
            "recent_history": recent_history,
            "grading_reason": grading_reason,
        }).content.strip()
    except Exception as e:
        print(f"❌ 프롬프트 입력 오류: {e}")
        generated_response = "질문 생성 중 서버 오류가 발생했습니다. 로그를 확인하세요."
    
    # 5. 최종 출력 (심사 기준 코멘트는 제거, 사용자에게는 질문만 표시)
    final_response = generated_response

    history = state.get("messages", [])
    history.append({"role": "assistant", "content": final_response})

    # 📌 [디버그] — score가 정상적으로 넘어오는지 확인
    # print("DEBUG >>> generate_query received state keys:", state.keys())
    # print("DEBUG >>> generate_query completeness_score:", state.get("completeness_score"))
    # print("DEBUG >>> generate_query section_scores:", section_scores)
    # print("DEBUG >>> generate_query focused score:", focused_subchapter_score)

    return {
        "current_query": final_response,
        "messages": history,
    }