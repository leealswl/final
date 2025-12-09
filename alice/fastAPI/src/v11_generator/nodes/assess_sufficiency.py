from typing import Dict, Any, List
# from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate 
from ..state_types import ProposalGenerationState
import re 
import json # ⬅️ JSON 파싱을 위해 추가 


def assess_info(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [판사 노드] (최종 버전)
    수집된 정보를 기반으로 LLM이 80점 기준으로 평가하고 흐름을 결정합니다.
    """
    print("--- 노드 실행: assess_sufficiency (Section Scoring) ---")

    # 1. 'anal_guide' 변수 준비
    # fetched_context = state.get("fetched_context", {})
    # 💡 draft_strategy에서 전략을 가져옴 (상태의 다른 필드를 참조할 경우 수정 필요)
    anal_guide = str(state.get("draft_strategy", "특별한 공고문 분석 전략 없음.")) 
    
    # 1. --- LLM 및 평가 프롬프트 정의 ---
    # 
    GRADING_PROMPT = """
        당신은 **최종 기획서 초안 생성 전문 검토관**입니다. 

        당신의 최우선 임무는 수집된 정보가 **'지정된 목차의 요구사항(Description)'을 얼마나 충실히 만족하는지** 평가하는 것입니다.
        공고문 전략은 참고 사항이며, 목차 설명에 부합하는 구체적인 내용이 있는지가 합격의 기준입니다.

        [목표 목차 정보]
        - 번호: {chapter_number}
        - 제목: {chapter_title}
        - 📌 **핵심 요구 사항(Description):** {chapter_description}

        [참고: 공고문 전략]
        - {anal_guide} (※ 위 내용은 방향성 참고용이며, 평가의 절대 기준은 아닙니다.)

        [수집된 정보]
        {collected_data}
        
        [평가 기준: '목차 적합성 및 초안 생성 가능성']
        다음 3가지 기준에 따라 평가하십시오. (80점 이상 합격)

        1. **목차 요구사항 충족도 (RATER_1):** - 수집된 정보가 위 **'핵심 요구 사항(Description)'**이 지시하는 내용을 빠짐없이 다루고 있는가?
           - 목차 설명과 무관한 정보가 아닌, 해당 단락 작성에 꼭 필요한 핵심 재료인가?

        2. **정보의 구체성 및 정량화 (RATER_2):** - 두루뭉술한 서술이 아닌, 구체적인 수치(매출액, 인원, 기간 등)나 명확한 고유명사(기관명, 솔루션명 등)가 포함되었는가?
           - 목차 설명에서 표나 차트를 요구할 경우, 이를 구성할 데이터가 존재하는가?

        3. **초안 작성 가능성 (RATER_3):**
           - 추가적인 질문 없이, 현재 정보만으로 즉시 완성된 수준의 초안 문단을 작성할 수 있는가?
           - 논리적 비약 없이 문장을 구성할 수 있을 만큼 정보가 충분한가?
        
        [출력 형식]
        - 최종 점수(3가지 항목 점수의 평균)는 반드시 <score> 태그 안에 숫자(정수)만 넣어주세요.
        - 상세 항목별 점수를 <breakdown> 태그 안에 **JSON** 형태로 넣어주세요. 키는 RATER_1, RATER_2, RATER_3 코드를 사용해야 합니다.
        - 점수를 매긴 이유와 부족한 부분을 <reason> 태그 안에 구체적으로 설명해주세요.
          **[중요]** <reason> 작성 시 'RATER_1' 같은 코드는 쓰지 말고, **'목차 요구사항 충족도', '구체성'** 등의 한글 표현을 사용하여 사용자가 이해하기 쉽게 설명하세요.
          **[중요]** 부족한 점을 지적할 때는 반드시 **"{chapter_description}"의 내용과 비교**하여 무엇이 없는지 설명하세요.
        
        <score>점수</score>
        <breakdown>{{"RATER_1": 90, "RATER_2": 80, "RATER_3": 85}}</breakdown>
        <reason>
        목차 설명에서는 '시장 진입 전략'을 요구하고 있으나, 현재 수집된 정보는 '제품 소개'에 치중되어 있어 요구사항 충족도가 낮습니다. 특히 경쟁사 대비 우위 전략에 대한 구체적인 내용이 보완되어야 초안 작성이 가능합니다.
        </reason>
        """
    
    llm = None
    try:
        # llm = ChatOpenAI(temperature=0, model="gpt-4o")
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
            max_tokens=4096
        )
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")
    
    prompt = PromptTemplate.from_template(GRADING_PROMPT)
    # ---------------------------------------------

    # 2. 현재 목표 섹션 정보 설정 (history_checker의 결정 반영 로직)
    collected_data = state.get("collected_data", "")
    print('collected_data 길이: ', len(collected_data))
    # print('collected_data: ', collected_data)
    # print(f"--- 📊 ASSESS_INFO 수신 데이터 길이: {len(collected_data)}자 ---")
    
    # print('-'*50)
    toc_structure = state.get("draft_toc_structure", [])
    # print('toc_structure: ', toc_structure)
    target_title = state.get("target_chapter", "").strip().strip('"')
    # print('target_title: ', target_title)
    current_idx = state.get("current_chapter_index", 0) 
    # print('current_idx: ', current_idx)
    # print('-'*50)

    # print('toc_structure: ', toc_structure)
    
    # 🔑 history_checker의 결정을 반영하여 current_idx를 덮어씁니다.
    found_idx = -1
    for i, item in enumerate(toc_structure):
        # print('i: ', i)
        # print('item: ', item)
        item_title = item.get("title", "")
        # print('item_title: ', item_title)
        if item_title == target_title or target_title in item_title:
            print(item_title)
            print(i)
            found_idx = i
            break
            
    if found_idx != -1:
        current_idx = found_idx

    # print('current_idx: ', current_idx)
    
    # 목차 끝에 도달했거나 유효하지 않은 인덱스인 경우 완료 처리
    # if not toc_structure or current_idx >= len(toc_structure):
    #     return {"sufficiency": True, "completeness_score": 100, "grading_reason": "모든 목차 항목 완료", "next_step": "FINISH"}

    current_section_item = toc_structure[current_idx]
    current_number = current_section_item.get("number", "0")
    current_title = current_section_item.get("title", "제목 없음")
    current_description = current_section_item.get("description", "정보가 필요합니다.")
    print('-' * 50)
    print("current_description: ", current_description)
    print('-' * 50)
    print('anal_guide: ', anal_guide)
    print('-' * 50)



    # 3. --- 평가 LLM 호출 및 결과 파싱 ---
    breakdown_data = {}  # 초기화
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
                    "chapter_title": current_title, # target으로 바꾸기
                    "chapter_description": current_description,
                    "collected_data": collected_data,
                    "anal_guide": anal_guide 
                }).content.strip()
                
                # 🔑 파싱 로직 수정: breakdown 점수 추가 추출
                score_match = re.search(r"<score>\s*(\d+)\s*</score>", response_text, re.IGNORECASE)
                reason_match = re.search(r"<reason>\s*(.*?)\s*</reason>", response_text, re.IGNORECASE | re.DOTALL)
                breakdown_match = re.search(r"<breakdown>\s*(\{.*?\})\s*</breakdown>", response_text, re.IGNORECASE | re.DOTALL)
                
                final_score = int(score_match.group(1)) if score_match else 0
                grading_reason = reason_match.group(1).strip() if reason_match else "평가 이유 파싱 오류"
                
                breakdown_data = {}
                if breakdown_match:
                    try:
                        breakdown_json_str = breakdown_match.group(1).strip()
                        # 🔑 JSON 파싱 실행
                        breakdown_data = json.loads(breakdown_json_str) 
                        # 점수를 int로 변환 (안전성 확보)
                        breakdown_data = {k: int(v) for k, v in breakdown_data.items()}
                        print(f"📊 상세 평가 항목별 점수: {breakdown_data}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Breakdown JSON 파싱 오류: {e}")
                    except ValueError as e:
                        print(f"❌ Breakdown 값 타입 변환 오류: {e}")
                
                print(f"📊 LLM 평가 결과: {final_score}점 - {grading_reason[:50]}...")
            except Exception as e:
                print(f"❌ LLM 호출/파싱 오류: {e}")

    print('response_text: ', response_text)
    print('final_score: ', final_score)
                
    # 4. --- 결과 반환 (80점 기준 분기 로직 구현 및 점수 영속화) ---
    is_sufficient = final_score >= 80 
    
    # 🔑 점수 영속화: section_scores에 현재 섹션 점수 저장
    section_scores = state.get("section_scores", {})
    section_scores[f"{current_number}"] = final_score
    
    # print(f"✅ 평가 완료: [{current_number} {current_title}] 필요정보: {final_score}%")
    if is_sufficient:
        print(f"🎯 충분성 판단: 80점 이상 → MANAGE_PROGRESSION으로 분기")
    else:
        print(f"⚠️ 충분성 판단: 80점 미만 → GENERATE_QUERY로 분기")
    
    return {
        "sufficiency": is_sufficient,
        "completeness_score": final_score,  # 🔑 점수 영속화를 위해 상태에 저장
        "grading_reason": grading_reason,
        "current_chapter_index": current_idx,  
        "section_scores": section_scores,  # 🔑 업데이트된 점수 저장
        # 🔑 80점 이상이면 MANAGE_PROGRESSION, 아니면 GENERATE_QUERY
        # "next_step": "MANAGE_PROGRESSION" if is_sufficient else "GENERATE_QUERY"
    }
