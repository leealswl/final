from ..state_types import ProposalGenerationState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from typing import List
import re
from langgraph.graph import StateGraph, END, START

llm = ChatOpenAI(model='gpt-4o-mini')


# 질문 목록 추출 함수
def parse_questions(result_text: str) -> List[str]:
    """
    LLM 출력(result_text)에서 [질문 목록] 블록만 추출하여
    bullet 형태 질문 리스트(List[str])로 변환
    """

    # 1) [질문 목록] 블록 추출
    pattern = r"\[질문 목록\](.*?)(?=\n\[|$)"
    match = re.search(pattern, result_text, re.DOTALL)

    if not match:
        return []

    question_block = match.group(1).strip()

    # 2) bullet('- ') 형태의 질문만 리스트로 추출
    questions = []
    for line in question_block.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            questions.append(line[2:].strip())  # "- " 제거
    
    return questions



def load_data(state: ProposalGenerationState) -> ProposalGenerationState:
    context_data = state.get("fetched_context", {})

     #목차 구조 추출 및 정리 ---
    result_toc = context_data.get('result_toc', {})
    toc_structure = result_toc.get("sections", [])

    anal_guide = context_data.get('anal_guide', {})
    generation_strategy = anal_guide.get(
        "writing_strategy", 
        "공고문 분석 전략이 없으므로, 목차를 작성하는 데 필요한 일반적인 정보를 수집합니다."
    )

    return {"draft_toc_structure": toc_structure, "guide": generation_strategy}

def select_chapter(state: ProposalGenerationState) -> ProposalGenerationState:
    select_chapter_template = '''
    당신은 사업계획서 작성 에이전트입니다.

    다음은 전체 목차 목록입니다:
    {chapter_data}

    다음은 사용자와의 질의응답 히스토리 입니다.
    {history}

    현재까지 작성된 내용 또는 사용자와의 질의응답 히스토리를 고려하여,
    "다음에 작성해야 할 정확한 목차 한 개"를 선택하십시오.

    선택 기준은 다음과 같습니다:
    1. 상위 → 하위 순서에 따라 작성 단계가 진행되어야 합니다.
    2. 이미 작성된 목차 또는 충분한 정보가 확보된 목차는 제외합니다.
    3. 아직 작성되지 않았거나 정보가 부족한 목차 중 가장 먼저 등장하는 항목을 선택합니다.
    4. 선택 이유를 간단히 설명합니다(내부 판단 로그이며, 최종 출력에는 포함하지 않을 수 있음).
    5. 최종적으로 반횐되는 값은 선택한 <목차이름>만 반환

    출력 형식은 아래 구조를 반드시 따르세요:

    [선택된 목차]
    <목차 이름>

    [선택 이유]
    <간단한 이유>

    만약 모든 목차 작성이 완료되었다고 판단되면:

    [선택된 목차]
    NONE

    [선택 이유]
    모든 목차가 작성 완료됨
    '''

    select_chapter_prompt = ChatPromptTemplate.from_template(select_chapter_template)
    select_chapter_chain = select_chapter_prompt | llm | StrOutputParser()
    result = select_chapter_chain.invoke({
        'chapter_data': state['draft_toc_structure'],
        'history': state['messages']})

    print(result)

    return {'target_chapter': result}

def check_need_question(state: ProposalGenerationState) -> ProposalGenerationState:
    check_template = '''
    당신은 사업계획서 작성 에이전트입니다.

    [선택된 목차]
    {chapter}

    [사용자와의 질의응답 히스토리]
    {history}

    [도메인 지식]
    {domain}

    당신의 목표는 위 정보를 기반으로,
    선택된 목차에 대한 본문을 작성하기 전에 
    "추가 질의가 필요한지 여부"를 정확히 판단하는 것입니다.

    판단 기준은 다음과 같습니다:

    1. 해당 목차를 작성하기 위해 필수 요소들이 충분히 확보되었는지 확인합니다.  
    (예: 목적, 필요성, 시장 분석 요소, 기술 정보, 사업 전략 등)

    2. 부족한 정보가 있다면,  
    - 어떤 정보가 부족한지 분석하고  
    - 그 정보를 얻기 위해 구체적인 질문을 생성합니다.

    3. 필요한 정보가 이미 충분하다면  
    - 질문이 필요하지 않다고 판단합니다.

    아래 출력 형식을 반드시 준수하세요.

    출력 형식:

    [결론]
    ASK or NO_ASK  
    - ASK: 추가 질문이 필요함  
    - NO_ASK: 질문 없이 본문 작성 가능

    [부족한 정보 분석]
    - (정보가 부족한 경우) 어떤 정보가 부족한지 명확히 설명  
    - (정보가 충분한 경우) 본문 작성이 가능한 이유를 설명

    [질문 목록]
    - 추가 질문이 필요한 경우: 질문 리스트를 bullet 형식으로 나열  
    - 질문이 필요하지 않다면: NONE

    예시:
    [결론]
    ASK

    [부족한 정보 분석]
    - 시장의 구체적인 타겟층이 정의되지 않음
    - 서비스 차별화 포인트가 충분히 명시되지 않음

    [질문 목록]
    - 귀사의 주요 타겟 고객층은 누구인가요?
    - 경쟁사와 비교했을 때 서비스의 차별화 포인트는 무엇인가요?
    '''

    check_prompt = ChatPromptTemplate.from_template(check_template)
    check_chain = check_prompt | llm | StrOutputParser()
    result = check_chain.invoke({
        'chapter': state['target_chapter'],
        'history': state['messages'],
        'domain': state['domain']})

    # questions = parse_questions(result)
    # state["pending_questions"] = questions

    # sufficiency 판단
    if "[결론]\nASK" in result:
        questions = parse_questions(result)
        return {'sufficiency': False, 'pending_questions': questions}
    else:
        return {"sufficiency": True}
    
