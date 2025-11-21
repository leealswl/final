"""
질문 생성 노드
부족한 정보를 수집하기 위한 질문을 생성하거나, 80점 이상일 때 완료 추천 메시지를 생성합니다.
"""
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI 
from langchain_core.prompts import PromptTemplate 
from ..state_types import ProposalGenerationState
import logging
# load_dotenv() # 이미 로드되었다고 가정

# DEBUG 용도
# logging.basicConfig(level=logging.DEBUG) 

def generate_query(state: ProposalGenerationState) -> Dict[str, Any]:
    print("--- 노드 실행: generate_query (Consultant) ---")
    
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
    
    # 🔑 2. 챕터 완료 플래그 확인 (MANAGE_PROGRESSION에서 설정됨)
    just_completed = state.get("section_just_completed")
    
    # 🔑 [핵심 변수] attempt_count 가져오기
    attempt_count = state.get("attempt_count", 0)
    
    # 🔑 3. 상태 변수 로드 (UX와 Flow에 필요한 모든 변수)
    completeness_score = state.get("completeness_score", 0)
    grading_reason = state.get("grading_reason", "추가적인 정보가 필요합니다.")
    current_title = state.get("target_chapter", "목차 제목 없음")
    collected_data = state.get("collected_data", "")
    is_sufficient = completeness_score >= 80

    # 🔑 2. 다음 목표 챕터 제목 찾기 (Manage Progression이 업데이트한 인덱스 기반)
    next_idx = state.get("current_chapter_index", 0)
    toc = state.get("draft_toc_structure", [])

    if next_idx < len(toc):
        next_chapter_title = toc[next_idx].get("title", "최종 마무리 단계")
    else:
        next_chapter_title = "최종 초안 생성" # 모든 챕터가 완료된 경우
    
    # --- LLM 초기화 ---
    llm = None
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")
        # LLM 실패 시 하드코딩된 에러 메시지를 반환
        return {"current_query": f"시스템 오류: LLM 초기화 실패. {e}"}
    
    # 3. --- 프롬프트 템플릿 선택 및 메시지 정의 ---
    print(f"🔍 점수 확인: {completeness_score}점, 충분성: {is_sufficient}")
    
    if is_sufficient:
        print(f"✅ 80점 이상: 완료 추천 메시지 생성 모드")
        # 80점 이상일 때: 완료 추천 프롬프트를 사용 (흐름 전환 메시지)
        PROMPT_TEMPLATE = """
            당신은 기획서 작성의 흐름을 지능적으로 관리하는 전문 어시스턴트입니다.
            
            [상태 정보]
            - 현재 목차는 {current_title}이며, {completeness_score}점으로 합격 기준을 통과했습니다.
            - 다음 진행 목차는 {next_chapter_title}입니다.
            
            [평가 결과]
            이전 평가 사유: {grading_reason}
            
            [출력 지침: 절대 질문 금지]
            1. **절대 사용자에게 추가 정보를 요구하는 질문을 하지 마십시오.**
            2. {current_title}이 합격했음을 축하하고, 정보 수집이 종료되었음을 알리세요.
            3. 이전 평가 사유를 참고하여, '합격은 했으나, **더 완벽하게 하려면 이 내용을 {next_chapter_title}을 시작하기 전에 보완하는 것이 좋다**'고 조언만 하십시오. (권유 톤)
            4. 최종적으로, **{next_chapter_title}에 대한 정보 수집을 시작할 것인지** 사용자에게 확인하고, 긍정적인 응답을 유도하세요.
            """
    else:
        print(f"⚠️ 80점 미만: 추가 정보 요청 메시지 생성 모드")
        # 80점 미만일 때: 추가 정보 요청 프롬프트를 사용
        PROMPT_TEMPLATE = """
            당신은 기획서 작성의 부족한 부분을 채우는 전문 어시스턴트입니다.
            
            [현재 목표 목차]: {current_title}
            [평가 결과 (부족 사유)]: {grading_reason}
            [현재까지 수집된 원본 정보]: {collected_data}
            
            [출력 지침]
            1. 사용자에게 현재 목차({current_title})의 점수({completeness_score}점)가 부족함을 명확히 알리세요.
            2. 부족 사유({grading_reason})를 인용하여, 어떤 정량적 데이터나 구체적인 근거가 필요한지 친절하게 재질문하세요.
            """

    # 4. --- LLM 호출 및 응답 생성 ---
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm

    try:
        final_message_content = chain.invoke({
            "completeness_score": completeness_score,
            "grading_reason": grading_reason,
            "current_title": current_title, 
            "next_chapter_title": next_chapter_title,
            "collected_data": collected_data 
            # Note: current_idx 등은 PromptTemplate 내에 직접 사용되지 않아 제외함
        }).content.strip()
    except Exception as e:
        final_message_content = f"시스템 오류: 응답 생성 중 오류가 발생했습니다. ({e})"

    # 5. --- 최종 응답 구성 (새로운 로직) ---
    final_response_prefix = ""
    
    if just_completed:
        # 🔑 [핵심 수정] 섹션 완료 메시지 생성 (1.1 정보)
        completed_score = state.get("completeness_score", 0)
        completed_reason = state.get("grading_reason", "정보 수집이 성공적으로 완료되었습니다.")
        
        # 🔑 추가: 상세 평가 항목 가져오기
        breakdown_data = state.get("assessment_breakdown", {})
        
        # 🔑 상세 평가 목록 문자열 생성
        breakdown_list_str = ""
        lowest_item_title = ""
        
        if breakdown_data:
            # 항목 이름 매핑
            mapping = {
                "RATER_1": "1. 정량적 데이터 포함 여부",
                "RATER_2": "2. 논리적 연결성",
                "RATER_3": "3. 공고문 전략 반영"
            }
            # 점수가 낮은 순서로 정렬하여, 가장 부족한 항목을 타겟합니다.
            sorted_items = sorted(breakdown_data.items(), key=lambda item: item[1])
            
            breakdown_list_str += "\n\n**[항목별 상세 평가]**"
            for code, score in sorted_items:
                title = mapping.get(code, code)
                breakdown_list_str += f"\n- {title}: {score}점"
            
            # 가장 낮은 점수 항목을 찾기
            lowest_item_title = mapping.get(sorted_items[0][0], sorted_items[0][0])
        
        # 1. 🔑 [최대 1회 보완 제어 및 메시지 통합]
        # 100점 미만이고, 아직 보완 요청을 한 번도 하지 않았을 때만 보완 요청 메시지 생성
        if completeness_score < 100 and attempt_count == 0:
            # **보완 맥락과 요청 통합:** 이유를 먼저 제시하고 행동을 유도
            if lowest_item_title:
                final_action_message = (
                    f"\n\n**📌 마지막 보완 요청 (1회 기회):**\n"
                    f"합격 기준을 통과했지만, 최종 완성도를 높이기 위해 **[{lowest_item_title}]** 항목에 대한 보완이 필요합니다.\n"
                    f"판사의 평가에 따르면, 해당 항목이 부족한 이유는 다음과 같습니다.\n"
                    f"> *{completed_reason}*\n\n"  # ⬅️ 전체 reason을 맥락으로 통합
                    f"**위의 평가 사유를 참고하여, 마지막으로 보완하고 싶은 점을 적어주세요.** (이후에는 다음 목차로 자동 진행됩니다.)"
                )
            else:
                final_action_message = (
                    f"\n\n**📌 마지막 보완 요청 (1회 기회):**\n"
                    f"합격 기준을 통과했지만, 최종 완성도를 높이기 위해 추가 보완이 필요합니다.\n"
                    f"판사의 평가에 따르면, 부족한 이유는 다음과 같습니다.\n"
                    f"> *{completed_reason}*\n\n"  # ⬅️ 전체 reason을 맥락으로 통합
                    f"**위의 평가 사유를 참고하여, 마지막으로 보완하고 싶은 점을 적어주세요.** (이후에는 다음 목차로 자동 진행됩니다.)"
                )
            
            # 다음 상태는 attempt_count를 1로 증가시킵니다.
            next_attempt_count = attempt_count + 1
            
        else:
            # (1) 이미 1회 보완을 시도했거나 (2) 점수가 100점일 때 -> 무조건 다음 챕터로 진행
            # 다음 목차 제목 가져오기
            next_idx = state.get("current_chapter_index", 0)
            toc = state.get("draft_toc_structure", [])
            if next_idx < len(toc):
                next_chapter_title = toc[next_idx].get("title", "다음 목차")
            else:
                next_chapter_title = "최종 초안 생성"
            
            final_action_message = (
                f"\n\n**⭐⭐ 정보 수집 완료! ⭐⭐**\n"
                f"현재 점수({completeness_score}점)는 초안 작성이 **완벽에 가깝게** 준비되었습니다. 더 이상의 보완은 필요하지 않습니다.\n"
                f"**이제 다음 목차인 '{next_chapter_title}'에 대한 정보 수집을 시작하겠습니다.**"
            )
            # attempt_count를 0으로 리셋하여 다음 챕터에서 다시 사용 가능하도록 준비합니다.
            next_attempt_count = 0
        
        # 2. 🔑 [최종 출력 순서 재배치]
        # 2-1. 헤더 및 점수 (축하)
        header_and_score = (
            f"🎉 **작성 완료!** 이전 목차 **[{just_completed}]**의 정보 수집이 완료되었습니다. "
            f"(최종 점수: {completed_score}점)\n"
            f"----------------------------------------\n"
        )
        
        # 2-2. 상세 평가
        detail_breakdown = f"{breakdown_list_str}\n\n" if breakdown_list_str else ""
        
        # 2-3. 최종 메시지 구성
        completion_message = (
            header_and_score +
            detail_breakdown +
            final_action_message  # ⬅️ 통합된 메시지를 마지막에 배치
        )
        final_response_prefix = completion_message
        print(f"✅ 섹션 완료 메시지 생성: [{just_completed}] - 상세 평가 포함, attempt_count: {attempt_count} -> {next_attempt_count}")
    
    # 🔑 [핵심 수정] 최종 응답에 완료 메시지 prefix를 추가합니다.
    feedback_text = f" | 💡 {grading_reason}" if grading_reason else ""
    final_response = final_response_prefix + final_message_content
    
    # 6. --- 최종 응답 출력 및 반환 ---
    print(f"📤 응답 전송: {final_response[:100]}...")
    
    # 🔑 [핵심] 상태 업데이트: 완료 플래그를 반드시 초기화합니다.
    history = state.get("messages", [])
    history.append({"role": "assistant", "content": final_response})
    
    # 3. [상태 업데이트] attempt_count 업데이트 및 반환
    if just_completed:
        return {
            "current_query": final_response, # LangGraph의 END 노드로 전달될 최종 응답
            "messages": history,
            "section_just_completed": None, # ⬅️ 플래그 초기화
            "attempt_count": next_attempt_count, # ⬅️ 시도 횟수 업데이트
            "next_step": "ASK_USER" if not is_sufficient else "MANAGE_PROGRESSION"
        }
    else:
        # failure 시에는 attempt_count를 유지하여 재시도하도록 함
        return {
            "current_query": final_response, # LangGraph의 END 노드로 전달될 최종 응답
            "messages": history,
            "attempt_count": attempt_count,  # ⬅️ attempt_count 유지
            "next_step": "ASK_USER" if not is_sufficient else "MANAGE_PROGRESSION"
        }
