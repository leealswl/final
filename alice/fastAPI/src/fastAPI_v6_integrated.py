import os
from dotenv import load_dotenv
load_dotenv()

import json
import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel # ChatRequest, ResumeRequest 정의를 위해 필요
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.checkpoint.sqlite import SqliteSaver

from v11_generator.nodes.fetch_context import fetch_context_for_proposal
from v11_generator.nodes.assess_sufficiency import assess_info
# from v11_generator.nodes.generate_section_draft import generate_section_draft
from v11_generator.nodes.generate_draft import generate_proposal_draft

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent 
sys.path.append(str(project_root))

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import List





# LangGraph 통합
from v11_generator import create_proposal_graph
from alice.fastAPI.src.ai_chat import handle_chat_message #챗봇

# 설정 import
from config import get_settings

# v6_rag_real 모듈 import (프로덕션 전용)
from v6_rag_real import create_batch_graph

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pydantic import BaseModel
from law_rag import rag_chain

# 설정 로드
settings = get_settings()
settings = get_settings()

class VerifyRequest(BaseModel):
    text: str   # 검증할 초안 문장/문단
PROJECT_ROOT = project_root.parent
print('PROJECT_ROOT: ', PROJECT_ROOT)

# 💡 MemorySaver 설정 (영구 상태 저장소)

NEW_DB_PATH = PROJECT_ROOT / "final" / "alice" / "db" / "checkpoints.db"
DB_PATH = str(NEW_DB_PATH)
# DB_PATH = "alice/db/checkpoints.db"
checkpointer = None  # 나중에 async 함수에서 초기화

# 앱 시작 시 그래프 한 번만 생성
batch_app = create_batch_graph()
# proposal_app은 checkpointer 없이 먼저 생성
proposal_graph = create_proposal_graph()

class ResumeRequest(BaseModel):
    thread_id: str
    userMessage: str
    userIdx: Optional[int] = None
    projectIdx: Optional[int] = None

class ChatRequest(BaseModel):
    userMessage: str
    userIdx: int | None = None
    projectIdx: int | None = None

class SectionGenerateRequest(BaseModel):
    """
    편집 탭에서 '특정 섹션'에 대해 대화 → 초안 생성할 때 사용하는 요청 스키마
    """
    userMessage: str                      # 사용자가 챗봇에 보낸 마지막 메시지
    sectionNumber: str                    # 예: "1.1"
    sectionTitle: str                     # 예: "사업 배경 및 필요성"
    userIdx: int | None = None
    projectIdx: int | None = None

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# API 엔드포인트
# ========================================

