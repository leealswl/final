import uuid
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path
import os
import json

# 경로 설정
current_file_path = Path(__file__).resolve()
source_root = current_file_path.parent.parent.parent.parent
sys.path.append(str(source_root))

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool

# [주석 처리] DB 저장소 (단순 실행 모드에서는 필요 없음)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from dotenv import load_dotenv

# 모듈 임포트
from v11_generator import create_proposal_graph
from config import get_settings

# v6_rag_real 모듈 import (프로덕션 전용)
from v6_rag_real import create_batch_graph

load_dotenv()
settings = get_settings()

# 경로 관련 (주석 처리된 DB 경로 등은 유지하거나 무시)
PROJECT_ROOT = source_root.parent
NEW_DB_PATH = PROJECT_ROOT / "final" / "alice" / "db" / "checkpoints.db"
DB_PATH = str(NEW_DB_PATH)

# 그래프 생성 (설계도만 가져옴)
proposal_graph = create_proposal_graph()
# batch_app = create_batch_graph()

# Request 모델들
class ResumeRequest(BaseModel):
    thread_id: str
    userMessage: str
    userIdx: Optional[int] = None
    projectIdx: Optional[int] = None

class ChatRequest(BaseModel):
    userMessage: str
    thread_id: Optional[str] = None # [추가] 대화 이어서 하려면 이게 필요함
    userIdx: int | None = None
    projectIdx: int | None = None

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
            raise ValueError(f"파일 개수({len(files)})와 폴더 개수({len(folders)})가 일치하지 않습니다.")

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

        # (기존 분석 로직 유지)
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
        "endpoints": {
            "POST /analyze": "공고 및 첨부서류 분석",
            "GET /health": "헬스 체크",
            "POST /generate": "기획서 질문 생성 (간소화)"
        }
    }

# ------------------------------------------------------------------------
# [신규] 간소화된 Generate 엔드포인트 (1회성 질문 생성 후 종료)
# ------------------------------------------------------------------------
@app.post("/generate")
async def generate_content(request: ChatRequest):
    try:
        print(f"📢 요청 수신: '{request.userMessage}' (Thread: {request.thread_id})")
        
        # 1. 컨텍스트 파일 로드
        base_dir = Path(__file__).resolve().parent.parent 
        context_data = {}
        try:
            # anal.json은 현재 로직에서 안 쓰더라도 일단 로드는 유지하거나 생략 가능
            # with open(base_dir / "src/anal.json", 'r', encoding='utf-8') as f:
            #     context_data['anal_guide'] = json.load(f)
            with open(base_dir / "src/result.json", 'r', encoding='utf-8') as f:
                context_data['result_toc'] = json.load(f)
        except Exception as e:
            print(f"⚠️ 파일 로드 경고: {e}")

        new_thread_id = str(uuid.uuid4()) # 로그용 ID
        current_thread_id = request.thread_id if request.thread_id else str(uuid.uuid4())
        # 2. 초기 상태 설정
        input_state = {
                    "user_id": str(request.userIdx) if request.userIdx else "unknown",
                    "project_idx": request.projectIdx,
                    
                    # 🚨 [수정] generate_query 노드가 'user_prompt'를 참조하므로 이 키를 꼭 넣어줘야 합니다!
                    "user_prompt": request.userMessage, 
                    
                    "fetched_context": context_data,
                    # "draft_toc_structure": [], 
                    # "collected_data": "",
                # draft_toc_structure, collected_data 등은 
                # DB에 있으면 그걸 쓰고, 없으면 노드에서 처리하도록 input에서 뺍니다.
                    # "accumulated_data": "", 
                    "attempt_count": 0,
                    "current_chapter_index": 0,
                }
        # initial_state = {
        #     "user_id": str(request.userIdx) if request.userIdx else "unknown",
        #     "project_idx": request.projectIdx,
        #     "user_prompt": request.userMessage, # 예: "1번 목차 작성할래"
        #     "fetched_context": context_data,
        #     "draft_toc_structure": [], # fetch_context 노드에서 채워짐
        #     # 나머지 필드는 현재 로직에서 안 쓰이므로 생략 가능하거나 빈 값
        #     "collected_data": "",
        #     "accumulated_data": "", 
        #     "attempt_count": 0,
        #     "current_chapter_index": 0,
        # }
        
        # 3. 그래프 실행 (단순 실행 모드)
        # ---------------------------------------------------------------------
        # [주석 처리] 기존의 복잡한 DB 저장 및 Interrupt 방식
        # ---------------------------------------------------------------------
        async with AsyncSqliteSaver.from_conn_string(DB_PATH) as saver:
            app_run = proposal_graph.compile(checkpointer=saver)
                # app_run = proposal_graph.compile() # 옵션 없음
            result = await app_run.ainvoke(input_state,
            config={"configurable": {"thread_id": "suyeonjoe"}}
            )
        
        # ---------------------------------------------------------------------
        # [활성화] 단순 메모리 실행 (DB 없이 1회성 실행)
        # ---------------------------------------------------------------------
        # app_run = proposal_graph.compile() # 옵션 없음
        # result = await app_run.ainvoke(initial_state)

        # 4. 결과 추출 (GENERATE_QUERY 노드가 만든 질문)
        current_query = result.get("current_query")
        
        print(f"📤 응답 전송: {current_query}")
        
        # 5. 프론트엔드로 질문 반환
        return JSONResponse({
            "status": "waiting_for_input", 
            "message": current_query,
            "thread_id": new_thread_id 
        })
        
    except Exception as e:
            print(f"❌ /generate 처리 중 오류: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": str(e), "message": "기획서 생성 중 서버 오류 발생"}
            )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ------------------------------------------------------------------------
# [주석 처리] 기존의 Resume 엔드포인트 (현재 상태 저장소가 없으므로 동작 불가)
# ------------------------------------------------------------------------
@app.post("/resume_generation")
async def resume_content(request: ResumeRequest):
    try:
        # print(f"📢 LangGraph 재개 요청 수신: thread_id={request.thread_id}, message={request.userMessage}")
        # 
        # thread_id = request.thread_id
        # 
        # # 1. 재개 시 전달할 입력 상태 구성 (사용자 메시지)
        # input_state = {
        #     # "user_prompt": request.userMessage, 
        #     "current_response": request.userMessage 
        # }
        # 
        # # 2. AsyncSqliteSaver 이전 상태 로드 및 실행 재개
        # async with AsyncSqliteSaver.from_conn_string(DB_PATH) as saver:
        #     proposal_app = proposal_graph.compile(checkpointer=saver)
        #     result = await proposal_app.ainvoke(
        #         input_state, 
        #         config={"configurable": {"thread_id": thread_id}}
        #     )
        # 
        # # ... (결과 처리 로직) ...
        
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": "현재 간소화 모드에서는 대화 재개 기능을 지원하지 않습니다. /generate를 이용해 주세요."
        })

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