from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from ..state_types import ProposalGenerationState
from dotenv import load_dotenv
import json
import re

load_dotenv()

def assess_info(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [판사 노드 - 점수 누적 보장 모드]
    정보가 누적됨에 따라 점수가 '유지'되거나 '상승'할 뿐, 절대 떨어지지 않도록 보장합니다.
    """
    print("--- 노드 실행: assess_sufficiency (Accumulative Scoring) ---")

    try:
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
    except Exception:
        return {"sufficiency": False, "completeness_score": 0, "next_step": "GENERATE_QUERY"}

    # 1. 데이터 확인
    collected_data = state.get("collected_data", "")
    if not collected_data.strip():
        return {
            "sufficiency": False, 
            "completeness_score": 0,
            "grading_reason": "아직 수집된 정보가 없습니다.", # 👈 이유 저장
            "missing_subsections": ["기초 아이디어"],
            "next_step": "GENERATE_QUERY"
        }
    
    # 2. 목표 챕터 설정
    toc_structure = state.get("draft_toc_structure", [])
    current_idx = state.get("current_chapter_index", 0)
    
    target_number = "" 
    target_title = "제목 없음" # 빈 필드
    target_desc = ""
    
    # 데이터가 정상이면 빈필드에 진짜내용 채워넣음
    if toc_structure and current_idx < len(toc_structure):
            item = toc_structure[current_idx]
            target_number = item.get('number', '')
            target_title = item.get('title', '')
            target_desc = item.get('description', '')

    # 판사에게 "너는 지금 타겟만 채점해야 해"라고 알려줌
    target_info = f"[{target_number}] {target_title}\n(설명: {target_desc})"

    # 3. 전략 가져오기
    fetched_context = state.get("fetched_context", {})
    anal_guide = str(fetched_context.get("anal_guide", 
        "현재는 특별한 전략 없음. 일반적인 논리적 완결성만 평가할 것."))

    # 4. 채점 프롬프트
    JUDGE_PROMPT = """
    당신은 기획서 평가 위원입니다.
    **누적된 정보**가 **[공고문 전략]**과 **[목표 챕터]**를 얼마나 충족하는지 **0~100점**으로 채점하세요.

    <현재 목표 챕터 (채점 기준이 되는)>
    {target_info}

    <채점 기준표 1: 공고문 전략>
    {anal_guide}

    <채점 기준표 2: 목표 챕터>
    {target_info}

    <수집된 정보 (누적)>
    {collected_data}

    <채점 가이드>
    - 정보가 추가되었더라도 핵심 전략과 무관하면 점수를 올리지 마세요. (유지)
    - 기존에 충족된 내용이 있다면 점수를 깎지 마세요. (누적 평가)
    - 0~100점 사이 점수 부여.

    <출력 형식 (JSON Only)>
    {{
        "score": 60,
        "reason": "기본 내용은 충족되나, 전략에서 요구하는 '글로벌 진출' 내용이 없음.",
        "missing_points": ["글로벌 진출 전략"]
    }}
    """
    try:
            prompt = PromptTemplate.from_template(JUDGE_PROMPT)
            chain = prompt | llm
            response_text = chain.invoke({
                "anal_guide": anal_guide,
                "target_info": target_info,
                "collected_data": collected_data
            }).content.strip()

            cleaned_json = re.sub(r"```json|```", "", response_text).strip()
            result_json = json.loads(cleaned_json)
            
            # 1) LLM이 계산한 이번 턴 점수
            calculated_score = result_json.get("score", 0)
            reason = result_json.get("reason", "평가 내용 없음")
            missing_points = result_json.get("missing_points", [])

            # 2) 점수 하락 방지 로직 (Max Logic)
            # -------------------------------------------------------
            previous_score = state.get("completeness_score", 0)
            # 이전 점수와 이번 점수 중 높은 걸 선택
            final_score = max(previous_score, calculated_score)
            
            # 점수가 떨어질 뻔했다면 로그로 알려줌 (디버깅용)
            if calculated_score < previous_score:
                print(f"📉 점수 방어 발동! (LLM판정: {calculated_score} -> 유지: {final_score})")
            # -------------------------------------------------------

            print(f"📊 [{target_number} {target_title}] 최종 점수: {final_score}점 | 이유: {reason}")

            return {
                "sufficiency": final_score >= 85,
                "completeness_score": final_score,  # 방어된 최종 점수 저장
                "grading_reason": reason,           # 이유 저장
                "missing_subsections": missing_points,
                "next_step": "GENERATE_QUERY"
            }

    except Exception as e:
        print(f"⚠️ 채점 오류: {e}")
        # 에러 나도 이전 점수는 유지해줌
        prev_score = state.get("completeness_score", 0)
        return {
            "sufficiency": False, 
            "completeness_score": prev_score, 
            "grading_reason": "시스템 오류 발생", 
            "next_step": "GENERATE_QUERY"
        }