@app.post("/analyze")
async def analyze_documents(
    files: List[UploadFile] = File(...),
    folders: List[str] = Form(...),
    userid: str = Form(...),
    projectidx: int = Form(...)
):
    
    """
    ✅ MVP1: 공고 + 첨부서류 분석 및 사용자 입력 폼 자동 생성

    디버깅: 422 에러가 발생하면 받은 파라미터를 로그로 출력

    Backend에서 받는 데이터 구조:
    - files: 업로드된 파일 리스트 (UploadFile 객체, 실제 파일 바이너리 포함)
    - folders: 각 파일이 속한 폴더 ID 리스트 (files와 1:1 매칭)
    - userid: 사용자 ID
    - projectidx: 프로젝트 ID

    예시:
    files[0] = UploadFile("2024_사업공고.pdf")  → folders[0] = "1" (공고 폴더)
    files[1] = UploadFile("붙임1_신청서.hwp")   → folders[1] = "2" (첨부서류 폴더)
    files[2] = UploadFile("붙임2_양식.xlsx")    → folders[2] = "2" (첨부서류 폴더)

    Returns:
    - form_source: 'TEMPLATE' (첨부 양식) or 'TOC' (공고 목차)
    - user_form: 사용자 입력 폼 스키마
    - documents: 분석된 문서 정보
    """



    try:
        # ========================================
        # 1단계: Backend에서 받은 데이터 검증
        # ========================================
        if len(files) != len(folders):
            raise ValueError(
                f"파일 개수({len(files)})와 폴더 개수({len(folders)})가 일치하지 않습니다."
            )

        print(f"📥 수신 데이터: userid={userid}, projectidx={projectidx}")
        print(f"📁 파일 개수: {len(files)}개")

        # ========================================
        # 2단계: 파일 바이트 변환 (디스크 저장 없이 메모리에서 처리)
        # ========================================
        # Backend가 이미 파일을 저장했으므로, FastAPI는 저장하지 않고
        # 바이트 데이터만 추출하여 LangGraph로 전달
        #
        # Backend가 보낸 files[i]와 folders[i]는 1:1 매칭됨
        # 예시:
        #   files[0] = UploadFile("공고.pdf")      folders[0] = "1"
        #   files[1] = UploadFile("붙임1.hwp")     folders[1] = "2"
        #   files[2] = UploadFile("붙임2.xlsx")    folders[2] = "2"

        saved_files = []
        for i, file in enumerate(files):
            folder_id = int(folders[i])  # "1" → 1, "2" → 2

            # UploadFile → 바이트 데이터 변환
            file_bytes = await file.read()

            saved_files.append({
                "bytes": file_bytes,         # 파일 바이너리 데이터
                "filename": file.filename,   # 원본 파일명
                "folder": folder_id          # 1=공고, 2=첨부서류
            })

            folder_type = "공고" if folder_id == 1 else "첨부서류"
            file_size_kb = len(file_bytes) / 1024
            print(f"  [{i}] {file.filename} → 폴더 {folder_id} ({folder_type}) - {file_size_kb:.1f}KB")

        print(f"✅ 파일 변환 완료: {len(saved_files)}개")

        # ========================================
        # 3단계: AI 분석을 위한 State 생성
        # ========================================
        state = {
            "files": saved_files,
            "user_id": userid,
            "project_idx": projectidx,
            "documents": [],
            "all_chunks": [],
            "all_embeddings": None,
            "embedding_model": None,
            "chroma_client": None,
            "chroma_collection": None,
            "vector_db_path": "",
            "extracted_features": [],
            "attachment_templates": [],
            "csv_paths": None,
            "oracle_ids": None,
            "response_data": {},
            "status": "initialized",
            "errors": []
        }

        # ========================================
        # 4단계: LangGraph AI 분석 실행
        # ========================================
        # v6_rag의 batch_app이 saved_files를 분석하여:
        # 1. folder=1 파일들 → 공고 분석 (TOC 추출)
        # 2. folder=2 파일들 → 첨부서류 분석 (양식 추출)
        # 3. 사용자 입력 폼 자동 생성
        print(f"🚀 LangGraph 분석 시작: project_idx={projectidx}")
        result = await run_in_threadpool(batch_app.invoke, state)
        print(f"✅ LangGraph 분석 완료")

        # ========================================
        # 5단계 LLM 호출 → JSON Plan 생성 [분리함]
        # ========================================
       
        # ========================================
        # 6단계: 분석 결과 반환
        # ========================================
        return JSONResponse(
            status_code=200,
            content=result['response_data']
        )

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "서버 내부 오류가 발생했습니다.",
                "detail": str(e)
            }
        )

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Alice Consultant API is running"}


@app.get("/")
async def root():
    return {
        "message": settings.API_TITLE,
        "version": settings.API_VERSION,
        "mvp1": "사용자 입력 폼 자동 생성",
        "endpoints": {
            "POST /analyze": "공고 및 첨부서류 분석",
            "GET /health": "헬스 체크"
        }
    }


# @app.post("/chat")
# async def chat(request: ChatRequest):
#     try:
#         print("📢 Chat 요청 수신:", request.userMessage)
#         response_data = await handle_chat_message(
#             request.userMessage,
#             request.userIdx,
#             request.projectIdx,
#             os.getenv("OPENAI_API_KEY")
#         )
#         return response_data
#     except Exception as e:
#         return {"error": str(e)}


