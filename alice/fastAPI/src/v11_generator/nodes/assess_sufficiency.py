from typing import Dict, Any, List
from langchain_openai import ChatOpenAI 
from langchain_core.prompts import PromptTemplate 
from ..state_types import ProposalGenerationState
import re 

def assess_info(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [판사 노드] (최종 버전)
    수집된 정보를 기반으로 LLM이 80점 기준으로 평가하고 흐름을 결정합니다.
    """
    print("--- 노드 실행: assess_sufficiency (Section Scoring) ---")

    # 1. 'anal_guide' 변수 준비
    fetched_context = state.get("fetched_context", {})
    # 💡 draft_strategy에서 전략을 가져옴 (상태의 다른 필드를 참조할 경우 수정 필요)
    anal_guide = str(state.get("draft_strategy", "특별한 공고문 분석 전략 없음.")) 
    
    # 1. --- LLM 및 평가 프롬프트 정의 ---
    GRADING_PROMPT = """
        당신은 **최종 기획서 초안 생성 전문 검토관**입니다. 

        당신의 임무는 현재 수집된 정보가 지정된 목차 항목에 대해 **'초안 생성에 즉시 사용 가능한 수준'**인지 평가하는 것입니다.

        [목표 목차]
        번호: {chapter_number}
        제목: {chapter_title}
        요구 사항: {chapter_description}

        [수집된 정보]
        {collected_data}

        [공고문 핵심 전략 및 평가 기준]
        ⭐ {anal_guide} ⭐ 공고문의 핵심 전략이 수집된 정보에 충분히 반영되었는지 평가하세요.
        
        [평가 기준: '생성 적합성']
        1. **정량적 데이터 포함 여부:** (예: 연 매출 목표, 시장 규모, % 성장률 등) 구체적인 수치와 데이터가 포함되어 있는가? (기획서의 설득력을 높이는 핵심 요소)
        2. **논리적 연결성:** 수집된 정보가 목표 목차의 요구 사항을 논리적으로 뒷받침하며 최종 기획서에 그대로 활용될 수 있는가?
        3. **완료 기준:** 80점 이상이면 '초안 생성에 필요한 정보가 확보됨'으로 판단합니다. 80점 미만이면 추가적인, 더욱 구체적인 정보가 필요합니다.
        
        [출력 형식]
        - 점수는 반드시 <score> 태그 안에 숫자(정수)만 넣어주세요.
        - 점수를 매긴 이유와 부족한 부분을 <reason> 태그 안에 구체적으로 설명해주세요.
          (부족한 부분은 '정량적 목표 수치가 부족합니다', '경쟁 우위 요소가 불명확합니다'와 같이 구체적으로 명시)
        
        <score>점수</score>
        <reason>평가 이유 및 부족한 점 설명</reason>
        """
    
    llm = None
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")
    
    prompt = PromptTemplate.from_template(GRADING_PROMPT)
    # ---------------------------------------------

    # 2. 현재 목표 섹션 정보 설정 (history_checker의 결정 반영 로직)
    collected_data = state.get("collected_data", "")
    print(f"--- 📊 ASSESS_INFO 수신 데이터 길이: {len(collected_data)}자 ---")
    
    toc_structure = state.get("draft_toc_structure", [])
    target_title = state.get("target_chapter", "")
    current_idx = state.get("current_chapter_index", 0) 
    
    # 🔑 history_checker의 결정을 반영하여 current_idx를 덮어씁니다.
    found_idx = -1
    for i, item in enumerate(toc_structure):
        item_title = item.get("title", "")
        if item_title == target_title or target_title in item_title:
            found_idx = i
            break
            
    if found_idx != -1:
        current_idx = found_idx
    
    # 목차 끝에 도달했거나 유효하지 않은 인덱스인 경우 완료 처리
    if not toc_structure or current_idx >= len(toc_structure):
        return {"sufficiency": True, "completeness_score": 100, "grading_reason": "모든 목차 항목 완료", "next_step": "FINISH"}

    current_section_item = toc_structure[current_idx]
    current_number = current_section_item.get("number", "0")
    current_title = current_section_item.get("title", "제목 없음")
    current_description = current_section_item.get("description", "정보가 필요합니다.")



    # 3. --- 평가 LLM 호출 및 결과 파싱 ---
    if not collected_data.strip():
        # 데이터가 없으면 0점으로 처리 (LLM 호출 생략)
        final_score = 0
        grading_reason = "수집된 정보가 없어 평가를 수행할 수 없습니다."
    else:
        # 데이터가 있으면 LLM을 호출하여 정교하게 평가합니다.
        final_score = 0
        grading_reason = "시스템 오류로 평가 불가 (LLM 호출 실패)"
        
        if llm is None:
            print("❌ LLM이 초기화되지 않았습니다. 0점 처리.")
        else:
            print(f"--- 🧠 LLM 호출: [{current_number} {current_title}] 정교한 평가 시작 ---")
            chain = prompt | llm
            
            try:
                response_text = chain.invoke({
                    "chapter_number": current_number,
                    "chapter_title": current_title,
                    "chapter_description": current_description,
                    "collected_data": collected_data,
                    "anal_guide": anal_guide 
                }).content.strip()
                
                # 🔑 파싱 로직
                score_match = re.search(r"<score>\s*(\d+)\s*</score>", response_text, re.IGNORECASE)
                reason_match = re.search(r"<reason>\s*(.*?)\s*</reason>", response_text, re.IGNORECASE | re.DOTALL)
                
                final_score = int(score_match.group(1)) if score_match else 0
                grading_reason = reason_match.group(1).strip() if reason_match else "평가 이유 파싱 오류"
                
                print(f"📊 LLM 평가 결과: {final_score}점 - {grading_reason[:50]}...")
            except Exception as e:
                print(f"❌ LLM 호출/파싱 오류: {e}")
                
    # 4. --- 결과 반환 (80점 기준 분기 로직 구현 및 점수 영속화) ---
    is_sufficient = final_score >= 80 
    
    # 🔑 점수 영속화: section_scores에 현재 섹션 점수 저장
    section_scores = state.get("section_scores", {})
    section_scores[f"{current_number}"] = final_score
    
    print(f"✅ 평가 완료: [{current_number} {current_title}] 필요정보: {final_score}%")
    if is_sufficient:
        print(f"🎯 충분성 판단: 80점 이상 → MANAGE_PROGRESSION으로 분기")
    else:
        print(f"⚠️ 충분성 판단: 80점 미만 → GENERATE_QUERY로 분기")
    
    return {
        "sufficiency": is_sufficient,
        "completeness_score": final_score,  # 🔑 점수 영속화를 위해 상태에 저장
        "grading_reason": grading_reason,
        "missing_subsections": [],
        "current_chapter_index": current_idx, 
        "target_chapter": current_title,      
        "section_scores": section_scores,  # 🔑 업데이트된 점수 저장
        # 🔑 80점 이상이면 MANAGE_PROGRESSION, 아니면 GENERATE_QUERY
        "next_step": "MANAGE_PROGRESSION" if is_sufficient else "GENERATE_QUERY"
    }
