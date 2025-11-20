# 초안을 작성해주는 작가 함수

from ..state_types import ProposalGenerationState
from typing import Dict, Any
# from langchain_core.prompts import PromptTemplate  # [주석 처리]
# from langchain_openai import ChatOpenAI            # [주석 처리]
import logging
# import json                                        # [주석 처리]

# [주석 처리] 고급 추론을 위해 GPT-4o 사용 권장
# LLM_CLIENT = ChatOpenAI(temperature=0.3, model="gpt-4o")

def generate_proposal_draft(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [작가 노드 - 비활성화 상태]
    현재는 초안 생성 로직을 주석 처리하여 실행되지 않도록 막아두었습니다.
    테스트 단계에서 오류를 방지하기 위해 더미(Dummy) 데이터를 반환합니다.
    """
    print("--- 노드 실행: generate_proposal_draft (현재 비활성화됨) ---")
    logging.info(f"📝 generate_draft 노드 실행 (Skipped)")
    
    # -------------------------------------------------------------------------
    # [주석 처리 시작] - 나중에 활성화 시 아래 주석을 해제하세요.
    # -------------------------------------------------------------------------
    # # 1. 입력 데이터 준비
    # # (1) 대화 기록 (User Domain Knowledge)
    # collected_data = state.get("collected_data", "")
    # accumulated_data = state.get("accumulated_data", "")
    # full_user_context = f"{accumulated_data}\n{collected_data}"
    # if len(full_user_context) < 10:
    #     full_user_context = "사용자로부터 수집된 구체적인 정보가 부족합니다. 일반적인 내용을 바탕으로 작성해주세요."

    # # (2) 공고문 분석 데이터 (Guide & Strategy)
    # # state['fetched_context']에 anal.json 내용이 있다고 가정
    # fetched_context = state.get("fetched_context", {})
    # # anal_guide가 리스트 형태라면 현재 챕터와 관련된 전략을 찾아야 함 (여기서는 전체를 문자열로 요약 가정)
    # # 실제로는 anal.json 구조에 맞춰 필터링 로직이 필요할 수 있습니다.
    # anal_guide_summary = "공고문에서 요구하는 '혁신성'과 '글로벌 진출 가능성'을 강조해야 합니다." 
    # 
    # # (3) 작성 목표 (Current Chapter)
    # target_chapter = state.get("target_chapter", "전체 기획서")
    # toc_structure = state.get("draft_toc_structure", [])
    # 
    # # 현재 작성해야 할 챕터의 하위 목차 상세 정보 구성
    # current_toc_detail = ""
    # current_idx = state.get("current_chapter_index", 0)
    # if toc_structure and current_idx < len(toc_structure):
    #     section = toc_structure[current_idx]
    #     current_toc_detail = f"챕터명: {section.get('title')}\n설명: {section.get('description')}"

    # # 2. proposal.py 스타일의 강력한 프롬프트 정의
    # SYSTEM_PROMPT = """
    # 당신은 정부 지원사업 제안서(RFP) 작성 전문 컨설턴트입니다.
    # 주어진 [공고문 가이드], [사용자 인터뷰 내용], [작성 목표]를 완벽하게 숙지하고,
    # 평가위원이 높은 점수를 줄 수밖에 없는 **전문적이고 논리적인 제안서 초안**을 작성하세요.

    # <작성 원칙>
    # 1. **두괄식 작성**: 핵심 주장을 문단 처음에 배치하십시오.
    # 2. **근거 제시**: 사용자의 인터뷰 내용에 있는 구체적 수치나 사실을 반드시 포함하십시오.
    # 3. **가이드 준수**: 공고문 분석 전략에서 강조하는 키워드(예: 글로벌, 혁신 등)를 녹여내십시오.
    # 4. **명확한 어조**: "~할 것임", "~로 사료됨" 보다는 "~함", "~를 추진함" 등의 개조식 혹은 명확한 해요체를 사용하십시오. (Markdown 포맷 사용)
    # """

    # USER_PROMPT_TEMPLATE = """
    # 아래 정보를 바탕으로 **[{target_chapter}]** 챕터의 초안을 작성해 주세요.

    # ### 1. 공고문 분석 및 작성 전략 (Guide)
    # {anal_guide_summary}

    # ### 2. 사용자 인터뷰 내용 (Domain Context)
    # {full_user_context}

    # ### 3. 작성 목표 (Target Section)
    # {current_toc_detail}

    # ---
    # **[요청사항]**
    # - 위 내용을 바탕으로 해당 챕터에 들어갈 본문을 작성하세요.
    # - 소제목(##)을 적절히 활용하여 가독성을 높이세요.
    # - 내용은 너무 짧지 않게, 전문적인 비즈니스 용어를 사용하여 풍성하게 작성하세요.
    # """

    # prompt = PromptTemplate(
    #     template=SYSTEM_PROMPT + "\n\n" + USER_PROMPT_TEMPLATE,
    #     input_variables=["target_chapter", "anal_guide_summary", "full_user_context", "current_toc_detail"]
    # )

    # # 3. LLM 실행
    # chain = prompt | LLM_CLIENT
    # 
    # try:
    #     response = chain.invoke({
    #         "target_chapter": target_chapter,
    #         "anal_guide_summary": anal_guide_summary,
    #         "full_user_context": full_user_context,
    #         "current_toc_detail": current_toc_detail
    #     })
    #     draft_content = response.content.strip()
    #     print(f"✅ [{target_chapter}] 초안 생성 완료")

    # except Exception as e:
    #     draft_content = f"❌ 초안 생성 중 오류 발생: {e}"
    #     logging.error(f"GENERATE_DRAFT 오류: {e}")
    # -------------------------------------------------------------------------
    # [주석 처리 끝]
    # -------------------------------------------------------------------------

    # 임시 반환값 (오류 방지용)
    draft_content = "(현재 초안 생성 기능은 비활성화되어 있습니다.)"

    # 4. 상태 반환
    return {
        "current_draft": draft_content,
        "generated_text": draft_content,
        # 다음 스텝은 사용자가 검토하거나, 다음 챕터로 넘어가는 로직으로 연결됨
        "next_step": "REVIEW_OR_NEXT" 
    }