# 파일: fastAPI_v6_integrated....py (또는 app.py)
@app.post("/generate")
async def generate_content(request: ChatRequest):
    """
    기존 LangGraph 전체 기획서 생성 대신,
    - anal.json + result.json 로드
    - 사용자가 쓴 문장 보고 '어느 섹션일 것 같다' 대략 추론
    - 해당 섹션 기준으로 assess_info → generate_section_draft 실행

    ※ 편집 탭에서는 가능하면 /generate/section 을 쓰고,
       이 /generate 는 '섹션 번호 안 준 자유 질문'용이라고 생각하면 됨.
    """
    try:
        print("📢 섹션 기반 기획서 생성 요청:", request.userMessage)

        # -------------------------------
        # 1) 분석 컨텍스트 가져오기 (anal.json + result.json)
        #    → 우리가 만든 fetch_context_for_proposal 재사용
        # -------------------------------
        base_state = fetch_context_for_proposal({})  # state 인자는 안 쓰니까 빈 dict로 OK

        toc = base_state.get("draft_toc_structure", [])
        if not toc:
            print("⚠️ TOC(목차)가 비어 있습니다.")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "목차 데이터가 없어 섹션을 선택할 수 없습니다.",
                },
            )

            # print("--- 전체 히스토리 확인 ---")
            # final_state = await proposal_app.aget_state({"configurable": {"thread_id": "alice"}})
            # print('final_state: ', final_state)
            # # for i, msg in enumerate(final_state["messages"], 1):
            # #     # print(f"{i}. [{msg['role']}] {msg['content']}")
            # #     print(msg)
            # print("--- 전체 히스토리 확인 ---")
        
        # --- 4. 결과 반환 ---
        current_query = result.get("current_query")
        
        # if current_query and result.get("next_step") == "ASK_USER":
        #     # LangGraph가 사용자에게 질문을 던지기 위해 멈춘 상태
        #     response_content = {
        #         "status": "waiting_for_input",
        #         "message": current_query,
        #         "full_process_result": result,
        #         "thread_id": new_thread_id, # thread_id 반환
        #     }
        # elif result.get("next_step") == "FINISH":
        #     # 루프 완료 후 END에 도달했을 때
        #     response_content = {
        #         "status": "completed",
        #         "message": result.get("generated_text", "처리 완료."),
        #         "generated_content": result.get("generated_text", ""),
        #         "thread_id": new_thread_id, # thread_id 반환
        #         "full_process_result": result
        #     }
        # else:
        #     # 기타 오류 또는 예상치 못한 종료
        #     response_content = {
        #         "status": "error_unexpected",
        #         "message": "LangGraph 실행 중 예상치 못한 상태로 멈췄습니다.",
        #         "thread_id": new_thread_id, # thread_id 반환
        #         "full_process_result": result
        #     }

        response_content = {
                "status": "completed",
                "message": result.get("generated_text", "처리 완료."),
                "generated_content": result.get("generated_text", ""),
                "thread_id": new_thread_id, # thread_id 반환
                "full_process_result": result
            }

    except Exception as e:
        print(f"❌ /generate 처리 중 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "섹션 초안 생성 중 서버 오류 발생",
                "detail": str(e),
            },
        )



@app.post("/resume_generation")
async def resume_content(request: ResumeRequest):
    try:
        print(f"📢 LangGraph 재개 요청 수신: thread_id={request.thread_id}, message={request.userMessage}")

        thread_id = request.thread_id
        
        # 1. 재개 시 전달할 입력 상태 구성 (사용자 메시지)
        input_state = {
            "user_prompt": request.userMessage, 
            "current_response": request.userMessage 
        }
        
        # 2. AsyncSqliteSaver 이전 상태 로드 및 실행 재개
        async with AsyncSqliteSaver.from_conn_string(DB_PATH) as saver:
            proposal_app = proposal_graph.compile(checkpointer=saver)
            result = await proposal_app.ainvoke(
                input_state, 
                config={"configurable": {"thread_id": "asdf"}}
            )

        # 3. 결과 반환 (LangGraph가 멈춘 지점의 상태 반환)
        current_query = result.get("current_query")
        
        if current_query and result.get("next_step") == "ASK_USER":
            response_content = {
                "status": "waiting_for_input",
                "message": current_query,
                "thread_id": thread_id, 
                "full_process_result": result
            }
        elif result.get("next_step") == "FINISH":
            response_content = {
                "status": "completed",
                "message": result.get("generated_text", "처리 완료."),
                "generated_content": result.get("generated_text", ""),
                "thread_id": thread_id, 
                "full_process_result": result
            }
        else:
             response_content = {
                "status": "error_unexpected",
                "message": "LangGraph 실행 중 예상치 못한 상태로 멈췄습니다.",
                "thread_id": thread_id, 
                "full_process_result": result
            }
            
        return JSONResponse(status_code=200, content=response_content)

    except Exception as e:
        print(f"❌ /resume_generation 처리 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "LangGraph 재개 중 서버 오류 발생"}
        )

