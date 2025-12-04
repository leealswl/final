from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from ..state_types import ProposalGenerationState

def classify_user_intent(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    [라우터 노드]
    사용자의 입력이 '단순 정보 제공'인지 '수정/재작성 요청'인지 판단합니다.
    """
    print("--- 노드 실행: classify_intent (Router) ---")
    
    user_prompt = state.get("user_prompt", "")
    
    # 1. 분류 프롬프트 정의
    ROUTER_PROMPT = """
        당신은 '사업계획서 작성 시스템'의 **의도 분석기(Intent Classifier)**입니다.
        사용자의 입력이 시스템에 '새로운 정보를 제공(INFO)'하는 것인지, 아니면 '작성된 글을 수정(EDIT)'하려는 것인지 판단하십시오.

        ======================================================================
        🎯 [판단 기준: 행동의 대상(Target)이 무엇인가?]

        1. **INFO** (정보 제공 및 대화 진행)
        - **정의**: 사용자가 사업 아이디어, 전략, 시장 현황 등 **'콘텐츠 내용'**을 설명하거나, 질문에 대답하는 경우.
        - **핵심**: "세상, 시장, 사업, 전략"에 대한 이야기라면, 그 안에 '수정', '변경', '개선' 같은 단어가 있어도 무조건 INFO입니다.
        - **판단 예시**:
            * "기존 시장의 문제점을 **수정**하는 것이 목표야." -> (사업 내용이므로) -> **INFO**
            * "사업 모델을 B2B에서 B2C로 **변경**할 계획이야." -> (새로운 정보이므로) -> **INFO**
            * "응, 다음으로 넘어가자." -> **INFO**

        2. **EDIT** (작성물 수정 요청)
        - **정의**: 사용자가 **'AI가 작성한 텍스트/결과물'**을 마음에 들어하지 않거나, 다시 써달라고 **명령**하는 경우.
        - **핵심**: "글, 문단, 말투, 분량, 특정 표현"을 고치라는 지시여야 합니다.
        - **판단 예시**:
            * "방금 쓴 내용이 너무 길어. 좀 줄여서 **수정**해줘." -> (작성물에 대한 지시이므로) -> **EDIT**
            * "매출 목표 수치가 틀렸어. 10억으로 **변경**해." -> (작성된 글을 고치는 것이므로) -> **EDIT**
            * "다시 써줘." -> **EDIT**

        ======================================================================
        ⚠️ [주의: 함정 피하기]
        - 사용자가 "우리 회사는 세상을 **바꾸는** 기업입니다"라고 말했다면, 이것은 수정 요청이 아니라 **사업 소개(INFO)**입니다.
        - 단어 자체가 아니라 **"사용자가 AI에게 문서를 고치라고 시키는가?"**를 기준으로 판단하십시오.

        [사용자 입력 메시지]
        "{user_input}"

        [최종 출력]
        부가적인 설명 없이, 오직 "INFO" 또는 "EDIT" 라는 단어 하나만 출력하십시오.
        """
    
    # 2. 모델 초기화 (가성비 좋은 gpt-4o-mini 사용)
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        prompt = PromptTemplate.from_template(ROUTER_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        # 3. 의도 판단 실행
        intent = chain.invoke({"user_input": user_prompt}).strip().upper()
        
    except Exception as e:
        print(f"⚠️ 의도 분류 실패: {e}")
        # 오류 시 기본값은 안전하게 INFO(정보 제공)로 처리
        intent = "INFO"

    print(f"🔍 사용자 의도 판단 결과: {intent}")

    # 4. 판단 결과를 state에 저장 (라우팅용 필드 추가 필요)
    return {
        "user_intent": intent 
    }