def router_ask_write(state: ProposalGenerationState) -> str:
    return 'write' if state.get('sufficiency') else "ask"

def question(state: ProposalGenerationState) -> ProposalGenerationState:

    question_template = '''
    [질문 목록]
    {question_list}

    [사용자와의 질의응답 히스토리]
    {history}

    당신은 '사업계획서 작성 보조 에이전트'입니다.
    현재 질문 목록은 “해당 목차를 작성하기 위해 반드시 필요한 핵심 정보들”을 기반으로 이미 선별된 상태입니다.

    당신의 역할은 다음 기준에 따라 **이번에 사용자에게 해야 할 질문 하나를 선택하는 것**입니다.

    ### 🔍 질문 선택 기준
    1. **이미 히스토리에서 질문되었거나 답변된 항목은 제외합니다.**
    - 중복 질문 금지
    - 히스토리의 assistant → user 질문 내역을 반드시 반영할 것

    2. **남은 질문 중 ‘현재 정보 흐름에서 가장 자연스럽게 이어지는 질문’을 선택합니다.**
    - 논리적 순서(예: 목표 → 대상 → 전략 → 실행 → 성과 등)
    - 사용자에게 부담이 적고 구체화 단계로 들어가기 적합한 질문
    - 문맥상 선행되어야 하는 질문이 있다면 그것을 우선 선택

    3. **질문의 목적이 명확하도록 필요한 경우 표현을 약간 다듬을 수 있으나, 의미는 변경하지 않습니다.**

    ### 출력 형식
    아래 형식을 반드시 지키십시오.

    [선택된 질문]
    (여기에 선택된 질문을 한 문장만 넣기)
    '''

    question_prompt = ChatPromptTemplate.from_template(question_template)
    question_chain = question_prompt | llm | StrOutputParser()
    result = question_chain.invoke({
        'question_list': state['pending_questions'],
        'history': state['messages']})

    return {'current_query': result}


def write(state: ProposalGenerationState) -> ProposalGenerationState:
    write_template = '''
    당신은 전문 사업계획서 작성 에이전트입니다.
    사용자가 제공한 정보(질의응답 히스토리 + 도메인 지식 + 사업계획서 작성 가이드)를 기반으로
    선택된 목차에 대한 사업계획서 본문을 논리적으로 완성해야 합니다.

    ────────────────────────
    [사용자와의 질의응답 히스토리]
    {history}

    [도메인 지식]
    {domain}

    [작성할 목차]
    {chapter}

    [사업계획서 작성 가이드]
    {guide}
    ────────────────────────

    아래 작성 규칙을 반드시 따라야 합니다:

    1. **선택된 목차의 목적에 정확히 부합하는 내용만 작성**합니다.
    - 목차에서 요구하지 않은 내용은 절대 추가하지 않습니다.
    - 일반적이고 모호한 문장은 피하고, 제공된 정보 기반으로 구체적으로 작성합니다.

    2. **질의응답 히스토리와 도메인 지식을 면밀히 분석하여**
    - 이미 제공된 핵심 정보를 우선 반영하고
    - 누락된 정보가 있다면 추측으로 채우지 않고, 논리적 범위 내에서만 보완합니다.

    3. **사업계획서 작성 가이드의 형식·톤·구조를 완전히 준수**합니다.
    - 예: 목적 → 필요성 → 기대효과 / 문제 정의 → 해결방안 / 전략 → 실행계획 등
    - 문단 구성, 논리 흐름, 강조 포인트 등을 가이드에 맞게 반영합니다.

    4. 작성할 때는 다음을 보장합니다:
    - 전문가 톤 유지 (컨설턴트 또는 PM 수준)
    - 명확한 근거 및 논리 흐름
    - 사업적 설득력, 분석 기반의 서술
    - 불필요한 수식어·중복 표현 제거

    5. 최종 출력은 아래 형식만 사용합니다:
    ────────────────────────
    [본문]
    (해당 목차의 완성된 사업계획서 본문)
    ────────────────────────

    위 규칙을 철저히 따르고,
    현재 목차에 최적화된 사업계획서 본문을 아래에 작성하세요.

    [본문]
    '''

    write_prompt = ChatPromptTemplate.from_template(write_template)
    write_chain = write_prompt | llm | StrOutputParser()
    result = write_chain.invoke({
        'domain': state['domain'],
        'history': state['messages'],
        'chapter': state['target_chapter'],
        'guide': state['guide']})

    return {'current_query': result}

def create_proposal_graph() -> StateGraph:
    
    workflow = StateGraph(ProposalGenerationState)

    workflow.add_node("load_data", load_data)
    workflow.add_node("select_chapter", select_chapter)
    workflow.add_node("check_need_question", check_need_question)
    workflow.add_node("question", question)
    workflow.add_node("write", write)

    workflow.add_edge(START, "load_data")    
    workflow.add_edge("load_data", "select_chapter")
    workflow.add_edge("select_chapter", "check_need_question") 

    workflow.add_conditional_edges(
        "check_need_question",
        router_ask_write,
        {
            "write": "write",
            "ask": "question"
        }
    )


    workflow.add_edge("write", END) # 
    workflow.add_edge("question", END)

    
    return workflow