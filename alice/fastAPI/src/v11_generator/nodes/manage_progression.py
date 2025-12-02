from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()

def manage_progression(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    [후처리 노드]
    초안 생성이 완료된 후 실행됩니다.
    1. 현재 챕터 내용을 요약하여 accumulated_data에 저장합니다.
    2. collected_data를 초기화하여 다음 챕터 작성을 준비합니다.
    3. 인덱스를 증가시킵니다.
    """
    print("--- 노드 실행: manage_progression (Post-Processing) ---")
    
    # 1. 기본 정보 추출
    current_idx = state.get("current_chapter_index", 0)
    toc = state.get("draft_toc_structure", [])
    collected_data = state.get("collected_data", "")
    
    # 예외 처리
    if current_idx >= len(toc):
        return {}

    current_item = toc[current_idx]
    current_number = current_item.get("number", "0")
    current_title = current_item.get("title", "제목 없음")
    
    # 2. 누적 데이터 가져오기
    raw_data = state.get("accumulated_data")
    accumulated_data_list: List[str] = []
    if isinstance(raw_data, list):
        accumulated_data_list = raw_data
    elif isinstance(raw_data, str):
        accumulated_data_list = [raw_data] if raw_data else []
    
    # 3. 요약 수행 (중복 확인)
    header_check = f"### [{current_number} {current_title} 요약]"
    is_already_saved = any(header_check in content for content in accumulated_data_list)
    
    new_accumulated_list = accumulated_data_list
    
    if not is_already_saved:
        print(f"⚡ [manage_progression] 요약 및 정리 시작: {current_title}")
        llm = None
        try:
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        except Exception as e:
            print(f"⚠️ LLM 초기화 오류: {e}")

        summary_text = collected_data
        if llm and collected_data.strip():
            SUMMARY_PROMPT = f"""
            당신은 기획서 요약 전문가입니다.
            아래 [대화 내용]에서 **[{current_title}]** 작성에 필요한 핵심 정보만 요약하세요.
            
            <대화 내용>
            {{current_data}}
            """
            try:
                prompt = PromptTemplate.from_template(SUMMARY_PROMPT)
                chain = prompt | llm
                summary_text = chain.invoke({"current_data": collected_data}).content.strip()
            except Exception as e:
                print(f"⚠️ 요약 오류: {e}")
        
        # 요약본 저장
        summary_content = f"### [{current_number} {current_title} 요약]\n{summary_text}\n----------------------------------------"
        new_accumulated_list = accumulated_data_list + [summary_content]
    
    # 4. 다음 단계 준비 (매우 중요!)
    # 초안 작성이 끝났으므로 데이터를 비우고 인덱스를 올립니다.
    next_idx = current_idx + 1
    
    print(f"✅ 섹션 완료 처리: [{current_title}] -> 다음 인덱스로 이동")
    
    return {
        "accumulated_data": new_accumulated_list,
        "collected_data": "",       # 🧹 데이터 비우기 (다음 챕터를 위해 필수)
        "current_chapter_index": next_idx, # ⏩ 인덱스 증가
        "sufficiency": False        # 상태 초기화
    }