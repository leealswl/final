from ..state_types import ProposalGenerationState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging
import json
import os
from pathlib import Path


def _extract_relevant_guide(guide_data: dict, chapter_number: str, chapter_title: str) -> str:
    """
    guide_claude.json에서 목차 번호/제목에 맞는 가이드를 추출합니다.

    Args:
        guide_data: 로드된 guide JSON 데이터
        chapter_number: 목차 번호 (예: "1", "2", "2.1")
        chapter_title: 목차 제목

    Returns:
        해당 목차에 대한 가이드 텍스트
    """
    try:
        # integrated_business_proposal_guide에서 섹션 찾기
        guide_root = guide_data.get("integrated_business_proposal_guide", {})

        # 목차 번호를 기반으로 섹션 키 매핑
        section_mapping = {
            "1": "section_01_basic_info",
            "2": "section_02_current_status",
            "3": "section_03_preparation_plan",
            "4": "section_04_goals_and_requirements",
            "5": "section_05_business_feasibility",
            "6": "section_06_budget",
            "7": "section_07_evaluation_criteria"
        }

        # 주요 섹션 번호 추출 (2.1 -> 2)
        main_section_num = chapter_number.split('.')[0] if '.' in chapter_number else chapter_number
        section_key = section_mapping.get(main_section_num)

        if section_key and section_key in guide_root:
            section_data = guide_root[section_key]

            # 가이드 텍스트 구성
            guide_text = f"## {section_data.get('section_name', '')}\n\n"

            # R&D 계획서 참조
            if 'rd_plan_reference' in section_data:
                guide_text += f"**R&D 참조**: {section_data['rd_plan_reference']}\n"

            # SW RFP 참조
            if 'sw_rfp_reference' in section_data:
                guide_text += f"**SW RFP 참조**: {section_data['sw_rfp_reference']}\n\n"

            # 주요 키워드
            if 'common_keywords' in section_data:
                guide_text += f"**핵심 키워드**: {', '.join(section_data['common_keywords'])}\n\n"

            # 나머지 섹션 데이터를 JSON으로 추가
            guide_text += "### 상세 가이드\n"
            guide_text += json.dumps(section_data, ensure_ascii=False, indent=2)

            return guide_text
        else:
            # 매칭되는 섹션이 없으면 일반 작성 팁 반환
            tips = guide_root.get("writing_tips_and_warnings", {}).get("common_tips", [])
            if tips:
                return f"일반 작성 지침:\n" + "\n".join(f"- {item}" for item in tips)
            else:
                return "해당 목차에 대한 가이드를 찾을 수 없습니다."

    except Exception as e:
        print(f"⚠️ 가이드 추출 오류: {e}")
        import traceback
        traceback.print_exc()
        return "가이드 정보를 추출할 수 없습니다."


