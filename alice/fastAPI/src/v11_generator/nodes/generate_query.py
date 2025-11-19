from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI # ChatOpenAI는 langchain_openai에서 임포트
from ..state_types import ProposalGenerationState 

# ----------------------------------------------------
# 1. 상세 질문 생성을 위한 Prompt 정의 (일반 루틴)
# ----------------------------------------------------

def generate_query(state: ProposalGenerationState) -> Dict[str, Any]: 
    print("--- 노드 실행: generate_query (순차 진행 안내 강화) ---")

    # State에서 정보 추출
    history = state.get("messages", []) 
    collected_data = state.get("collected_data", "")
    draft_strategy = state.get("draft_strategy", "목차 내용 채우기에 집중")
    user_prompt = state.get("user_prompt")
    
    # 🔑 [핵심] 최초 턴 확인 (collected_data가 비어있다면 최초 턴으로 간주)
    is_first_turn = not collected_data
    
    # 🔑 [컨텍스트 추출] (fetch_context에서 추출되었다고 가정-패치컨텍스트에서 이 필드 쓸거임)
    major_chapters = state.get("major_chapter_titles", []) # [추후연결] major_chapter_titles 필드 사용
    target_subchapters = state.get("target_subchapters", []) # [추후연결] target_subchapters 필드 사용
    missing_subsections = state.get("missing_subsections", []) # [추후연결] missing_subsections 필드 사용
    
    # LLM Chain 정의 (재사용)
    llm = ChatOpenAI(temperature=0.3, model="gpt-4o") 
    
    # if (Case 1)	없음 (Empty)	없음 (Empty)	최초 턴. 이제 막 대화를 시작하는 시점입니다.
    # elif (Case 2)	있음 (Present)	있음 (Present)	표준 루프. 정보가 누적되었지만, 여전히 부족한 항목이 남아 다음 질문이 필요한 상태입니다.
    # else (Case 3)	있음 (Present)	없음 (Empty)	루프 종료. 충분한 정보가 누적되었고, assess_sufficiency.py가 모든 요구사항이 충족되었다고 판단한 상태입니다.
            
    if is_first_turn and major_chapters and target_subchapters:
        # -----------------------------------------------------------------
        # 🔑 CASE 1: 최초 턴 (collected_data와 missing_subsections가 비어있을 때)
        # -----------------------------------------------------------------
        
        # 첫 번째 하위 항목의 정보 추출 (1.1)
        first_subsection_title = target_subchapters[0].get('title')
        criteria_list = target_subchapters[0].get('description')
        first_subsection_criteria = criteria_list[0]
        # target_subchapters가 현재 작업할 하위 목차를 순서대로 담고 있고,
        # 그중 **가장 먼저 할 일([0])**의 요구사항을 추출하여 질문의 근거로 사용하는 것
  
        FIRST_TURN_PROMPT = f"""
        당신은 기획서 작성을 돕는 AI 도우미입니다. 사용자와의 첫 대화임을 인식하고, 기획서 작성을 시작할 것을 제의하십시오.
        
        <요청 사항>
        1. 사용자에게 환영 인사와 함께 기획서 작성을 바로 시작할 것을 제안하십시오.
        2. 기획서의 **첫 번째 주요 목차인 '{major_chapters[0]}'**부터 시작함을 명시하십시오.
        3. 곧바로 **첫 번째 하위 항목인 '{first_subsection_title}'**에 대한 **핵심 질문**을 던지십시오.
        4. 이 질문은 **'{first_subsection_criteria}'** 내용을 바탕으로 사용자에게 구체적인 답변을 요구해야 합니다.
        5. **질문 내용만을 출력하십시오.** (예: "저희가 첫 번째 목차인 1. 사업 개요부터 시작합니다. 1.1 사업 배경 및 필요성에 대한 귀사의 핵심 비전을 구체적인 사례와 함께 말씀해 주시겠어요?")
        """
        prompt_template = PromptTemplate.from_template(FIRST_TURN_PROMPT)
        generated_query = (prompt_template | llm).invoke({}).content.strip()
        
    elif missing_subsections:
        # -----------------------------------------------------------------
        # 🔑 CASE 2: 일반 루틴 (collected_data가 있고, 부족한 항목이 있을 때)
        # -----------------------------------------------------------------

        # 다음 목표 섹션 제목을 추출합니다. (순서상 가장 먼저 오는 항목)
        next_target_subsection_title = missing_subsections[0]
        
        # LLM Chain에 전달할 변수 구성
        missing_subsections_list = ", ".join(missing_subsections) 
        subchapters_criteria = "\n".join([
            f"- {s.get('title', '제목 없음')}: {s.get('criteria', ['세부 설명 없음'])[0]}" for s in target_subchapters
        ])
        # 조인함수 쓰는데 왜쓰는진 모름
        
        PROMPT_TEMPLATE = f"""
        당신은 공고문 분석 기반의 '기획서 작성 에이전트'입니다. 현재 기획서 작성이 **목차 순서에 따라 순차적으로 진행** 중임을 사용자에게 명확히 알리고 다음 질문을 생성해야 합니다.

        <현재 목표 설정>
        현재 작성 목표는 **'{next_target_subsection_title}'**입니다.

        <입력 정보>
        - **현재까지 수집된 정보:** {collected_data}
        - **가장 부족한 하위 항목 목록 (다음 질문의 목표):** {missing_subsections_list}
        - **하위 항목별 상세 질문 기준:**
        {subchapters_criteria}
        
        <요청 사항 - 확실한 아웃풋 강제>
        1. 질문의 시작은 **'자, 그럼 이제 {next_target_subsection_title}을 작성할 차례입니다.'** 와 같은 안내 문구로 시작하십시오.
        2. **[질문 생성]** 선택된 항목({next_target_subsection_title})에 해당하는 **Description** 내용을 기반으로, 사용자에게 **정량적 데이터 또는 구체적인 사례**를 요구하는 **명확한 질문 하나**를 생성하십시오.
        3. 이미 {collected_data}에 있는 내용과 겹치지 않도록 질문을 다듬으십시오.
        4. **생성된 안내 문구와 질문 내용만을 출력하십시오.** (다른 설명, 서론, 결론 없이 오직 안내+질문 자체만 출력)
        """
        
        prompt_template = PromptTemplate.from_template(PROMPT_TEMPLATE)
        generated_query = (prompt_template | llm).invoke({
            "collected_data": collected_data,
            "missing_subsections_list": missing_subsections_list, 
            "subchapters_criteria": subchapters_criteria,         
            "draft_strategy": draft_strategy,
            "user_prompt": user_prompt, # 대화 흐름 유지를 위해 전달
            "messages": history
        }).content.strip()

    else:
        # -----------------------------------------------------------------
        # 🔑 CASE 3: 예외 (모든 정보가 충분하거나 초기 컨텍스트 추출 오류)
        # -----------------------------------------------------------------
        generated_query = "현재 목표 목차에 대한 모든 정보 수집이 완료되었습니다. 다음 챕터로 넘어가거나, 현재까지의 내용을 바탕으로 초안을 생성해달라고 요청해 주세요."

    # ... (history 업데이트 및 State 반환 로직은 유지) ...

    return {
        "current_query": generated_query,
        "next_step": "ASK_USER", # LangGraph의 실행을 일시 정지하고 사용자에게 질문을 던집니다.
        "messages": history
    }