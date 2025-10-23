from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/analyze")
async def analyze(files: list, folders: list, userId: str):
    # 파일 처리 로직
    return JSONResponse(content={
        "status": "success",
        "message": "분석 완료",
        "processedFiles": len(files)
    })