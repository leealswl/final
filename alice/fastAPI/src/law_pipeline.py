import os
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re

from docx import Document
import numpy as np
import chromadb

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader

# RAW → JSON → VectorDB 생성

# ----------------------------------------------------------
# 0) 기본 경로 설정
# ----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
LAW_DIR = BASE_DIR / "law_pipeline_data"

RAW_DIR = LAW_DIR / "raw"
PARSED_DIR = LAW_DIR / "parsed"
VECTORDB_DIR = LAW_DIR / "vectordb"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)
VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

LAW_COLLECTION_NAME = "law_articles"


# ----------------------------------------------------------
# 1) 텍스트 정리 함수
# ----------------------------------------------------------

def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


# ----------------------------------------------------------
# 2) 조문 분리
# ----------------------------------------------------------

def split_articles(text: str, law_name: str):
    pattern = r"\n(제\d+조(?:\([^)]*\))?)"
    parts = re.split(pattern, text)

    articles = []
    seen_main = False
    is_addendum = False

    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = clean_text(parts[i + 1])

        # 부칙 구분
        if title == "부칙" or content.startswith("부칙"):
            is_addendum = True
            continue

        if title.startswith("제1조("):
            if not seen_main:
                seen_main = True
            else:
                is_addendum = True

        articles.append({
            "title": f"{law_name} {'[부칙]' if is_addendum else ''} {title}".strip(),
            "content": content,
            "is_addendum": is_addendum
        })

    return articles


# ----------------------------------------------------------
# 3) HWPX / DOCX / PDF 파서
# ----------------------------------------------------------

def extract_hwpx(path: Path):
    with zipfile.ZipFile(path, "r") as z:
        xml = z.read("Contents/section0.xml")
    root = ET.fromstring(xml)
    texts = [e.text for e in root.iter() if e.text]
    return clean_text("\n".join(texts))


def extract_docx(path: Path):
    doc = Document(path)
    return clean_text("\n".join([p.text for p in doc.paragraphs]))


def extract_pdf(path: Path):
    loader = PyPDFLoader(str(path))
    docs = loader.load()
    return clean_text("\n".join(d.page_content for d in docs))


# ----------------------------------------------------------
# 4) 파일 파싱
# ----------------------------------------------------------

def parse_law_file(path: Path):
    law_name = re.sub(r"\(.*?\)", "", path.stem).strip()

    if path.suffix.lower() == ".hwpx":
        text = extract_hwpx(path)
    elif path.suffix.lower() == ".docx":
        text = extract_docx(path)
    elif path.suffix.lower() == ".pdf":
        text = extract_pdf(path)
    else:
        raise ValueError(f"지원되지 않는 형식: {path}")

    articles = split_articles(text, law_name)

    return {
        "law_name": law_name,
        "articles": articles
    }


# ----------------------------------------------------------
# 5) RAW → JSON 변환
# ----------------------------------------------------------

def build_parsed_json():
    print("\n🔵 RAW → JSON 변환 시작")

    for file in RAW_DIR.iterdir():
        if file.suffix.lower() not in [".hwpx", ".docx", ".pdf"]:
            continue

        print(f"📘 파싱 중: {file.name}")
        data = parse_law_file(file)

        json_path = PARSED_DIR / f"{file.stem}.json"
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f" → 저장됨: {json_path}")


# ----------------------------------------------------------
# 6) JSON → VectorDB
# ----------------------------------------------------------

def embed_openai(texts):
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return emb.embed_documents(texts)


def build_vectordb():
    print("\n🔵 VectorDB 구성 시작")

    client = chromadb.PersistentClient(path=str(VECTORDB_DIR))

    try:
        client.delete_collection(LAW_COLLECTION_NAME)
    except:
        pass

    coll = client.create_collection(LAW_COLLECTION_NAME)

    for json_file in PARSED_DIR.glob("*.json"):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        law_name = data["law_name"]

        texts = []
        ids = []
        metas = []

        for i, a in enumerate(data["articles"]):
            full = f"{a['title']}\n{a['content']}"
            texts.append(full)
            ids.append(f"{law_name}_{i}")
            metas.append({
                "law_name": law_name,
                "title": a["title"],
                "is_addendum": a["is_addendum"]
            })

        embeds = embed_openai(texts)

        coll.add(
            ids=ids,
            documents=texts,
            embeddings=embeds,
            metadatas=metas
        )

        print(f" → {json_file.name}: {len(texts)} 조문 저장")

    print("✅ VectorDB 생성 완료")


# ----------------------------------------------------------
# 7) 메인 실행
# ----------------------------------------------------------

if __name__ == "__main__":
    print("\n🚀 법령 파이프라인 실행")

    build_parsed_json()
    build_vectordb()

    print("\n🎉 모든 작업 완료! (parsed/ + vectordb/ 생성됨)")


# 법령 rag -> python law_pipeline.py 실행하면 law_pipeline_data/parsed/ 와 vectordb/ 생성됨