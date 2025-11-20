from ..state_types import ProposalGenerationState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
import re

def history_checker(state: ProposalGenerationState) -> ProposalGenerationState:
    print('history_checker 실행')

    toc_structure = state.get("draft_toc_structure", [])
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



    llm = None
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")

    prompt = PromptTemplate.from_template(HISTORY_PROMPT)
    # 💡 람다 함수를 이용한 초간편 파싱: LLM 응답 객체(x)를 받아서 원하는 스트링만 추출합니다.
    simple_parser = lambda x: (
        re.search(r"<선택된 목차>\s*(.*?)\s*</선택된 목차>|<선택된 목차>\s*(.*?)$", x.content, re.DOTALL)
        .group(1) or re.search(r"<선택된 목차>\s*(.*?)\s*</선택된 목차>|<선택된 목차>\s*(.*?)$", x.content, re.DOTALL).group(2)
    ).strip() if re.search(r"<선택된 목차>\s*(.*?)\s*</선택된 목차>|<선택된 목차>\s*(.*?)$", x.content, re.DOTALL) else x.content.strip()

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
    
    print('선택된 목차 (파싱 완료): ', parsed_chapter)

    # 🔑 핵심 수정: parsed_chapter를 기반으로 toc_structure에서 정확한 인덱스를 찾아서 업데이트합니다.
    found_idx = -1
    for i, item in enumerate(toc_structure):
        item_title = item.get("title", "")
        # 양방향 검사: LLM이 반환한 제목이 실제 제목과 일치하는지 확인
        # 예: parsed_chapter = "1.2 사업 목표", item_title = "사업 목표" → 매칭 성공
        if item_title == parsed_chapter or parsed_chapter == item_title:
            found_idx = i
            break
        # 부분 일치 검사: 양방향으로 확인
        elif parsed_chapter in item_title or item_title in parsed_chapter:
            found_idx = i
            break
        # 번호 제거 후 비교 (예: "1.2 사업 목표" → "사업 목표")
        else:
            number_match = re.search(r'^\d+\.?\d*\s*', parsed_chapter)
            if number_match:
                parsed_clean = parsed_chapter.replace(number_match.group(0), '').strip()
                if parsed_clean == item_title:
                    found_idx = i
                    break
    
    # 인덱스를 찾지 못한 경우, 기본값으로 유지하되 경고 출력
    if found_idx == -1:
        print(f"⚠️ 경고: '{parsed_chapter}'에 해당하는 목차를 toc_structure에서 찾을 수 없습니다. 기존 인덱스를 유지합니다.")
        current_idx = state.get("current_chapter_index", 0)
    else:
        current_idx = found_idx
        print(f"✅ 목차 인덱스 업데이트: '{parsed_chapter}' → 인덱스 {current_idx}")

    # 람다 함수를 썼기 때문에, parsed_chapter는 이미 최종 스트링입니다.
    return {
            'target_chapter': parsed_chapter, # ⬅️ LLM이 동적으로 결정한 목표 제목 (예: "사업 목표")
            'current_chapter_index': current_idx, # ⬅️ 찾은 인덱스로 상태 업데이트
            'next_step': "ASSESS_SUFFICIENCY" 
        }