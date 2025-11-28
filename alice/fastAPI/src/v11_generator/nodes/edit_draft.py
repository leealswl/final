from ..state_types import ProposalGenerationState
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import logging
from pathlib import Path
import os
import re

def get_json_file_path() -> Path:
    """
    JSON 파일 저장 경로를 반환
    Returns:
        Path: backend/uploads/admin/1/1/234.json 경로 (Spring Boot가 서빙하는 경로)
    """
    current_file = Path(__file__).resolve()
    # alice/fastAPI/src/v11_generator/nodes/edit_draft.py
    # → alice/fastAPI/src/v11_generator/ → alice/fastAPI/src/ → alice/fastAPI/ → alice/ → final/ (프로젝트 루트)
    project_root = current_file.parent.parent.parent.parent.parent.parent
    # Spring Boot가 서빙하는 backend/uploads/ 경로에 저장
    save_dir = project_root / "backend" / "documents"
    return save_dir


def load_existing_json(state: ProposalGenerationState) -> Optional[Dict[str, Any]]:
    """
    기존 JSON 파일을 읽어서 반환
    Returns:
        Optional[Dict[str, Any]]: ProseMirror JSON 구조, 파일이 없으면 None
    """
    file_path = Path(get_json_file_path()) / str(state.get("user_id")) / str(state.get("project_idx")) / "초안.json"
    
    try:
        if not file_path.exists():
            print(f"📄 파일이 존재하지 않음: {file_path}")
            return None
        
        print(f"📖 파일 읽기 시작: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # JSON 구조 검증
        if not isinstance(content, dict):
            print(f"⚠️ JSON이 dict 형식이 아님: {type(content)}")
            return None
        
        if content.get("type") != "doc":
            print(f"⚠️ ProseMirror JSON 형식이 아님: type={content.get('type')}")
            return None
        
        paragraph_count = len(content.get("content", []))
        print(f"✅ 파일 읽기 완료: {paragraph_count}개 요소")
        
        return content
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        import traceback
        print(f"🔍 상세 오류: {traceback.format_exc()}")
        return None


def edit_proposal_draft(state: ProposalGenerationState) -> ProposalGenerationState:
    import os
    """
    에디터 내용 수정 노드
    사용자 요청에 따라 기존 JSON 파일을 수정하고 저장
    """
    print("--- 노드 실행: edit_proposal_draft ---")
    logging.info(f"✏️ edit_draft 노드 실행")
    
    user_prompt = state.get("user_prompt", "")
    print(f"🔍 수정 요청: {user_prompt}")
    
    # 1. 기존 JSON 파일 읽기
    existing_json = load_existing_json(state)
    
    if not existing_json:
        return {
            "current_query": "수정할 문서를 찾을 수 없습니다. 먼저 문서를 생성해주세요.",
            "completedContent": None,
            "messages": state.get("messages", [])
        }
    
    # 2. LLM 프롬프트 구성
    EDIT_PROMPT = """
당신은 ProseMirror JSON 문서 수정 전문가입니다.
사용자의 요청에 따라 기존 문서를 정확하게 수정하세요.

======================================================================
📌 <기존 문서 JSON>
{existing_json}

📌 <사용자 수정 요청>
{user_request}
======================================================================

✍️ <수정 지침>
- 사용자의 요청을 정확히 이해하고, 기존 JSON 구조를 최대한 유지하면서 수정하세요.
- ProseMirror JSON 형식을 반드시 준수하세요.
- paragraphIndex는 0부터 순차적으로 재정렬하세요.
- 수정된 전체 JSON만 출력하세요.
- 코드 블록 마커(```json)를 사용하지 마세요.
- 순수 JSON만 출력하세요.

⚠️ 중요:
- 기존 문서의 구조와 형식을 최대한 유지하세요.
- 사용자가 특정 부분만 수정하라고 했으면, 그 부분만 수정하고 나머지는 그대로 유지하세요.
- paragraphIndex를 0부터 순차적으로 재정렬하세요.
- 각 paragraph의 attrs에 textAlign과 paragraphIndex를 포함하세요.

<출력 형식>
수정된 전체 ProseMirror JSON만 출력하세요. 코드 블록 없이 순수 JSON만 출력하세요.
"""
    
    # 3. LLM 호출
    try:
        prompt = PromptTemplate.from_template(EDIT_PROMPT)
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        chain = prompt | llm | StrOutputParser()
        
        existing_json_str = json.dumps(existing_json, ensure_ascii=False, indent=2)
        
        print(f"🤖 LLM 수정 요청 시작...")
        result = chain.invoke({
            "existing_json": existing_json_str,
            "user_request": user_prompt
        })
        
        print(f"✅ LLM 응답 수신 완료 (길이: {len(result)}자)")
        
    except Exception as e:
        print(f"❌ LLM 호출 실패: {e}")
        import traceback
        print(f"🔍 상세 오류: {traceback.format_exc()}")
        return {
            "current_query": "문서 수정 중 오류가 발생했습니다. 다시 시도해주세요.",
            "completedContent": None,
            "messages": state.get("messages", [])
        }
    
    # 4. JSON 파싱 및 파일 저장
    try:
        # 코드 블록 마커 제거
        json_text = result.strip()
        if json_text.startswith('```'):
            lines = json_text.split('\n')
            # 첫 줄과 마지막 줄 제거 (```json, ```)
            json_text = '\n'.join(lines[1:-1]) if len(lines) > 2 and lines[-1].strip() == '```' else '\n'.join(lines[1:])
        
        # JSON 파싱
        modified_json = json.loads(json_text)
        print(f"✅ JSON 파싱 완료: {len(modified_json.get('content', []))}개 요소")
        
        # 파일 저장 경로 설정
        save_path = Path(get_json_file_path()) / str(state.get("user_id")) / str(state.get("project_idx")) / "초안.json"
        absolute_path = save_path.resolve()
        print(f"💾 파일 저장 시작: {absolute_path}")
        
        # JSON 파일 저장 (덮어쓰기)
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(modified_json, f, ensure_ascii=False, indent=2)
            f.flush()
            if hasattr(f, 'fileno'):
                try:
                    os.fsync(f.fileno())
                except:
                    pass
        
        print(f"✅ JSON 파일 저장 완료: {absolute_path}")
        
        # 저장 후 검증
        import time
        time.sleep(0.1)  # 파일 시스템 동기화 대기
        
        if save_path.exists():
            with open(save_path, 'r', encoding='utf-8') as f:
                saved_content = json.load(f)
            saved_count = len(saved_content.get('content', []))
            print(f"✅ 저장 후 검증: {saved_count}개 요소, 파일 크기: {save_path.stat().st_size} bytes")
        
        # 응답 메시지 생성
        response_message = "문서가 성공적으로 수정되었습니다."
        
        return {
            "current_query": response_message,
            "completedContent": modified_json,
            "messages": state.get("messages", [])
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        print(f"🔍 파싱 실패한 텍스트: {result[:500]}...")
        import traceback
        print(f"🔍 상세 오류: {traceback.format_exc()}")
        return {
            "current_query": "수정된 문서를 파싱하는 중 오류가 발생했습니다. 다시 시도해주세요.",
            "completedContent": None,
            "messages": state.get("messages", [])
        }
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        import traceback
        print(f"🔍 상세 오류: {traceback.format_exc()}")
        return {
            "current_query": "수정된 문서를 저장하는 중 오류가 발생했습니다. 다시 시도해주세요.",
            "completedContent": None,
            "messages": state.get("messages", [])
        }

