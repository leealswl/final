from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List

app = FastAPI()

# @app.post("/analyze")
# async def analyze(files: list[UploadFile], folders: list[str], userId: str):
#     print('python fastapi 작동 시작')
#     # 파일 처리 로직
#     print('python fastapi 작동 완료')
#     return JSONResponse(content={
#         "status": "success",
#         "message": "분석 완료",
#         "processedFiles": len(files)
#     })

@app.post("/analyze")
async def analyze(
    files: List[UploadFile] = File(...),
    folders: List[str] = Form(...),
    userId: str = Form(...)
):
    print("fastapi server 시작")
    for f in files:
        contents = await f.read()
        print(f.filename, len(contents))

    print(folders, userId)
    return {"status": "success", "processedFiles": len(files)}
