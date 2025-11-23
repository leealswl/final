"""
질문 생성 노드
부족한 정보를 수집하기 위한 질문을 생성하거나, 80점 이상일 때 완료 추천 메시지를 생성합니다.
"""
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI 
from langchain_core.prompts import PromptTemplate 
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()


PROMPT_TEMPLATE_CONSULTANT = """
당신은 정부 지원사업 합격을 돕는 최고 수준의 “전략기획 파트너 AI 컨설턴트”입니다.
당신의 최종 목표는 사업계획서의 완성도를 높여 **심사위원 점수 70점 이상(합격 기준)**을 달성하는 것입니다.
사용자의 감정적 만족보다, “심사 기준 충족”과 “점수 개선”이 절대적 우선순위입니다.

    
    # 🔑 1. 완료된 목차 언급 플래그 확인 (HISTORY_CHECKER에서 설정됨)
    target_completed = state.get("target_already_completed")
    
    # 🔑 [핵심 수정] 완료된 목차 언급 시 분기 (단순 응답)
    if target_completed:
        # 현재 진행해야 할 목표를 가져옵니다. (history_checker가 결정한 다음 챕터)
        current_target = state.get('target_chapter', '다음 작업 목표를 찾을 수 없습니다.')
        
        # 사용자 요청에 따른 단순 완료 메시지
        completion_message = (
            f"✅ **[작성 완료]**\n"
            f"사용자님께서 언급하신 목차 **'{target_completed}'**는 **이미 정보 수집이 완료**되어 초안 데이터에 저장되었습니다.\n\n"
            f"현재 저희가 집중해야 할 다음 목표는 **'{current_target}'** 입니다. 이 목표에 대한 정보를 계속 입력해 주시면 됩니다."
        )
        
        # 상태 업데이트 및 반환
        history = state.get("messages", [])
        history.append({"role": "assistant", "content": completion_message})
        
        print(f"✅ 완료된 목차 언급 감지: '{target_completed}' - 완료 메시지 반환")
        
        return {
            "current_query": completion_message,
            "messages": history,
            "target_already_completed": None # ⬅️ 플래그 초기화
        }
    
    current_avg_score = state.get("completeness_score", 0) 
    grading_reason = state.get("grading_reason", "")
    # missing_list = state.get("missing_subsections", [])
    section_scores = state.get("section_scores", {}) 
    # missing_points = ", ".join(missing_list) if missing_list else "(없음)"
    
    # 🔑 [핵심 변수] attempt_count 가져오기
    attempt_count = state.get("attempt_count", 0)
    
    # 2. [핵심] 진행률 표시 변수 초기화 및 계산
    major_chapter_title = "챕터 제목 없음"
    focused_subchapter_display = "초기 질문"
    focused_subchapter_score = current_avg_score #현재 ASSESS_INFO의 결과 점수
    all_sub_section_numbers = []
    # avg_score_description = "(데이터 로드 오류 또는 초기 진입)"
    target_info_full = "정보 수집"
    chapter_display = "전체 개요"

    # 🔑 2. 다음 목표 챕터 제목 찾기 (Manage Progression이 업데이트한 인덱스 기반)
    next_idx = state.get("current_chapter_index", 0)
    toc = state.get("draft_toc_structure", [])

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

    # 4. --- LLM 호출 및 응답 생성 ---
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm

    try:
        final_message_content = chain.invoke({
            "completeness_score": completeness_score,
            "grading_reason": grading_reason,
            # "missing_points": missing_points
        }).content.strip()
    except Exception as e:
        final_message_content = f"시스템 오류: 응답 생성 중 오류가 발생했습니다. ({e})"

    # 5. --- 최종 응답 구성 (새로운 로직) ---
    final_response_prefix = ""
    
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
