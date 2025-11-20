# 목차(단락)을 관리 해주는 매니저 함수 
# 한락이 완성이 되면 그 완성됐다는 정보를 판사함수와 작성함수에게전달

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()

def manage_progression(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [진행 관리자 노드]
    합격 시: 대화 내용 요약 -> 저장 -> 다음 챕터로 인덱스 이동 -> 상태 리셋
    """
    print("--- 노드 실행: manage_progression (Manager) ---")
    
    is_sufficient = state.get("sufficiency", False)
    current_idx = state.get("current_chapter_index", 0)
    toc = state.get("draft_toc_structure", [])
    
    # 1. 합격 안 했으면 아무것도 안 함
    if not is_sufficient:
        return {}

    # -------------------------------------------------------
    # [기능 1] 대화 내용 요약 (Summarize)
    # -------------------------------------------------------
    current_data = state.get("collected_data", "")
    summary_text = current_data # 기본값

    if current_data.strip():
        try:
            llm = ChatOpenAI(temperature=0, model="gpt-4o")
            SUMMARY_PROMPT = """
            아래 대화 내용을 기획서 작성용으로 간략히 요약하세요.
            (사실, 수치, 결정된 전략 위주로)
            
            대화: {text}
            """
            chain = PromptTemplate.from_template(SUMMARY_PROMPT) | llm
            summary_text = chain.invoke({"text": current_data}).content.strip()
            print(f"⚡ 데이터 요약 완료: {len(current_data)}자 -> {len(summary_text)}자")
        except Exception as e:
            print(f"⚠️ 요약 실패(원본 저장): {e}")

    # -------------------------------------------------------
    # [기능 2] 창고에 저장 (Archive)
    # -------------------------------------------------------
    accumulated = state.get("accumulated_data", "")
    
    # 현재 챕터 제목 찾기
    chapter_title = "챕터"
    if current_idx < len(toc):
        chapter_title = toc[current_idx].get("title", "제목없음")
        
    # 예쁘게 포장해서 누적
    new_accumulated = f"{accumulated}\n\n### [{current_idx + 1}. {chapter_title} 요약]\n{summary_text}\n--------------------\n"
    
    # -------------------------------------------------------
    # [기능 3] 다음 페이지로 이동 (Next Chapter)
    # -------------------------------------------------------
    next_idx = current_idx + 1
    
    if next_idx < len(toc):
        next_chapter = toc[next_idx]
        print(f"⏩ 챕터 전환! [{chapter_title}] -> [{next_chapter.get('title')}]")
        
        return {
            "current_chapter_index": next_idx,   # 페이지 넘김
            "accumulated_data": new_accumulated, # 창고 저장
            "collected_data": "",                # 수첩 비우기 (중요!)
            "completeness_score": 0,             # 점수 리셋
            "grading_reason": "",                # 이유 리셋
            "sufficiency": False                 # 다시 불합격 상태로
        }
    else:
        print("🎉 모든 챕터 완료!")
        return {
            "accumulated_data": new_accumulated,
            "next_step": "FINISH"
        }