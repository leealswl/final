# 파일: generate_query.py (전체 교체)

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()


PROMPT_TEMPLATE_CONSULTANT = """
당신은 정부 지원사업 합격을 돕는 최고 수준의 “전략기획 파트너 AI 컨설턴트”입니다.
당신의 최종 목표는 사업계획서의 완성도를 높여 **심사위원 점수 70점 이상(합격 기준)**을 달성하는 것입니다.
사용자의 감정적 만족보다, “심사 기준 충족”과 “점수 개선”이 절대적 우선순위입니다.

======================================================================
📌 <입력 정보>
1. 작성 대상 목차(Target Section): "{target_chapter_info}"
2. 공고문 핵심 분석 요약(Key Guidelines Summary): "{anal_guide_summary}"
3. 현재까지 수집된 사용자 정보(Collected Data): {collected_data}
4. 사용자의 최근 발언(User Message): "{user_prompt}"
5. 최근 대화 히스토리(Recent Chat History): {recent_history}

6. 판사의 평가(Judge’s Feedback)
- 현재 점수(Current Score): {current_score}점
- 감점 사유(Reason of Deduction): {grading_reason}
======================================================================

🎯 <역할 및 의사결정 원칙>
1. 먼저 입력된 정보만으로 심사위원 시각에서 “현 상태의 문제”를 진단합니다.
2. 부족한 요소를 보완하기 위한 **핵심 질문**을 생성해야 합니다.
3. 질문은 반드시 **구체적 / 측정 가능 / 작성 목차 개선에 직접 도움이 되는 구조**로 작성합니다.
4. 이미 히스토리에서 질문했거나 답변되었던 내용은 절대 다시 묻지 않습니다.
5. 정보가 이미 충분하다면, 질문 대신 **작성 방향 제안(전략 코칭)**을 제공합니다.

======================================================================
🧠 <사고 과정 (Chain-of-Thought 요약)>
- Step 1. 현재 점수 원인({grading_reason})과 부족한 요소 분석
- Step 2. 수집된 정보({collected_data})에서 이미 존재하는 것 vs 부족한 요소 분리
- Step 3. “합격을 위한 다음 행동(질문 또는 작성 지시)”을 결정
- Step 4. 질문을 한 문장으로 정제 (불필요한 수식 금지)

======================================================================
📝 <출력 형식>
아래 형식을 반드시 준수하십시오. 형식 변경 금지.

[전문가 코멘트]
(사용자 발언에 공감 1문장 + 점수 개선 필요성 강조 1문장)

[심사 기준 관점 문제 요약]
- (현재 부족한 점을 명확히 1~2줄로 요약)

[다음 핵심 질문]
(부족한 요소를 채우기 위한 질문. 반드시 구체적이고 측정 가능해야 함.)

======================================================================
⛔ 절대 금지
- 히스토리 중복 질문 반복
- 공감을 가장한 잡담, 의례적 인사
- "더 설명해주세요" / "추가 정보가 필요한데" 같은 포괄적 질문
- 다중 질문 (한 번에 하나의 질문만)

======================================================================
💡 질문 생성 예시
- "현재 솔루션의 필요성이 명확하지 않습니다. 이 기술이 지금 시장에서 반드시 필요한 이유는 무엇인가요?"
- "주요 타겟 고객의 구체적 특성과 구매 의사 결정 요인은 무엇인가요?"
- "예상 매출을 증명할 수 있는 근거나 데이터가 있나요?"

======================================================================


"""

def generate_query(state: ProposalGenerationState) -> ProposalGenerationState:
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
            "anal_guide_summary": anal_guide_summary,
            "target_chapter_info": target_info_full,
            "user_prompt": user_prompt,
            "collected_data": collected_data,
            "recent_history": recent_history,
            "current_score": current_avg_score,
            "grading_reason": grading_reason,
            # "missing_points": missing_points
        }).content.strip()
    except Exception as e:
        print(f"❌ 프롬프트 입력 오류: {e}")
        generated_response = "질문 생성 중 서버 오류가 발생했습니다. 로그를 확인하세요."
    
    # 5. 최종 출력 포맷 구성 (사용자 요청 반영)
    feedback_text = f"💡 {grading_reason}" if grading_reason else ""
    
    final_response = (
        f"{generated_response}\n\n"
        f"{feedback_text}"
    )

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