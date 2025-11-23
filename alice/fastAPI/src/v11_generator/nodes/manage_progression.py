from typing import Dict, Any, List
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
        # Note: 이 함수는 sufficiency=True일 때만 호출되어야 함
        return {} 

    # 1. 현재 완료된 섹션 정보 및 데이터
    current_item = toc[current_idx]
    current_number = current_item.get("number", "0")
    current_title = current_item.get("title", "제목 없음")
    current_data = state.get("collected_data", "")
    
    # 🔑 [핵심 1] 중복 저장 방지를 위한 검사
    # state에서 데이터를 가져와 List[str]로 강제 변환합니다.
    raw_data = state.get("accumulated_data")
    
    if isinstance(raw_data, str) or raw_data is None:
        # 이전에 잘못된 타입이 저장되었거나, None인 경우, 빈 리스트로 시작
        accumulated_data_list: List[str] = []
    else:
        # 올바른 List[str] 타입인 경우 그대로 사용
        accumulated_data_list: List[str] = raw_data
    
    # 요약 헤더가 이미 존재하는지 검사 (예: "### [1.1 사업 배경 및 필요성 요약]")
    header_check = f"### [{current_number} {current_title} 요약]"
    is_already_saved = any(header_check in content for content in accumulated_data_list)
    
    if is_already_saved:
        print(f"✅ 데이터 재처리 스킵: [{current_number} {current_title}]은 이미 최종 저장소에 저장되어 있습니다.")
        # 이미 저장되어 있다면, 요약/저장 과정을 건너뛰고 기존 리스트를 유지합니다.
        new_accumulated_list = accumulated_data_list
    
    else:
        # --- [최초 저장: 요약 및 압축 로직] ---
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
        
        # 요약된 내용을 List에 추가할 포맷을 만듭니다.
        summary_content = f"### [{current_number} {current_title} 요약]\n{summary_text}\n----------------------------------------"
        
        # 💡 [핵심 수정] 리스트 결합을 사용하여 데이터를 추가합니다.
        new_accumulated_list = accumulated_data_list + [summary_content]
        
        print(f"⚡ 데이터 압축 및 저장 완료: [{current_number} {current_title}]")
    
    
    # 2. [핵심 2] 다음 섹션 인덱스 업데이트 (중복 여부와 상관없이 다음으로 진행)
    next_idx = current_idx + 1 # 완료된 인덱스 다음 순서로 업데이트
    
    next_chapter_info = ""
    if next_idx < len(toc):
        next_chapter = toc[next_idx]
        next_chapter_info = next_chapter.get('title')
        # print 문은 실제 저장 여부와 상관없이 다음 인덱스 정보를 출력
        print(f"⏩ 섹션 인덱스 업데이트: [{current_title}] -> 다음 인덱스 [{next_chapter_info}]")
    
    # 🔑 [핵심 수정] 다음 노드(GENERATE_QUERY)에게 완료 정보를 전달
    just_completed_chapter = f"{current_number} {current_title}"
    
    if next_idx < len(toc):
        return {
            "current_chapter_index": next_idx,
            "target_chapter": next_chapter.get("title", "목표 없음"),
            # "accumulated_data": new_accumulated,
            "collected_data": "", # 다음 챕터를 위해 데이터 초기화
            "completeness_score": 0, # 다음 챕터 점수 초기화
            "next_step": "GENERATE_QUERY"
        }
    else:
        # 더 이상 하위 섹션이 없다면 모든 정보 수집 완료로 간주
        print("🎉 모든 섹션 완료: 최종 초안 생성 단계로 이동합니다.")
        return {
            "next_step": "FINISH_DRAFT", # (추후 generate_draft 노드로 연결)
            # "accumulated_data": new_accumulated,
            "collected_data": "", 
            "current_draft": f"최종 초안을 생성하기 위한 정보가 모두 수집되었습니다. 수집된 총 정보 길이: {len(new_accumulated)}자",
            "completeness_score": 100
        }
