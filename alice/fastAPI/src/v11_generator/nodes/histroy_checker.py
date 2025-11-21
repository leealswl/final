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
    user_prompt = state.get('user_prompt')
    accumulated_data = state.get('accumulated_data', [])
    current_idx = state.get("current_chapter_index", 0)

    HISTORY_PROMPT = """
        당신은 기획서 작성 흐름을 **순차적으로 관리하는 전문 AI**이며, 데이터 무결성을 최우선으로 합니다.
        당신의 임무는 현재 상태를 보고 **다음으로 반드시 작성해야 할 목차**를 결정하는 것입니다.

        [목차 전체 목록]: {toc_structure}
        [완료된 항목]: {accumulated_data} 
        [사용자 메시지]: {user_prompt}
        
        ---
        
        [다음 목차 결정 규칙: 순차적 진행 절대 강제]
        
        1. ⭐ **최우선 규칙:** **{toc_structure}** 목록에서 **{accumulated_data}**에 포함되지 않은 (즉, 80점 이상으로 아직 완료되지 않은) 항목들 중 **가장 낮은 번호의 목차**를 선택해야 합니다.
        
        2. **사용자 메시지({user_prompt})가 이전에 완료된 목차(예: 1.1 사업 배경)와 관련된 내용을 담고 있더라도, 그 내용을 무시하고** 규칙 1의 순차적 흐름을 유지해야 합니다. 즉, 완료된 목차는 절대로 다시 선택할 수 없습니다.
        
        3. 선택된 목차를 출력 형식으로 명확히 표시합니다.
        
        [출력 형식 예시]
        <선택된 목차>1.2 사업 목표</선택된 목차>
        """



    llm = ChatOpenAI( model="gpt-4o")

    prompt = PromptTemplate.from_template(HISTORY_PROMPT)
    chain = prompt | llm | StrOutputParser()

    # 체인 구성: 프롬프트 -> LLM -> 람다 파서
    # LLM이 반환하는 객체(x)의 content 속성만 파서로 넘겨 최종 결과를 추출합니다.
    chain = prompt | llm | simple_parser 
    
    # chain.invoke()의 결과는 이제 순수한 파싱된 스트링입니다.
    parsed_chapter = chain.invoke({
        'toc_structure': toc_structure,
        'user_prompt': user_prompt,
        'accumulated_data': accumulated_data,
        'current_idx': current_idx  # 🔑 현재 인덱스 전달
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
