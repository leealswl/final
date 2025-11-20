from .state_types2 import ProposalGenerationState
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
    pattern = r"\[질문 목록\](.*?)(?=\n\[|$)"
    match = re.search(pattern, result_text, re.DOTALL)

    if not match:
        return []

    question_block = match.group(1).strip()

    questions = []
    for line in question_block.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            questions.append(line[2:].strip())
    
    return questions


def load_data(state: ProposalGenerationState) -> ProposalGenerationState:
    print("노드 실행: load_data")

    # Checkpointer가 복원한 기존 히스토리
    history = state.get("messages", [])
    
    # 새 사용자 메시지 추가
    if state.get("user_prompt"):
        user_msg = {"role": "user", "content": state["user_prompt"]}
        history.append(user_msg)

    context_data = state.get("fetched_context", {})

    # 목차 구조 추출 및 정리
    result_toc = context_data.get('result_toc', {})
    toc_structure = result_toc.get("sections", [])

    anal_guide = context_data.get('anal_guide', [])
    generation_strategy = [
        item.get("writing_strategy")
        for item in anal_guide
        if "writing_strategy" in item
    ]

    print('generation_strategy: ', generation_strategy)

    # 기존 상태 유지하면서 필요한 것만 업데이트
    update = {
        'messages': history
    }
    
    # draft_toc_structure가 비어있을 때만 설정 (최초 1회)
    if not state.get("draft_toc_structure"):
        update["draft_toc_structure"] = toc_structure
    
    # guide가 비어있을 때만 설정 (최초 1회)
    if not state.get("guide"):
        update["guide"] = generation_strategy

    return update


def select_chapter(state: ProposalGenerationState) -> ProposalGenerationState:
    print("노드 실행: select_chapter")
    
    current_target = state.get("target_chapter", "")
    completed_chapters = state.get("completed_chapters", [])
    
    print(f"현재 선택된 목차: {current_target}")
    print(f"완료된 목차들: {completed_chapters}")
    
    # 💡 핵심 수정: 현재 목차가 있고, 아직 완료되지 않았으면 절대 바꾸지 않음
    if current_target and current_target not in completed_chapters and "NONE" not in current_target:
        print(f"🔒 목차 '{current_target}' 작업 진행 중 - 변경 안함")
        return {}  # 상태 변경 없음
    
    # 💡 새로운 목차 선택이 필요한 경우 (write 완료 후에만 실행됨)
    print("🔄 새로운 목차 선택 시작")
    
    select_chapter_template = '''
    당신은 사업계획서 작성 에이전트입니다.

    다음은 전체 목차 목록입니다:
    {chapter_data}

    다음은 이미 완료된 목차 목록입니다:
    {completed_chapters}

    다음은 사용자와의 질의응답 히스토리입니다:
    {history}

    현재까지 작성된 내용 또는 사용자와의 질의응답 히스토리를 고려하여,
    "다음에 작성해야 할 정확한 목차 한 개"를 선택하십시오.

    선택 기준은 다음과 같습니다:
    1. **완료된 목차는 절대 선택하지 않습니다.**
    2. 상위 → 하위 순서에 따라 작성 단계가 진행되어야 합니다.
    3. 아직 작성되지 않은 목차 중 가장 먼저 등장하는 항목을 선택합니다.

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
        'completed_chapters': completed_chapters,
        'history': state['messages']
    })

    print(f"🆕 새로 선택된 목차: {result}")

    return {'target_chapter': result}


def check_need_question(state: ProposalGenerationState) -> ProposalGenerationState:
    print("노드 실행: check_need_question")
    
    current_target = state.get("target_chapter", "")
    pending = state.get("pending_questions", [])
    answered = state.get("answered_questions", [])
    
    # 💡 남은 질문 계산
    remaining_questions = [q for q in pending if q not in answered]
    
    print(f"📊 질문 현황:")
    print(f"  - 전체 질문: {len(pending)}개")
    print(f"  - 답변 완료: {len(answered)}개")
    print(f"  - 남은 질문: {len(remaining_questions)}개")
    
    # 💡 케이스 1: 질문 목록이 이미 있고, 남은 질문이 있으면 계속 질문
    if pending and remaining_questions:
        print(f"✅ 기존 질문 목록 사용 (남은 질문: {len(remaining_questions)}개)")
        return {'sufficiency': False}
    
    # 💡 케이스 2: 모든 질문에 답변 완료 → write로 이동
    if pending and not remaining_questions:
        print(f"✅ 모든 질문 답변 완료 → write 노드로 이동")
        return {'sufficiency': True}
    
    # 💡 케이스 3: 질문 목록이 없음 → 새로 생성
    print("🔄 새로운 질문 목록 생성 시작")
    
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

    2. 부족한 정보가 있다면,  
    - 어떤 정보가 부족한지 분석하고  
    - 그 정보를 얻기 위해 구체적인 질문을 생성합니다.

    3. 필요한 정보가 이미 충분하다면  
    - 질문이 필요하지 않다고 판단합니다.

    출력 형식:

    [결론]
    ASK or NO_ASK

    [부족한 정보 분석]
    - 어떤 정보가 부족한지 또는 충분한지 설명

    [질문 목록]
    - 추가 질문이 필요한 경우: 질문 리스트를 bullet 형식으로 나열  
    - 질문이 필요하지 않다면: NONE
    '''

    check_prompt = ChatPromptTemplate.from_template(check_template)
    check_chain = check_prompt | llm | StrOutputParser()
    result = check_chain.invoke({
        'domain': state.get('domain', ''),
        'chapter': current_target,
        'history': state['messages']
    })

    print('check_need_question result: ', result)
    questions = parse_questions(result)
    print('추출된 질문들: ', questions)

    # ASK 판단 로직
    if "ASK" in result and "[결론]" in result:
        result_lines = result.split('\n')
        for i, line in enumerate(result_lines):
            if '[결론]' in line and i + 1 < len(result_lines):
                decision = result_lines[i + 1].strip()
                if decision == "ASK":
                    print(f"🔄 질문 필요 → {len(questions)}개 질문 생성")
                    return {
                        'sufficiency': False, 
                        'pending_questions': questions,
                        'answered_questions': []  # 초기화
                    }
    
    print("✅ 질문 불필요 → 바로 write로 이동")
    return {"sufficiency": True}


