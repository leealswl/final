from ..state_types import ProposalGenerationState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def history_checker(state: ProposalGenerationState) -> ProposalGenerationState:
    print('history_checker 실행')

    HISTORY_PROMPT = """

        [목차 전체(TOC)]
        {toc_structure}

        [사용자 메시지]
        {user_prompt}

        [이미 충분히 작성된 목차 목록]
        {accumulated_data}

        당신은 '사업계획서 자동 생성 에이전트'이며, 현재 단계는
        "다음에 작성해야 할 목차를 정확하게 선택하는 단계"입니다.

        아래 규칙을 순차적으로 적용하여 단 하나의 목차만 선택하세요.

        ────────────────────────────────
        [다음 목차 선택 규칙]

        1. **사용자 직접 선택 우선 규칙**
        - 사용자 메시지({user_prompt})에 특정 목차명이 명시적으로 등장한다면,
            해당 목차를 최우선으로 선택합니다.
        - 부분 일치가 아닌, 의미적으로 명확한 일치를 기준으로 합니다.
        - 이때 사용자가 선택한 목차가 이미 작성 완료(accumulated_data)에 포함되어 있어도,
            사용자의 선택을 우선합니다.

        2. **작성 완료 제외 규칙**
        - 사용자가 특정 목차를 선택하지 않았다면,
            이미 충분히 작성된 목차({accumulated_data})는 모두 제외합니다.
        - 제외 후 남은 목차({toc_structure} - {accumulated_data})만 후보군으로 사용합니다.

        3. **논리적 순서 기반 규칙**
        - 후보군 중에서 다음 기준을 만족하는 목차를 선택합니다:
            a) 상위 단계의 목차 → 하위 단계의 목차 순
            b) 일반적 정보 → 구체적 정보 순
            c) 사업계획서의 자연스러운 작성 흐름을 따름
                (예: 개요 → 시장 분석 → 제품/서비스 → 비즈니스 모델 → 전략 → 실행 계획 → 재무 → 기대효과 등)

        4. **정보 공백 최소화 규칙**
        - 이미 작성된 정보(accumulated_data)와 사용자 메시지의 흐름을 고려하여,
            "전체 문서 완성도에 중요한 연결 역할을 하는 목차"를 우선 선택합니다.

        5. **단일 출력 규칙**
        - 최종적으로 선택된 목차명만 출력합니다.
        - 부가 설명, 메타 발화, 판단 근거는 절대 포함하지 않습니다.

        ────────────────────────────────
        [출력 형식]

        <선택된 목차명>

        (형식을 절대 변경하지 말 것)
        ────────────────────────────────

        """

    toc_structure = state.get("draft_toc_structure", [])
    # toc_structure = state['draft_toc_structure']
    print(1)
    user_prompt = state.get('user_prompt', "").strip()
    accumulated_data = state.get('accumulated_data', [])
   
    llm = ChatOpenAI( model="gpt-4o")

    prompt = PromptTemplate.from_template(HISTORY_PROMPT)
    chain = prompt | llm | StrOutputParser()

    
    # chain.invoke()의 결과는 이제 순수한 파싱된 스트링입니다.
    result = chain.invoke({
        'toc_structure': toc_structure,
        'user_prompt': user_prompt,
        'accumulated_data': accumulated_data
    })
    
    print('----------------')
    print('선택된 목차: ', result)
    print('-----------------')

    # 만약 accumulated_data가 문자열이면 리스트로 변환
    if isinstance(accumulated_data, str):
        accumulated_data = [accumulated_data]

    accumulated_data.append(result)

    print('accumulated_data: ', accumulated_data)

    return{ 'target_chapter': result,
           "accumulated_data": accumulated_data}
