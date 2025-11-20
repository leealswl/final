from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv
import json
import re

load_dotenv()

def assess_info(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [판사 노드]
    현재 목표 섹션(예: 1.1)의 정보 충족률(필요정보)을 평가합니다.
    70점 이상이면 다음 섹션으로 진행하도록 True를 반환합니다. (섹션 단위 진행 로직)
    """
    print("--- 노드 실행: assess_sufficiency (Section Scoring) ---")

    # [초기 방어벽 - LLM 초기화 에러만 방어]
    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception:
        # LLM 오류 시에도 일단 다음 노드로 이동하여 질문 생성은 시도 (또는 기본값 반환)
        return {"sufficiency": False, "completeness_score": 0, "grading_reason": "LLM 초기화 오류로 평가 불가", "next_step": "GENERATE_QUERY"}

    # 1. 데이터 확인 (수첩이 비었는지 확인)
    collected_data = state.get("collected_data", "")
    print(f"--- 📊 ASSESS_INFO 수신 데이터 길이: {len(collected_data)}자 ---")

    if not collected_data.strip():
        return {
            "sufficiency": False, "completeness_score": 0, "grading_reason": "아직 수집된 정보가 없습니다.",
            "missing_subsections": ["기초 아이디어"], "next_step": "GENERATE_QUERY"
        }

    # 2. 현재 목표 섹션 정보 설정 (단일 항목 추출)
    toc_structure = state.get("draft_toc_structure", [])
    current_idx = state.get("current_chapter_index", 0)
    
    # 목차 끝에 도달했거나 유효하지 않은 인덱스인 경우 완료 처리
    if not toc_structure or current_idx >= len(toc_structure):
        return {"sufficiency": True, "completeness_score": 100, "grading_reason": "모든 목차 항목 완료", "next_step": "FINISH"}

    current_section_item = toc_structure[current_idx]
    
    # 현재 목표 섹션의 정보만 추출
    current_number = current_section_item.get("number", "0")
    current_title = current_section_item.get("title", "제목 없음")
    current_desc = current_section_item.get("description", "설명 없음")

    # LLM이 채점할 목표 목록 (단일 항목 요청)
    scoring_targets = f"[{current_number} {current_title}] - {current_desc}" 

    # 4. 전략 가져오기
    fetched_context = state.get("fetched_context", {})
    anal_guide = str(fetched_context.get("anal_guide", "특별한 전략 없음."))

    # 5. [핵심] 단일 항목 채점 프롬프트 (JSON Only, 이스케이프 적용)
    JUDGE_PROMPT = """
    당신은 정부 지원사업 기획서의 **공정성 및 필요정보를 평가하는 전문 심사위원**입니다.
    **[수집된 정보]**를 바탕으로 **[공고문 전략]**과 **[현재 목표 항목]**을 분석하여, **해당 항목의 필요정보 충족률**을 **0~100점**으로 채점하세요.

    <평가 임무 및 기준>
    1. **평가 대상:** 오직 **[현재 목표 항목]** 하나뿐입니다.
    2. **필요정보 (충족) 기준:** 점수 **70점 이상**일 때, **다음 항목으로 진행**할 수 있는 충분한 정보가 수집된 것으로 판단합니다. (질문의 정보량을 평가하세요.)
    3. **채점 원칙:** 상태에 저장된 **기존 점수보다 낮은 점수를 절대 주지 마세요.**

    <채점 기준표 1: 공고문 핵심 전략>
    {anal_guide}
    (이 전략에 명시된 키워드(예: 글로벌, AI 기술 등)가 답변에 포함되어 있는지 확인하세요.)

    <현재 목표 항목 (단일 평가 대상)> 
    {scoring_targets} 
    
    <수집된 정보 (현재 섹션 관련 누적)>
    {collected_data}

    <출력 형식 (JSON Only)>
    **요구사항**: 반드시 [JSON 객체] 형태로 응답하세요.
    {{
        "number": "{current_number}",
        "title": "{current_title}",
        "score": (0~100점),
        "reason": "필요정보를 충족하는지에 대한 구체적인 평가 사유",
        "missing_points": ["부족한 구체적 정보 목록 (예: 정량적 목표 수치)"] 
    }}
    """
    
    # 6. LLM 호출 및 JSON 파싱
    
    # [변수 설명] LLM 호출 및 파싱에 필요한 변수들
    prompt = PromptTemplate.from_template(JUDGE_PROMPT)
    chain = prompt | llm
    
    response_text = chain.invoke({
        "anal_guide": anal_guide,
        "scoring_targets": scoring_targets,
        "collected_data": collected_data,
        # 🔑 프롬프트 템플릿에 사용된 모든 변수를 전달 (오류 해결)
        "current_number": current_number, 
        "current_title": current_title 
    }).content.strip()

    # 7. LLM 결과 통합 및 분석 (단일 객체 파싱)
    cleaned_json = re.sub(r"```json|```", "", response_text, flags=re.DOTALL).strip()
    
    try:
        parsed_score: Dict[str, Any] = json.loads(cleaned_json) 
    except json.JSONDecodeError as e:
        # LLM이 JSON 형식을 지키지 않았을 때
        print(f"❌ JSON 파싱 오류: {e}. Raw Text: {cleaned_json[:200]}")
        return {
            "sufficiency": False, 
            "completeness_score": 0, 
            "grading_reason": "평가 시스템 오류 (LLM이 JSON 형식을 지키지 않았습니다.)", 
            "missing_subsections": ["시스템 오류"], 
            "next_step": "GENERATE_QUERY"
        }
    
    # 8. 단일 항목 점수 계산 및 누적
    num = parsed_score.get("number", current_number)
    score = parsed_score.get("score", 0)
    missing = parsed_score.get("missing_points", [])

    final_section_scores = state.get("section_scores", {})
    previous_score = final_section_scores.get(num, 0)
    
    # 점수 하락 방지 (기존 점수와 새 점수 중 높은 값 선택)
    final_score_for_item = max(previous_score, score)
    final_section_scores[num] = final_score_for_item
    
    # 9. [핵심] 진행 여부 판단 (단일 섹션 70점 기준)
    is_sufficient = final_score_for_item >= 70
    
    # 10. 반환값 구성
    representative_score = final_score_for_item
    representative_reason = parsed_score.get("reason", "평가 사유 누락")
        
    print(f"✅ 평가 완료: [{current_number} {current_title}] 필요정보: {representative_score}%")

    return {
        "sufficiency": is_sufficient,
        "completeness_score": representative_score, # 이제 단일 섹션 점수
        "grading_reason": representative_reason,
        "missing_subsections": list(set(missing)), # 재질문을 위해 부족 항목 반환
        "section_scores": final_section_scores,
        "next_step": "GENERATE_QUERY"
    }