def router_ask_write(state: ProposalGenerationState) -> str:
    return 'write' if state.get('sufficiency') else "ask"


def question(state: ProposalGenerationState) -> ProposalGenerationState:
    print("노드 실행: question")

    history = state.get("messages", [])
    pending = state.get("pending_questions", [])
    answered = state.get("answered_questions", [])

    # 💡 아직 답변받지 않은 질문 필터링
    remaining_questions = [q for q in pending if q not in answered]

    if not remaining_questions:
        print("⚠️ 질문 목록이 비어있습니다!")
        return {'generated_text': "질문이 더 이상 없습니다."}

    print(f"📋 남은 질문 개수: {len(remaining_questions)}")

    question_template = '''
    [질문 목록]
    {question_list}

    [사용자와의 질의응답 히스토리]
    {history}

    당신은 '사업계획서 작성 보조 에이전트'입니다.

    ### 🔍 질문 선택 기준
    1. **이미 히스토리에서 질문되었거나 답변된 항목은 제외합니다.**
    2. **남은 질문 중 '현재 정보 흐름에서 가장 자연스럽게 이어지는 질문'을 선택합니다.**
    3. **질문은 반드시 '질문 목록에 있는 문장 그대로' 출력해야 합니다.**

    ### 출력 형식
    (선택된 질문 한 문장만 출력)
    '''

    question_prompt = ChatPromptTemplate.from_template(question_template)
    question_chain = question_prompt | llm | StrOutputParser()
    result = question_chain.invoke({
        'question_list': remaining_questions,
        'history': history
    })
    
    print('✅ 선택된 질문: ', result)

    # 히스토리에 질문 추가
    history.append({"role": "assistant", "content": result})
    
    # 💡 이 질문을 answered에 추가
    answered_copy = answered.copy()
    answered_copy.append(result.strip())

    return {
        'generated_text': result,
        'messages': history,
        'answered_questions': answered_copy
    }


def write(state: ProposalGenerationState) -> ProposalGenerationState:
    print("노드 실행: write")
    
    write_template = '''
    당신은 전문 사업계획서 작성 에이전트입니다.
    사용자가 제공한 정보를 기반으로 선택된 목차에 대한 사업계획서 본문을 작성해야 합니다.

    [사용자와의 질의응답 히스토리]
    {history}

    [도메인 지식]
    {domain}

    [작성할 목차]
    {chapter}

    [사업계획서 작성 가이드]
    {guide}

    작성 규칙:
    1. 선택된 목차의 목적에 정확히 부합하는 내용만 작성
    2. 질의응답 히스토리와 도메인 지식을 면밀히 분석
    3. 사업계획서 작성 가이드의 형식·톤·구조를 준수
    4. 전문가 톤 유지, 명확한 근거 및 논리 흐름

    최종 출력 형식:
    [본문]
    (해당 목차의 완성된 사업계획서 본문)
    '''

    write_prompt = ChatPromptTemplate.from_template(write_template)
    write_chain = write_prompt | llm | StrOutputParser()
    result = write_chain.invoke({
        'domain': state.get('domain', ''),
        'history': state['messages'],
        'chapter': state['target_chapter'],
        'guide': state['guide']
    })

    # 💡 작성 완료된 목차를 completed_chapters에 추가
    completed = state.get("completed_chapters", []).copy()
    current_chapter = state.get("target_chapter", "")
    
    if current_chapter and current_chapter not in completed and "NONE" not in current_chapter:
        completed.append(current_chapter)
    
    print(f"✅ 목차 '{current_chapter}' 작성 완료")
    print(f"📚 완료된 목차 목록: {completed}")

    return {
        'generated_text': result,
        'completed_chapters': completed,
        'pending_questions': [],  # 💡 다음 목차를 위해 초기화
        'answered_questions': []   # 💡 다음 목차를 위해 초기화
    }


def create_proposal_graph() -> StateGraph:
    """
    상태 지속성을 위한 그래프 생성
    (checkpointer는 FastAPI에서 AsyncSqliteSaver로 설정)
    """
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

    workflow.add_edge("write", END)
    workflow.add_edge("question", END)

    return workflow