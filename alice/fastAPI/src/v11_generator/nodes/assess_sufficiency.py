# llm정보가 충분한지 판단함 질문을 더해야할지말지

import json
from typing import Dict, Any, List
# 🚨 Pydantic V2 호환성을 위해 BaseModel을 사용하고 LangChain V2 방식을 따릅니다.
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI # ChatOpenAI는 langchain_openai에서 임포트합니다.
from ..state_types import ProposalGenerationState
# (state_types.py 파일은 .state_types 로 상대 임포트가 되어야 합니다.)

# ----------------------------------------------------
# 1. Output Schema 정의 (TypedDict 대신 Pydantic BaseModel 사용)
# ----------------------------------------------------
class SufficiencyAssessment(BaseModel):
    is_sufficient: bool = Field(..., description="정보가 충분하면 True, 추가 질문이 필요하면 False를 결정하는 플래그")
    reasoning: str = Field(..., description="충분성 판단의 구체적인 근거.")
    # 🔑 is_sufficient=False일 경우, 부족한 하위 항목의 제목 리스트를 반드시 포함

    missing_subsections: List[str] = Field(..., 
    #이 리스트가 다음 질문의 명확한 목표가 됩니다.
        description="정보가 부족한 하위 항목(Sub-section)의 제목 리스트. 충분하면 빈 리스트."
    )
    #지금 모든항목을 만족하면 true 하나라도 만족못하면false

# ----------------------------------------------------
# 2. 충분성 판단을 위한 Prompt 정의 (draft_strategy 변수 추가)
# ----------------------------------------------------
PROMPT_TEMPLATE = """
당신은 기획서 작성 지원 에이전트의 핵심 판단 모듈입니다.
아래 '분석 전략'과 '하위 목차 목록'을 참조하여 사용자가 수집한 정보가 '목표 목차'를 완성하기에 충분한지 객관적으로 판단해야 합니다.

<판단 기준>
1. **분석 전략 준수:** 수집된 정보가 '{draft_strategy}' 전략에서 요구하는 핵심 강조점과 논리를 포함하는가?
# {draft_strategy}: anal.json 파일에서 추출된, 이 목차를 작성할 때 LLM이 강조해야 할 작성 전략 및 핵심 지침이 담긴 값
2. **하위 목차 충족:** 아래 **{target_chapter}**에 해당하는 하위 목차 목록의 내용을 충분히 서술할 수 있는가? (단답형이 아닌 구체적인 사례나 데이터가 포함되었는가?)
3. **루프 탈출 강제:** 더 이상 구체적인 후속 질문을 생성하기 어렵다면 (즉, 수집할 수 있는 정보가 한계에 도달했다면), 정보가 완벽하지 않더라도 True를 반환합니다.

<입력 정보>
- 목표 목차 (상위): {target_chapter}
# {target_chapter}: LangGraph State의 'target_chapter' 필드에 담긴 값. 현재 정보 수집의 목표가 되는 상위 목차 제목 (예: 1. 사업 개요)
- **하위 목차 목록 (작성 범위):** {subchapters_list}
# {subchapters_list}: 현재 목표 목차({target_chapter})에 포함된 하위 목차들의 리스트가 개행으로 담긴 값 (예: - 1.1 사업 배경 및 필요성\n- 1.2 사업 목표)
- 수집된 정보:
{collected_data}
# {collected_data}: ask_user_and_update_data.py 노드를 통해 누적된, 질문과 사용자 응답(Q&A) 쌍이 모두 담긴 값. 초안 작성의 유일한 근거 자료.

<요청 사항>
1. `is_sufficient` 필드에 판단 결과를 작성하세요.
2. `is_sufficient=False`일 경우, **하위 목차 목록** 중에서 **가장 정보가 부족한 항목의 제목**을 `missing_subsections` 필드에 리스트 형태로 반드시 채우십시오. (1개 이상)
3. JSON 형식으로만 응답하세요.
"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["target_chapter", "collected_data", "draft_strategy", "subchapters_list"], 
)

# ----------------------------------------------------
# 3. 노드 함수 정의
# ----------------------------------------------------
# 이 함수가 호출되면 챕터 의 충분성 판단 시작함
def assess_info(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    현재까지 수집된 정보를 평가하여 목차 작성이 가능한지 판단하고 상태를 업데이트합니다.
    """
    print("--- 노드 실행: assess_info ---")
    
    # State 필드 추출
    target_chapter = state.get("target_chapter", "미정 목차")
    collected_data = state.get("collected_data", "수집된 데이터 없음")
    # 🔑 draft_strategy 필드 추출 (anal.json 전략)
    draft_strategy = state.get("draft_strategy", "표준 기획서 작성 기준")
    
    # LLM Chain 정의: Pydantic V2 오류를 우회하는 with_structured_output 사용
    llm = ChatOpenAI(temperature=0.0, model="gpt-4o") 
    # 💡 Pydantic V2 호환성을 위해 with_structured_output 사용
    structured_llm = llm.with_structured_output(schema=SufficiencyAssessment)
    
    try:
        # 🔑 chain.invoke 호출 시 draft_strategy를 포함하여 전달
        assessment_result = structured_llm.invoke(
            prompt.format_prompt(
                target_chapter=target_chapter,
                collected_data=collected_data,
                draft_strategy=draft_strategy
            ).to_string()
        )
        # with_structured_output은 Pydantic 객체를 반환합니다.
        new_sufficiency = assessment_result.is_sufficient 
        llm_reasoning = assessment_result.reasoning
        
    except Exception as e:
        print(f"LLM 호출 중 오류 발생: {e}. 임시로 sufficiency=False 설정")
        new_sufficiency = False
        llm_reasoning = f"LLM 호출 오류: {e}"

    # State 업데이트
    print(f"판단 결과: {new_sufficiency}")

    return {
        "sufficiency": new_sufficiency,
        # 💡 [next_step]은 router_next_step 함수가 sufficiency 값을 보고 결정하므로, 
        # 여기서는 다음 라우터가 필요한 정보를 반환했다는 의미로 'ROUTER_DECISION'을 반환합니다.
        "next_step": "ROUTER_DECISION" 
    }