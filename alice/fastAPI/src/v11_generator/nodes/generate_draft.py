# 수집된 컨텍스트와 프롬프트를 결합하여 LLM을 통해 기획서 초안(서론 등)을 생성하는 노드 함수를 정의합니다.

# 파일: v11_generator.py (또는 노드 구현 파일)

from ..state_types import ProposalGenerationState
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI 
import logging

LLM_CLIENT = ChatOpenAI(temperature=0.3, model="gpt-4o") # LLM 클라이언트 가정

def generate_proposal_draft(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    수집된 정보(collected_data)와 목차 구조/분석 전략을 기반으로 기획서 초안을 생성합니다.
    """

    print("노드 실행: generate_proposal_draft")
    logging.info(f"📝 generate_draft 노드 실행 (시도: {state.get('attempt_count', 0) + 1})")
    
    # --- 1. 상태에서 필요한 정보 추출 ---
    
    # 📚 목차 구조 (작성할 내용의 뼈대)
    toc_structure = state.get("draft_toc_structure", [])

    print('toc_structure: ', toc_structure)
    toc_text = "\n".join([f"- {item.get('title', '제목 없음')}: {item.get('description', '설명 없음')}" 
                          for item in toc_structure])
    
    print('toc_text: ', toc_text)

    # 💡 분석 전략 (작성 톤 및 강조점)
    strategy = state.get("draft_strategy", "명확하고 논리적인 표준 보고서 형식으로 작성합니다.")
    
    # 💬 수집된 사용자 정보 (초안을 채울 데이터)
    collected_data = state.get("collected_data", "사용자로부터 충분한 정보를 수집하지 못했습니다.")
    
    # --- 2. LLM 호출을 위한 프롬프트 구성 ---
    
    # 수집된 정보가 'collected_data'에 모두 누적되어 있다고 가정합니다.
    DRAFT_PROMPT = f"""
    당신은 전문 제안서 작성자입니다. 다음의 [목표 목차], [분석 전략], [수집된 정보]를 종합하여
    완벽하게 문장이 연결되고 흐름이 자연스러운 **기획서 초안 전체 내용**을 Markdown 형식으로 작성하십시오.
    
    # 🎯 목표 목차 구조:
    {toc_text}
    
    # 💡 공고문 분석 전략:
    {strategy}
    
    # 💬 수집된 사용자 정보 (초안 작성의 근거):
    ---
    {collected_data}
    ---
    
    [요청 사항]
    1. 목차 순서대로 내용을 작성하되, 수집된 정보를 각 목차에 적절히 배치하고 상세하게 서술하십시오.
    2. 생성된 결과물은 **초안 내용 자체**만 포함해야 합니다.
    """
    
    # 3. LLM Chain 정의 및 실행
    prompt_template = PromptTemplate.from_template(DRAFT_PROMPT)
    chain = prompt_template | LLM_CLIENT
    
    try:
        draft_content = chain.invoke({}).content.strip()
    except Exception as e:
        draft_content = f"❌ 초안 생성 중 LLM 호출 오류 발생: {e}"
        logging.error(f"GENERATE_DRAFT LLM 호출 오류: {e}")

    # 4. 상태 업데이트
    return {
        "current_draft": draft_content,
        "generated_text": draft_content, # generated_text는 주로 최종 결과물 필드로 사용될 수 있음
        "attempt_count": state.get('attempt_count', 0) + 1,
        # 다음 단계는 초안을 검토하고 수정할지 결정하는 노드로 이동
        "next_step": "REVIEW_AND_DECIDE" 
    }