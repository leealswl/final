import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel # ChatRequest, ResumeRequest 정의를 위해 필요
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.checkpoint.sqlite import SqliteSaver


import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent 
sys.path.append(str(project_root))

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import List


# from v11_generator.ai_generator import generate_proposal
from dotenv import load_dotenv
load_dotenv()

import os
import json

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
    try:
        if len(files) != len(folders):
            raise ValueError(f"파일 개수({len(files)})와 폴더 개수({len(folders)})가 일치하지 않습니다.")

        print(f"📥 수신 데이터: userid={userid}, projectidx={projectidx}")
        print(f"📁 파일 개수: {len(files)}개")

        saved_files = []
        for i, file in enumerate(files):
            folder_id = int(folders[i])
            file_bytes = await file.read()
            saved_files.append({
                "bytes": file_bytes,
                "filename": file.filename,
                "folder": folder_id
            })
            folder_type = "공고" if folder_id == 1 else "첨부서류"
            file_size_kb = len(file_bytes) / 1024
            print(f"  [{i}] {file.filename} → 폴더 {folder_id} ({folder_type}) - {file_size_kb:.1f}KB")

        print(f"✅ 파일 변환 완료: {len(saved_files)}개")

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

        base_dir = Path(__file__).resolve().parent.parent
        json_file_path = base_dir / "result.json"
        response_data = {}
        if json_file_path.exists():
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    response_data = json.load(f)
                print(f"✅ 'result.json' 파일 로드 완료. (경로: {json_file_path})")
            except Exception as e:
                print(f"❌ 'result.json' 로드 중 오류 발생: {e}")
                response_data = {"status": "error", "message": "JSON 파일 로드 오류"}
        else:
            print(f"⚠️ 'result.json' 파일을 찾을 수 없습니다. 시도된 경로: {json_file_path}")
            response_data = {"status": "warning", "message": "'result.json' 파일 없음"}

        return JSONResponse(status_code=200, content=response_data)

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
    from IPython.display import Image, display
    try:
        print("📢 기획서 생성 (LangGraph) 최초 요청 수신:", request.userMessage)
        
        # --- 1. 컨텍스트 파일 로드 ---
        base_dir = Path(__file__).resolve().parent.parent 
        context_data = {}
        
        try:
            # 1. anal.json 로드 (분석 전략)
            anal_file_path = base_dir / "src/anal.json"
            if anal_file_path.exists():
                with open(anal_file_path, 'r', encoding='utf-8') as f:
                    context_data['anal_guide'] = json.load(f)
                print(f"✅ 'anal.json' 로드 완료.")
            
            # 2. result.json 로드 (목차 구조)
            result_file_path = base_dir / "src/result.json"
            if result_file_path.exists():
                with open(result_file_path, 'r', encoding='utf-8') as f:
                    context_data['result_toc'] = json.load(f)
                print(f"✅ 'result.json' 로드 완료.")

        except Exception as e:
            print(f"❌ 컨텍스트 파일 로드 중 오류: {e}")

        # 💡 1. 새로운 thread_id 생성 (최초 요청)
        new_thread_id = str(uuid.uuid4())
        print(f"🆕 새로운 LangGraph 세션 ID 생성: {new_thread_id}")

        # --- 2. initial_state 구성 (로드된 컨텍스트 주입) ---
        initial_state = {
            "user_id": str(request.userIdx) if request.userIdx else "unknown",
            "project_idx": request.projectIdx,
            "user_prompt": request.userMessage,
            
            # 🔑 로드된 JSON 데이터 주입 (FETCH_CONTEXT 노드의 입력)
            "fetched_context": context_data,
            
            "generated_text": "",
            "next_step": "", 
            "attempt_count": 0,
            
            # 💬 최초 메시지를 collected_data에 넣기 위한 필드 초기화
            "collected_data": "",
            "current_query": "",
            "current_response": request.userMessage, # 최초 메시지를 응답으로 간주하여 처리할 수 있음
            "sufficiency": False,
            "draft_toc_structure": [],
            "draft_strategy": "",
            "target_chapter": "",
            "current_chapter_index": 0,
            "target_subchapters": [],
        }
        
        # 💡 3. AsyncSqliteSaver 초기화 및 그래프 실행
        async with AsyncSqliteSaver.from_conn_string(DB_PATH) as saver:
            proposal_app = proposal_graph.compile(checkpointer=saver)
            # display(Image(proposal_app.get_graph().draw_mermaid_png()))
            result = await proposal_app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": "alice"}}
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
        
        if current_query and result.get("next_step") == "ASK_USER":
            # LangGraph가 사용자에게 질문을 던지기 위해 멈춘 상태
            response_content = {
                "status": "waiting_for_input",
                "message": current_query,
                "full_process_result": result,
                "thread_id": new_thread_id, # thread_id 반환
            }
        elif result.get("next_step") == "FINISH":
            # 루프 완료 후 END에 도달했을 때
            response_content = {
                "status": "completed",
                "message": result.get("generated_text", "처리 완료."),
                "generated_content": result.get("generated_text", ""),
                "thread_id": new_thread_id, # thread_id 반환
                "full_process_result": result
            }
        else:
            # 기타 오류 또는 예상치 못한 종료
            response_content = {
                "status": "error_unexpected",
                "message": "LangGraph 실행 중 예상치 못한 상태로 멈췄습니다.",
                "thread_id": new_thread_id, # thread_id 반환
                "full_process_result": result
            }

        return JSONResponse(status_code=200, content=response_content)
        
    except Exception as e:
        print(f"❌ /generate 처리 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "기획서 생성 중 서버 오류 발생"}
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
                config={"configurable": {"thread_id": thread_id}}
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
