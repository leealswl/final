from ..state_types import ProposalGenerationState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate

def history_checker(state: ProposalGenerationState) -> ProposalGenerationState:
    print('history_checker 실행')

    HISTORY_PROMPT = f"""
        [목차 전체]
        {toc_structure}

        [사용자 메시지]
        {user_prompt}

        [질문 완료, 충분히 작성된 목차]
        {accumulated_data}


        [다음 목차 결정 규칙]
        1. 사용자가 메시지에서 특정 목차를 명시적으로 선택했다면, 그 목차를 우선 선택합니다.
        2. 사용자가 선택하지 않았다면, 이미 질문을 받고 충분히 작성된 목차({accumulated_data})를 제외한 나머지 목차({toc_structure}) 중에서 다음 작성할 목차를 선택합니다.
        3. 다음 목차를 선택할 때는 논리적 흐름과 자연스러운 순서를 고려합니다.
        4. 선택된 목차를 출력 형식으로 명확히 표시합니다.

        [출력 형식 예시]
        <선택된 목차>
        """

    toc_structure = state.get("draft_toc_structure", [])
    print(1)
    user_prompt = state.get('user_prompt')
    accumulated_data = state.get('accumulated_data', [])

    llm = None
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")

    prompt = PromptTemplate.from_template(HISTORY_PROMPT)
    chain = prompt | llm

    result = chain.invoke({
        'toc_structure': toc_structure,
        'user_prompt': user_prompt,
        'accumulated_data': accumulated_data
        })
    
    print('선택된 목차: ', result)





    return{ 'target_chapter': result}