def generate_proposal_draft(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    [작가 노드 - 비활성화 상태]
    현재는 초안 생성 로직을 주석 처리하여 실행되지 않도록 막아두었습니다.
    테스트 단계에서 오류를 방지하기 위해 더미(Dummy) 데이터를 반환합니다.
    """
    print("--- 노드 실행: generate_proposal_draft (현재 비활성화됨) ---")
    logging.info(f"📝 generate_draft 노드 실행 (Skipped)")

    DRAFT_PROMPT = """
        당신은 한국 정부 RFP(제안요청서)·입찰·지원사업 제안서 작성 전문가이며,
        실제 평가 심사위원이 읽는 수준으로 공식적이고 설득력 있는 문체를 사용합니다.

        ======================================================================
        📌 <입력 정보>
        1. 작성 대상 목차 (Target Section)
        - "{target_chapter_info}"

        2. 공고문 핵심 분석 요약 (Key Guidelines Summary)
        - "{anal_guide_summary}"

        3. 현재까지 수집된 사용자 정보 (Collected Data)
        - {collected_data}

        4. 최근 대화 히스토리 (Recent Chat History)
        - {recent_history}

        5. 제안서 작성 가이드 (Writing Guide Reference)
        - {guide_reference}
        ======================================================================

        ✍️ <작성 지침>
        - 위 다섯 가지 입력 정보를 모두 반영하여 **정부 제안서 공식 문체로 해당 목차의 완성된 단락**을 작성하십시오.
        - **제안서 작성 가이드**에 명시된 해당 목차의 작성 요령, 핵심 포인트, 필수 포함 내용을 반드시 준수하십시오.
        - 가이드에 제시된 표 형식, 측정 방법, 정량적 지표, 예시 등의 요구사항이 있다면 반드시 반영하십시오.
        - 문단 형식으로 작성하고, 개조식 나열이 필요한 경우 적절히 혼합하십시오.
        - 사용자가 제공한 정보가 불충분한 영역이 있어도 추론 가능한 범위 내에서 자연스럽게 보완하십시오.
        - 단순 요약이나 나열이 아닌 **논리적 구조(배경 → 필요성 → 목적 → 근거 → 기대효과 등)**로 설득력 있게 작성하십시오.
        - 공고문 요구사항과의 적합성을 명확하게 드러내십시오.
        - 평가위원이 읽을 때 **사업의 타당성, 실현 가능성, 공공성, 혁신성, 기대 성과**가 강조되도록 작성하십시오.
        - '우리는', '저희는' 같은 표현 대신 **기업명 또는 사업 주체를 3인칭으로 기술**하십시오.

        📌 <출력 형식>
        아래 형식을 반드시 준수하여 출력하십시오:
        ----------------------------------------------------------------------
        <작성된 제안서 본문>\n
        (여기에 최종 작성 문단을 넣으십시오)
        \n----------------------------------------------------------------------
        """
    
    # 1. guide_claude.json 로드
    guide_data = {}
    guide_reference = "가이드 정보를 불러올 수 없습니다."

    try:
        # 현재 파일 기준으로 guide 폴더 경로 찾기
        current_dir = Path(__file__).parent
        guide_path = current_dir.parent / "guide" / "guide_claude.json"

        if guide_path.exists():
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_data = json.load(f)
                print(f"✅ guide_claude.json 로드 성공: {guide_path}")
        else:
            print(f"⚠️ guide_claude.json 파일을 찾을 수 없습니다: {guide_path}")
    except Exception as e:
        print(f"⚠️ guide_claude.json 로드 오류: {e}")

    # 2. 현재 목표 섹션 정보 설정 (history_checker의 결정 반영 로직)
    collected_data = state.get("collected_data", "")
    # print('collected_data: ', collected_data)
    # print(f"--- 📊 ASSESS_INFO 수신 데이터 길이: {len(collected_data)}자 ---")

    toc_structure = state.get("draft_toc_structure", [])
    target_title = state.get("target_chapter", "")
    current_idx = state.get("current_chapter_index", 0)

    fetched_context = state.get("fetched_context", {})
    anal_guide_summary = str(fetched_context.get("anal_guide", "전략 정보 없음"))

    if toc_structure and current_idx < len(toc_structure):
        major_chapter_item = toc_structure[current_idx]
        major_chapter_number = major_chapter_item.get("number", "0")
        major_chapter_title = major_chapter_item.get("title", "제목 없음")

        # 2-1. LLM 프롬프트에 사용될 주 챕터 정보 구성
        chapter_display = f"{major_chapter_item.get('number')} {major_chapter_item.get('title')}"
        target_info_full = f"[{chapter_display}]\n설명: {major_chapter_item.get('description')}"

        print('target_info_full: ', target_info_full)

        # 2-2. 가이드에서 해당 목차에 맞는 섹션 찾기
        if guide_data:
            guide_reference = _extract_relevant_guide(guide_data, major_chapter_number, major_chapter_title)
            print(f"📚 추출된 가이드 길이: {len(guide_reference)}자")

    msgs = state.get("messages", [])
    recent_history = ""
    if msgs:
        for msg in msgs:
            role = "👤" if msg.get("role") == "user" else "🤖"
            content = msg.get("content", "")
            recent_history += f"{role}: {content}\n"


    prompt = PromptTemplate.from_template(DRAFT_PROMPT)

    llm = None
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")

    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        'target_chapter_info': target_info_full,
        'anal_guide_summary': anal_guide_summary,
        'collected_data': collected_data,
        'recent_history': recent_history,
        'guide_reference': guide_reference
        })
    
    # 만약 accumulated_data가 문자열이면 리스트로 변환
    accumulated_data = state.get('accumulated_data', [])
    if isinstance(accumulated_data, str):
        accumulated_data = [accumulated_data]

    accumulated_data.append(target_title)

    print('accumulated_data: ', accumulated_data)
    
    history = state.get("messages", [])
    history.append({"role": "assistant", "content": result})
    # 4. 상태 반환
    return {
        "current_query": result,
        "messages": history,
        "target_chapter": ""
    }