@app.get("/toc")
async def get_table_of_contents(projectidx: int | None = None):
    try:
        print(f"📚 목차 조회 요청: projectidx={projectidx}")
        base_dir = Path(__file__).resolve().parent
        json_file_path = base_dir / "result.json"
        print(f"📂 시도된 파일 경로: {json_file_path}")

        if not json_file_path.exists():
            print("⚠️ result.json 파일이 없습니다.")
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "목차 데이터를 찾을 수 없습니다. (result.json 404)",
                    "sections": []
                }
            )

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        sections = data.get("sections", [])
        print(f"✅ 목차 데이터 반환: {len(sections)}개 섹션")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "목차 데이터 조회 성공",
                "source": data.get("source", "unknown"),
                "source_file": data.get("source_file", ""),
                "extraction_method": data.get("extraction_method", ""),
                "total_sections": len(sections),
                "sections": sections,
                "extracted_at": data.get("extracted_at", "")
            }
        )

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류 발생: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"JSON 파싱 오류: result.json 파일에 문제가 있습니다. {str(e)}",
                "sections": []
            }
        )

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/generate/section")
async def generate_section(request: SectionGenerateRequest):
    """
    편집 탭에서 '특정 섹션'만 놓고 대화 → 초안 생성하는 엔드포인트

    흐름:
    1) anal.json + result.json 읽어서 컨텍스트(state) 구성
    2) sectionNumber로 해당 섹션을 찾아 current_chapter_index / target_chapter 세팅
    3) assess_info 로 정보 충분성 평가
       - 부족: missing_items 기반으로 추가 질문 문장 만들어서 반환
       - 충분: generate_section_draft 호출해서 그 섹션 초안만 생성
    """
    try:
        print(
            f"📢 섹션 초안 생성 요청: "
            f"[{request.sectionNumber} {request.sectionTitle}] "
            f"msg='{request.userMessage[:30]}...' "
            f"userIdx={request.userIdx}, projectIdx={request.projectIdx}"
        )

        # -------------------------------
        # 1) anal.json / result.json 컨텍스트 불러오기
        #    (기존 fetch_context_for_proposal 재사용)
        # -------------------------------
        base_state = fetch_context_for_proposal({})  # 빈 state 넣어도 됨 (state 안 씀)

        toc = base_state.get("draft_toc_structure", [])
        section_idx = 0

        # 섹션 번호로 index 찾기 (없으면 0번 유지)
        for i, sec in enumerate(toc):
            if str(sec.get("number")) == str(request.sectionNumber):
                section_idx = i
                break

        # 선택된 섹션으로 포커싱
        base_state["current_chapter_index"] = section_idx
        base_state["target_chapter"] = request.sectionTitle

        # -------------------------------
        # 2) 사용자 입력을 state에 주입
        #    (여기서는 프론트에서 누적해서 보내준다고 가정)
        # -------------------------------
        user_text = request.userMessage

        working_state: Dict[str, Any] = {
            **base_state,
            "user_prompt": user_text,
            "collected_data": user_text,
            "user_id": str(request.userIdx) if request.userIdx else "unknown",
            "project_idx": request.projectIdx,
        }

        # -------------------------------
        # 3) 정보 충분성 평가 (assess_info)
        # -------------------------------
        assess_result = assess_info(working_state)
        working_state.update(assess_result)

        is_sufficient = working_state.get("is_sufficient", False)
        missing_items = working_state.get("missing_items", [])

        if not is_sufficient:
            # ❗ 아직 정보 부족 → 어떤 정보를 더 써야 하는지 질문 문장 만들어서 반환
            bullets = (
                "\n".join(f"- {item}" for item in missing_items)
                if missing_items else "- (추가로 필요한 항목이 명시되지 않았습니다.)"
            )

            msg = (
                f"지금까지 알려주신 내용만으로는 '{request.sectionTitle}' 섹션을 작성하기에 조금 부족합니다.\n\n"
                f"특히 아래 항목들을 더 구체적으로 알려주시면 좋아요:\n{bullets}\n\n"
                "위 항목들을 참고해서 내용을 더 자세히 써 주시겠어요?"
            )

            return JSONResponse(
                status_code=200,
                content={
                    "status": "need_more_info",
                    "message": msg,
                    "missing_items": missing_items,
                    "sectionNumber": request.sectionNumber,
                    "sectionTitle": request.sectionTitle,
                },
            )

        # -------------------------------
        # 4) 충분하면 → 섹션 초안 생성 (generate_section_draft)
        # -------------------------------
        draft_result = generate_section_draft(working_state)
        section_text = draft_result.get("generated_section_text", "")

        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "sectionNumber": request.sectionNumber,
                "sectionTitle": request.sectionTitle,
                "generated_content": section_text,
            },
        )

    except Exception as e:
        print(f"❌ /generate/section 처리 중 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "섹션 초안 생성 중 서버 오류 발생",
                "detail": str(e),
            },
        )


    
# @app.post("/verify")
# async def verify_text(req: VerifyRequest):
#     """
#     초안 문단을 문장별로 분리하여
#     법령 RAG 기반으로 '적합/부적합' 검증해주는 API
#     """
#     try:
#         print("🔍 검증 요청:", req.text[:50], "...")

#         import re
#         sentences = re.split(r'(?<=[.!?])\s+', req.text.strip())

#         results = []
#         for s in sentences:
#             if not s.strip():
#                 continue
#             rag_res = rag_chain.invoke(s)
#             results.append({
#                 "sentence": s,
#                 "result": rag_res.content
#             })

#         return {
#             "status": "ok",
#             "count": len(results),
#             "results": results
#         }

#     except Exception as e:
#         print("❌ 검증 오류:", e)
#         return {
#             "status": "error",
#             "message": str(e)
#         }
    
        print(f"❌ /toc 처리 중 기타 서버 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"FastAPI 내부 오류: {str(e)}",
                "sections": []
            }
        )


# ========================================
# 실행 (개발용)
# ========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastAPI_v6_integrated:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD)