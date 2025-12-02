from ..state_types import ProposalGenerationState
# from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging
from typing import Dict, Any, Optional
import re
import json
from json_repair import repair_json
from pathlib import Path
import os

def get_json_file_path() -> Path:
    """
    JSON 파일 저장 경로를 반환
    Returns:
        Path: backend/uploads/admin/1/1/234.json 경로 (Spring Boot가 서빙하는 경로)
    """
    current_file = Path(__file__).resolve()
    # alice/fastAPI/src/v11_generator/nodes/generate_draft.py
    # → alice/fastAPI/src/v11_generator/ → alice/fastAPI/src/ → alice/fastAPI/ → alice/ → final/ (프로젝트 루트)
    project_root = current_file.parent.parent.parent.parent.parent.parent
    # Spring Boot가 서빙하는 backend/uploads/ 경로에 저장
    save_dir = project_root / "backend" / "documents"
    return save_dir


def load_existing_json() -> Optional[Dict[str, Any]]:
    """
    기존 JSON 파일을 읽어서 반환
    Phase 1: 파일 읽기 기능
    
    Returns:
        Optional[Dict[str, Any]]: ProseMirror JSON 구조, 파일이 없으면 None
    """
    file_path = get_json_file_path()
    
    try:
        if not file_path.exists():
            print(f"📄 [Phase 1] 파일이 존재하지 않음: {file_path}")
            return None
        
        print(f"📖 [Phase 1] 파일 읽기 시작: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # JSON 구조 검증
        if not isinstance(content, dict):
            print(f"⚠️ [Phase 1] JSON이 dict 형식이 아님: {type(content)}")
            return None
        
        if content.get("type") != "doc":
            print(f"⚠️ [Phase 1] ProseMirror JSON 형식이 아님: type={content.get('type')}")
            return None
        
        paragraph_count = len(content.get("content", []))
        print(f"✅ [Phase 1] 파일 읽기 완료: {paragraph_count}개 paragraph")
        
        return content
        
    except json.JSONDecodeError as e:
        print(f"❌ [Phase 1] JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ [Phase 1] 파일 읽기 실패: {e}")
        import traceback
        print(f"🔍 [Phase 1] 상세 오류: {traceback.format_exc()}")
        return None


def text_to_prosemirror_json(text: str) -> Dict[str, Any]:
    """
    텍스트를 ProseMirror JSON 형식으로 변환
    한글 문서/DOCX 스타일: 각 줄을 별도 paragraph로, 빈 줄도 빈 paragraph로 처리
    """
    if not text or not text.strip():
        return {
            "type": "doc",
            "content": []
        }
    
    # 프롬프트에서 반환된 텍스트에서 실제 본문만 추출
    # "----------------------------------------------------------------------" 구분자 제거
    lines = text.split('\n')
    content_lines = []
    in_content = False
    
    for line in lines:
        line_stripped = line.strip()
        # 구분자 라인 무시
        if line_stripped.startswith('---') or line_stripped.startswith('==='):
            continue
        # <작성된 제안서 본문> 같은 태그 제거
        if '<작성된 제안서 본문>' in line_stripped or '</작성된 제안서 본문>' in line_stripped:
            in_content = True
            continue
        # 모든 줄을 포함 (빈 줄도 포함)
        content_lines.append(line_stripped)
    
    # 각 줄을 별도 paragraph로 처리 (한글 문서 스타일)
    paragraphs = []
    
    for line in content_lines:
        # 빈 줄도 빈 paragraph로 처리
        if not line:
            paragraphs.append({
                "type": "paragraph",
                "attrs": {"textAlign": "left"},
                "content": [{"type": "text", "text": "​"}]  # 빈 텍스트 (zero-width space)
            })
        else:
            # 각 줄을 별도 paragraph로
            paragraphs.append({
                "type": "paragraph",
                "attrs": {"textAlign": "left"},
                "content": [{"type": "text", "text": line}]
            })
    
    # 빈 경우 기본 paragraph 추가
    if not paragraphs:
        paragraphs.append({
            "type": "paragraph",
            "attrs": {"textAlign": None},
            "content": [{"type": "text", "text": ""}]
        })
    
    return {
        "type": "doc",
        "content": paragraphs
    }
import json
import os
from pathlib import Path


def _extract_relevant_guide(guide_data: dict, chapter_number: str, chapter_title: str) -> str:
    """
    guide_claude.json에서 목차 번호/제목에 맞는 가이드를 추출합니다.

    Args:
        guide_data: 로드된 guide JSON 데이터
        chapter_number: 목차 번호 (예: "1", "2", "2.1")
        chapter_title: 목차 제목

    Returns:
        해당 목차에 대한 가이드 텍스트
    """
    try:
        # integrated_business_proposal_guide에서 섹션 찾기
        guide_root = guide_data.get("integrated_business_proposal_guide", {})

        # 목차 번호를 기반으로 섹션 키 매핑
        section_mapping = {
            "1": "section_01_basic_info",
            "2": "section_02_current_status",
            "3": "section_03_preparation_plan",
            "4": "section_04_goals_and_requirements",
            "5": "section_05_business_feasibility",
            "6": "section_06_budget",
            "7": "section_07_evaluation_criteria"
        }

        # 주요 섹션 번호 추출 (2.1 -> 2)
        main_section_num = chapter_number.split('.')[0] if '.' in chapter_number else chapter_number
        section_key = section_mapping.get(main_section_num)

        if section_key and section_key in guide_root:
            section_data = guide_root[section_key]

            # 가이드 텍스트 구성
            guide_text = f"## {section_data.get('section_name', '')}\n\n"

            # R&D 계획서 참조
            if 'rd_plan_reference' in section_data:
                guide_text += f"**R&D 참조**: {section_data['rd_plan_reference']}\n"

            # SW RFP 참조
            if 'sw_rfp_reference' in section_data:
                guide_text += f"**SW RFP 참조**: {section_data['sw_rfp_reference']}\n\n"

            # 주요 키워드
            if 'common_keywords' in section_data:
                guide_text += f"**핵심 키워드**: {', '.join(section_data['common_keywords'])}\n\n"

            # 나머지 섹션 데이터를 JSON으로 추가
            guide_text += "### 상세 가이드\n"
            guide_text += json.dumps(section_data, ensure_ascii=False, indent=2)

            return guide_text
        else:
            # 매칭되는 섹션이 없으면 일반 작성 팁 반환
            tips = guide_root.get("writing_tips_and_warnings", {}).get("common_tips", [])
            if tips:
                return f"일반 작성 지침:\n" + "\n".join(f"- {item}" for item in tips)
            else:
                return "해당 목차에 대한 가이드를 찾을 수 없습니다."

    except Exception as e:
        print(f"⚠️ 가이드 추출 오류: {e}")
        import traceback
        traceback.print_exc()
        return "가이드 정보를 추출할 수 없습니다."


def generate_proposal_draft(state: ProposalGenerationState) -> ProposalGenerationState:
    import os
    """
    [작가 노드 - 비활성화 상태]
    현재는 초안 생성 로직을 주석 처리하여 실행되지 않도록 막아두었습니다.
    테스트 단계에서 오류를 방지하기 위해 더미(Dummy) 데이터를 반환합니다.
    """
    print("🔍 [디버깅] --- 노드 실행: generate_proposal_draft ---")
    print(f"🔍 [디버깅] state.keys(): {list(state.keys())}")
    print(f"🔍 [디버깅] collected_data 길이: {len(state.get('collected_data', ''))}")
    logging.info(f"📝 generate_draft 노드 실행")

    DRAFT_PROMPT = """
        당신은 한국 정부 RFP(제안요청서)·입찰·지원사업 제안서 작성 전문가이며,
        실제 평가 심사위원이 읽는 수준으로 공식적이고 설득력 있는 문체를 사용합니다.

        ======================================================================
        📌 <입력 정보>
        1. 작성 대상 목차 (Target Section)
        - "{target_chapter_info}"

        2. 공고문 핵심 분석 요약 (Key Guidelines Summary)
        - "{anal_guide_summary}"

        3. 현재까지 수집된 사용자 정보 (Collected Data)
        - {collected_data}

        4. 최근 대화 히스토리 (Recent Chat History)
        - {recent_history}

        5. 제안서 작성 가이드 (Writing Guide Reference)
        - {guide_reference}
        ======================================================================

        ✍️ <작성 지침>
        - 위 다섯 가지 입력 정보를 모두 반영하여 **정부 제안서 공식 문체로 해당 목차의 완성된 단락**을 작성하십시오.
        - **제안서 작성 가이드**에 명시된 해당 목차의 작성 요령, 핵심 포인트, 필수 포함 내용을 반드시 준수하십시오.
        - 가이드에 제시된 표 형식, 측정 방법, 정량적 지표, 예시 등의 요구사항이 있다면 반드시 반영하십시오.
        - 문단 형식으로 작성하고, 개조식 나열이 필요한 경우 적절히 혼합하십시오.
        - 사용자가 제공한 정보가 불충분한 영역이 있어도 추론 가능한 범위 내에서 자연스럽게 보완하십시오.
        - 단순 요약이나 나열이 아닌 **논리적 구조(배경 → 필요성 → 목적 → 근거 → 기대효과 등)**로 설득력 있게 작성하십시오.
        - 공고문 요구사항과의 적합성을 명확하게 드러내십시오.
        - 평가위원이 읽을 때 **사업의 타당성, 실현 가능성, 공공성, 혁신성, 기대 성과**가 강조되도록 작성하십시오.
        - '우리는', '저희는' 같은 표현 대신 **기업명 또는 사업 주체를 3인칭으로 기술**하십시오.

        📌 <출력 형식>
        아래 ProseMirror JSON 형식을 반드시 준수하여 출력하십시오. 코드 블록 없이 순수 JSON만 출력하세요.

        ⚠️ 중요: 반드시 **제목(heading)을 첫 번째 요소로** 생성하고, 그 다음에 내용(paragraph)을 생성하세요.
        - 제목 텍스트: "{chapter_title}" 형식을 그대로 사용하세요 (예: "1. 기업현황")
        - 제목의 level은 1을 사용하세요

        {{
          "type": "doc",
          "content": [
            {{
              "type": "heading",
              "attrs": {{
                "level": 1
              }},
              "content": [
                {{
                  "type": "text",
                  "text": "{chapter_title}"
                }}
              ]
            }},
            {{
              "type": "paragraph",
              "attrs": {{
                "textAlign": "left",
                "paragraphIndex": 0
              }},
              "content": [
                {{
                  "type": "text",
                  "text": "첫 번째 문단 내용"
                }}
              ]
            }},
            {{
              "type": "paragraph",
              "attrs": {{
                "textAlign": "left",
                "paragraphIndex": 1
              }},
              "content": [
                {{
                  "type": "text",
                  "text": "​"
                }}
              ]
            }},
            {{
              "type": "paragraph",
              "attrs": {{
                "textAlign": "left",
                "paragraphIndex": 2
              }},
              "content": [
                {{
                  "type": "text",
                  "text": "두 번째 문단 내용"
                }}
              ]
            }}
          ]
        }}

        ⚠️ 중요:
        - **반드시 첫 번째 요소로 heading을 생성하세요** (제목 텍스트: "{chapter_title}")
        - 각 paragraph는 paragraphIndex를 0부터 순차적으로 부여하세요
        - 빈 줄은 text: "​" (zero-width space)로 처리하세요
        - 코드 블록 마커(```)를 사용하지 마세요
        - 순수 JSON만 출력하세요
        - 각 문단은 별도의 paragraph로 구분하세요
        """
    
    # 1. guide_claude.json 로드
    guide_data = {}
    guide_reference = "가이드 정보를 불러올 수 없습니다."

    try:
        # 현재 파일 기준으로 guide 폴더 경로 찾기
        current_dir = Path(__file__).parent
        guide_path = current_dir.parent / "guide" / "guide_claude.json"

        if guide_path.exists():
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_data = json.load(f)
                print(f"✅ guide_claude.json 로드 성공: {guide_path}")
        else:
            print(f"⚠️ guide_claude.json 파일을 찾을 수 없습니다: {guide_path}")
    except Exception as e:
        print(f"⚠️ guide_claude.json 로드 오류: {e}")

    # 2. 현재 목표 섹션 정보 설정 (history_checker의 결정 반영 로직)
    collected_data = state.get("collected_data", "")
    # print('collected_data: ', collected_data)
    # print(f"--- 📊 ASSESS_INFO 수신 데이터 길이: {len(collected_data)}자 ---")

    toc_structure = state.get("draft_toc_structure", [])
    target_title = state.get("target_chapter", "")
    current_idx = state.get("current_chapter_index", 0)

    fetched_context = state.get("fetched_context", {})
    anal_guide_summary = str(fetched_context.get("anal_guide", "전략 정보 없음"))

    if toc_structure and current_idx < len(toc_structure):
        major_chapter_item = toc_structure[current_idx]
        major_chapter_number = major_chapter_item.get("number", "0")
        major_chapter_title = major_chapter_item.get("title", "제목 없음")

        # 2-1. LLM 프롬프트에 사용될 주 챕터 정보 구성
        chapter_display = f"{major_chapter_item.get('number')} {major_chapter_item.get('title')}"
        target_info_full = f"[{chapter_display}]\n설명: {major_chapter_item.get('description')}"

        print('target_info_full: ', target_info_full)

        # 2-2. 가이드에서 해당 목차에 맞는 섹션 찾기
        if guide_data:
            guide_reference = _extract_relevant_guide(guide_data, major_chapter_number, major_chapter_title)
            print(f"📚 추출된 가이드 길이: {len(guide_reference)}자")

    msgs = state.get("messages", [])
    recent_history = ""
    if msgs:
        for msg in msgs:
            role = "👤" if msg.get("role") == "user" else "🤖"
            content = msg.get("content", "")
            recent_history += f"{role}: {content}\n"


    prompt = PromptTemplate.from_template(DRAFT_PROMPT)

    llm = None
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
            max_tokens=8000
        )
    except Exception as e:
        print(f"⚠️ LLM 초기화 오류: {e}")

    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        'target_chapter_info': target_info_full,
        'chapter_title': chapter_display,  # 제목을 별도로 전달
        'anal_guide_summary': anal_guide_summary,
        'collected_data': collected_data,
        'recent_history': recent_history,
        'guide_reference': guide_reference
        })
    
    # 만약 accumulated_data가 문자열이면 리스트로 변환
    accumulated_data = state.get('accumulated_data', [])
    if isinstance(accumulated_data, str):
        accumulated_data = [accumulated_data]

    accumulated_data.append(target_title)

    print('accumulated_data: ', accumulated_data)
    
    history = state.get("messages", [])
    history.append({"role": "assistant", "content": result})
    
    # LLM이 생성한 JSON 파싱 및 파일 저장
    completed_content = None
    try:
        print(f"🔍 [디버깅] JSON 파싱 시작, result 길이: {len(result) if result else 0}")
        
        # 코드 블록 마커 제거 (```json ... ``` 형식일 경우)
        json_text = result.strip()
        if json_text.startswith('```'):
            lines = json_text.split('\n')
            # 첫 줄과 마지막 줄 제거 (```json, ```)
            json_text = '\n'.join(lines[1:-1]) if len(lines) > 2 and lines[-1].strip() == '```' else '\n'.join(lines[1:])
        
        # JSON 파싱
        # completed_content = json.loads(json_text)
        try:
            completed_content = repair_json(json_text, return_objects=True)
        except Exception as e:
            print(f"JSON 복구 실패: {e}")
            # 실패 시 원본 텍스트를 로그에 남겨 확인 필요
            print(json_text) 
            raise e
        print(f"✅ JSON 파싱 완료: {len(completed_content.get('content', []))}개 문단")
        
        # 파일 저장 경로 설정 (get_json_file_path 함수 재사용)
        save_path = Path(get_json_file_path()) / str(state.get("user_id")) / str(state.get("project_idx")) / "초안.json"
        
        # 절대 경로 명확히 출력
        absolute_path = save_path.resolve()
        print(f"💾 [저장 전] 파일 경로 (상대): {save_path}")
        print(f"💾 [저장 전] 파일 경로 (절대): {absolute_path}")
        print(f"💾 [저장 전] 파일 존재: {save_path.exists()}")
        
        # 기존 파일 읽기 (있으면)
        existing_content = None
        if save_path.exists():
            with open(save_path, 'r', encoding='utf-8') as f:
                existing_content = json.load(f)
            old_para_count = len(existing_content.get('content', []))
            print(f"💾 [저장 전] 기존 paragraph 개수: {old_para_count} (추가 예정)")
        else:
            print(f"💾 [저장 전] 파일 없음 (새로 생성)")
        
        # 기존 content가 있으면 새 content를 뒤에 추가, 없으면 새로 생성
        if existing_content and existing_content.get('content'):
            # 기존 content에 새 content 추가
            existing_content_list = existing_content.get('content', [])
            new_content_list = completed_content.get('content', [])
            
            # 기존 paragraph의 최대 paragraphIndex 찾기
            max_paragraph_index = -1
            for para in existing_content_list:
                if para.get('type') == 'paragraph' and para.get('attrs', {}).get('paragraphIndex') is not None:
                    max_paragraph_index = max(max_paragraph_index, para.get('attrs', {}).get('paragraphIndex', -1))
            
            # 새 paragraph들의 paragraphIndex를 기존 인덱스 다음부터 시작
            current_index = max_paragraph_index + 1
            for para in new_content_list:
                if para.get('type') == 'paragraph':
                    if 'attrs' not in para:
                        para['attrs'] = {}
                    para['attrs']['paragraphIndex'] = current_index
                    if 'textAlign' not in para['attrs']:
                        para['attrs']['textAlign'] = 'left'
                    current_index += 1
                elif para.get('type') == 'heading':
                    # heading은 paragraphIndex가 필요 없지만, attrs는 유지
                    if 'attrs' not in para:
                        para['attrs'] = {}
            
            # 기존 content 뒤에 새 content 추가
            existing_content_list.extend(new_content_list)
            final_content = {
                "type": "doc",
                "content": existing_content_list
            }
            print(f"💾 [추가 모드] 기존 {len(existing_content_list) - len(new_content_list)}개 + 새 {len(new_content_list)}개 = 총 {len(existing_content_list)}개")
        else:
            # 기존 파일이 없으면 새로 생성
            final_content = completed_content
            # 새 paragraph들의 paragraphIndex가 0부터 시작하도록 보장
            for i, para in enumerate(final_content.get('content', [])):
                if para.get('type') == 'paragraph':
                    if 'attrs' not in para:
                        para['attrs'] = {}
                    if 'paragraphIndex' not in para['attrs']:
                        para['attrs']['paragraphIndex'] = i
                    if 'textAlign' not in para['attrs']:
                        para['attrs']['textAlign'] = 'left'
            print(f"💾 [새로 생성] paragraph 개수: {len(final_content.get('content', []))}")
        
        # JSON 파일 저장 (기존 내용 + 새 내용)
        print(f"💾 [저장 시도] 총 paragraph 개수: {len(final_content.get('content', []))}")
        if final_content.get('content'):
            first_para_text = final_content['content'][0].get('content', [{}])[0].get('text', '')[:50] if final_content['content'][0].get('content') else ''
            print(f"💾 [저장 시도] 첫 번째 paragraph 텍스트: {first_para_text}...")
        
        try:
            # 파일 저장 (기존 + 새 내용)
            print(f"💾 [저장 시작] 경로: {absolute_path}")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(final_content, f, ensure_ascii=False, indent=2)
                # 파일 버퍼 플러시 강제
                f.flush()
                import os
                if hasattr(f, 'fileno'):
                    try:
                        os.fsync(f.fileno())
                    except:
                        pass
            print(f"✅ JSON 파일 저장 완료: {absolute_path}")
        except Exception as save_error:
            print(f"❌ [저장 실패] 오류: {save_error}")
            print(f"❌ [저장 실패] 경로: {absolute_path}")
            import traceback
            print(f"🔍 [저장 실패 상세] {traceback.format_exc()}")
            raise
        
        # 저장 후 파일 내용 검증
        import time
        time.sleep(0.1)  # 파일 시스템 동기화 대기
        
        if save_path.exists():
            with open(save_path, 'r', encoding='utf-8') as f:
                saved_content = json.load(f)
            saved_para_count = len(saved_content.get('content', []))
            saved_first_text = ''
            if saved_content.get('content') and saved_content['content'][0].get('content'):
                saved_first_text = saved_content['content'][0]['content'][0].get('text', '')[:50]
            
            print(f"✅ [저장 후 검증] 파일 경로: {absolute_path}")
            print(f"✅ [저장 후 검증] 파일 paragraph 개수: {saved_para_count}")
            print(f"✅ [저장 후 검증] 첫 번째 paragraph 텍스트: {saved_first_text}...")
            print(f"✅ [저장 후 검증] 파일 크기: {save_path.stat().st_size} bytes")
            0
            # 내용 일치 확인
            expected_count = len(final_content.get('content', []))
            if saved_para_count == expected_count:
                print(f"✅ [저장 후 검증] paragraph 개수 일치! (예상: {expected_count}개, 실제: {saved_para_count}개)")
                print(f"✅ [저장 후 검증] ✅✅✅ 파일 저장 성공! ✅✅✅")
            else:
                print(f"⚠️ [저장 후 검증] paragraph 개수 불일치: 저장됨={saved_para_count}, 예상={expected_count}")
        else:
            print(f"❌ [저장 후 검증] 파일이 존재하지 않음! 저장 실패!")
            print(f"❌ [저장 후 검증] 예상 경로: {absolute_path}")
        
        # completed_content를 final_content로 업데이트 (반환값에 사용)
        completed_content = final_content
        
        print(f"🔍 [디버깅] completedContent 구조: {json.dumps(completed_content, ensure_ascii=False, indent=2)[:500]}...")
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 파싱 실패: {e}")
        print(f"🔍 [디버깅] 파싱 실패한 텍스트: {result[:500]}...")
        import traceback
        print(f"🔍 [디버깅] 파싱 실패 상세: {traceback.format_exc()}")
        completed_content = None
    except Exception as e:
        print(f"⚠️ 파일 저장 실패: {e}")
        import traceback
        print(f"🔍 [디버깅] 저장 실패 상세: {traceback.format_exc()}")
        # 파싱은 성공했지만 저장 실패한 경우 completed_content는 유지
    
    # 4. 상태 반환
    # 다음 챕터 정보 가져오기 (목차의 description 필드 사용)
    current_chapter_info = chapter_display if 'chapter_display' in locals() else "현재 섹션"
    
    # 다음 챕터 정보 및 description 가져오기
    next_chapter_info = ""
    next_chapter_description = ""
    
    if toc_structure and current_idx + 1 < len(toc_structure):
        next_chapter = toc_structure[current_idx + 1]
        next_chapter_number = next_chapter.get('number', '')
        next_chapter_title = next_chapter.get('title', '')
        next_chapter_description = next_chapter.get('description', '')
        next_chapter_info = f"{next_chapter_number} {next_chapter_title}"
    else:
        next_chapter_info = "모든 섹션 작성이 완료되었습니다."
        next_chapter_description = ""
    
    # 코멘트 생성 (생성 완료 메시지 + 다음 챕터 설명)
    if next_chapter_description:
        comment = f"""✅ '{current_chapter_info}' 섹션이 성공적으로 생성되었습니다.

📝 다음 단계:
다음으로 작성할 섹션은 '{next_chapter_info}'입니다.
{next_chapter_description}

해당 섹션에 대한 정보를 알려주시면 계속 작성하겠습니다."""
    else:
        comment = f"""✅ '{current_chapter_info}' 섹션이 성공적으로 생성되었습니다.

📝 다음 단계:
{next_chapter_info}"""
    
    return_value = {
        "current_query": comment,  # 코멘트 + 다음 챕터 description
        "completedContent": completed_content,
        "messages": history
    }
    print(f"🔍 [디버깅] generate_draft 반환값 - current_query 존재: {return_value.get('current_query') is not None}")
    print(f"🔍 [디버깅] generate_draft 반환값 - completedContent 존재: {return_value.get('completedContent') is not None}")
    print(f"🔍 [디버깅] generate_draft 반환값 - keys: {list(return_value.keys())}")
    
    return return_value