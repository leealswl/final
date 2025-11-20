# 목차(단락)을 관리 해주는 함수 
# 한락이 완성이 되면 그 완성됐다는 정보를 판사함수와 작성함수에게전달

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv

load_dotenv()

def manage_progression(state: ProposalGenerationState) -> Dict[str, Any]:
    print("--- 노드 실행: manage_progression (Section Progression) ---")
    
    is_sufficient = state.get("sufficiency", False)
    current_idx = state.get("current_chapter_index", 0)
    toc = state.get("draft_toc_structure", [])
    
    if not is_sufficient or current_idx >= len(toc):
        # 충분하지 않거나 목차 끝이면 진행 관리 노드가 호출될 일 없음 (방어적 코드)
        return {} 

    # 1. 이전 섹션 데이터 요약 및 누적
    
    # 현재 완료된 섹션 정보
    current_item = toc[current_idx]
    current_number = current_item.get("number", "0")
    current_title = current_item.get("title", "제목 없음")
    current_data = state.get("collected_data", "")
    
    llm = None
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")

    summary_text = current_data
    if llm and current_data.strip():
        SUMMARY_PROMPT = f"""
        당신은 기획서 요약 전문가입니다.
        아래 [대화 내용]에서 **[{current_title}]** 작성에 필요한 **핵심 정보(사실, 수치, 전략)**만 추출하여 요약하세요.
        잡담이나 불필요한 문장은 모두 제거하세요. 개조식으로 간결하게 작성하세요.
        
        작성이 완료된 목차는 
        <대화 내용>
        {{current_data}}
        """
        try:
            prompt = PromptTemplate.from_template(SUMMARY_PROMPT)
            chain = prompt | llm
            summary_result = chain.invoke({"current_data": current_data}).content.strip()
            summary_text = summary_result
            print(f"⚡ 데이터 압축 완료: {current_number} - {len(current_data)}자 -> {len(summary_text)}자")
        except Exception as e:
            print(f"⚠️ 요약 중 오류 발생: {e}")

    # 누적 데이터에 불러오기
    accumulated_data = state.get("accumulated_data", "")
    
    new_accumulated = f"{accumulated_data}\n\n### [{current_number} {current_title} 요약]\n{summary_text}\n----------------------------------------\n"
    
    # 2. [핵심] 다음 섹션 인덱스 찾기
# 4. 다음 챕터 계산
    
    # ------------------------------------------------------------------
    # 🔑 [핵심 수정] 현재 인덱스 이후의 첫 번째 '하위 섹션' (예: 1.2, 2.1)을 찾습니다.
    #    하위 섹션은 번호에 '.'이 포함되어 있습니다.
    # ------------------------------------------------------------------
    next_idx = -1
    
    # 현재 인덱스 다음부터 목차 끝까지 순회합니다.
    for i in range(current_idx + 1, len(toc)):
        item = toc[i]
        num = item.get("number", "")
        
        # 소수점('.')이 포함된 '하위 섹션'을 찾습니다. (예: 1.1, 1.2, 2.1)
        if '.' in num: 
            next_idx = i
            break
            
    # ------------------------------------------------------------------

    if next_idx != -1:
        next_chapter = toc[next_idx]
        print(f"⏩ 섹션 전환: [{current_title}] -> [{next_chapter.get('title')}]")
        
        return {
            "current_chapter_index": next_idx,
            "target_chapter": next_chapter.get("title", "목표 없음"),
            "accumulated_data": new_accumulated,
            "collected_data": "", # 다음 챕터를 위해 데이터 초기화
            "completeness_score": 0, # 다음 챕터 점수 초기화
            "next_step": "GENERATE_QUERY"
        }
    else:
        # 더 이상 하위 섹션이 없다면 모든 정보 수집 완료로 간주
        print("🎉 모든 섹션 완료: 최종 초안 생성 단계로 이동합니다.")
        return {
            "next_step": "FINISH_DRAFT", # (추후 generate_draft 노드로 연결)
            "accumulated_data": new_accumulated,
            "collected_data": "", 
            "current_draft": f"최종 초안을 생성하기 위한 정보가 모두 수집되었습니다. 수집된 총 정보 길이: {len(new_accumulated)}자",
            "completeness_score": 100
        }