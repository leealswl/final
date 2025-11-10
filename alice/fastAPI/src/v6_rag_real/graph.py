"""
LangGraph 구성
"""

from langgraph.graph import StateGraph, START, END
from .state_types import BatchState
from . import nodes


def create_batch_graph():
    """
    LangGraph 생성 및 컴파일

    Returns:
        compiled graph
    """
    # 그래프 생성
    graph = StateGraph(BatchState)

    # 노드 추가
    graph.add_node("extract_all_texts", nodes.extract_all_texts)
    graph.add_node("chunk_all_documents", nodes.chunk_all_documents)
    graph.add_node("embed_all_chunks", nodes.embed_all_chunks)
    graph.add_node("init_and_store_vectordb", nodes.init_and_store_vectordb)
    graph.add_node("extract_features_rag", nodes.extract_features_rag)  # Feature 추출
    graph.add_node("detect_templates", nodes.detect_proposal_templates)  # ✨ 양식 감지

    # ✨ 조건부 목차 추출 노드 (라우팅 기반)
    graph.add_node("extract_toc_from_template", nodes.extract_toc_from_template)  # 양식 기반
    graph.add_node("extract_toc_from_announcement_and_attachments", nodes.extract_toc_from_announcement_and_attachments)  # 공고+첨부 기반

    # 🔖 MVP2: match_cross_references 노드 제거 (현재 미사용, MVP2에서 재구현 예정)
    # graph.add_node("match_cross_references", nodes.match_cross_references)

    # ✨ 저장 노드: CSV (개발/테스트용)
    graph.add_node("save_to_csv", nodes.save_to_csv)
    graph.add_node("build_response", nodes.build_response)

    # 엣지 추가 (순차 실행)
    graph.add_edge(START, "extract_all_texts")
    graph.add_edge("extract_all_texts", "chunk_all_documents")
    graph.add_edge("chunk_all_documents", "embed_all_chunks")
    graph.add_edge("embed_all_chunks", "init_and_store_vectordb")
    graph.add_edge("init_and_store_vectordb", "extract_features_rag")
    graph.add_edge("extract_features_rag", "detect_templates")  # Feature → 양식 감지

    # ✨ 조건부 엣지: 양식 유무에 따라 라우팅
    graph.add_conditional_edges(
        "detect_templates",
        nodes.route_toc_extraction,  # 라우터 함수
        {
            "extract_toc_from_template": "extract_toc_from_template",  # 양식 O
            "extract_toc_from_announcement_and_attachments": "extract_toc_from_announcement_and_attachments"  # 양식 X
        }
    )

    # 두 목차 추출 노드 모두 save_to_csv로 연결
    graph.add_edge("extract_toc_from_template", "save_to_csv")
    graph.add_edge("extract_toc_from_announcement_and_attachments", "save_to_csv")

    # save_to_csv → build_response → END
    graph.add_edge("save_to_csv", "build_response")
    graph.add_edge("build_response", END)

    # 컴파일
    batch_app = graph.compile()

    # Mermaid 다이어그램을 PNG로 저장
    try:
        png_data = batch_app.get_graph().draw_mermaid_png()
        output_path = "langgraph_diagram.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
        print(f"✅ Mermaid 다이어그램 PNG 저장: {output_path}")
    except Exception as e:
        print(f"⚠️ Mermaid 다이어그램 PNG 저장 실패: {e}")

    print("✅ LangGraph 컴파일 완료")
    print(f"\n📊 노드 구성:")
    print(f"  1. extract_all_texts (텍스트 + 표 구조 추출)")
    print(f"  2. chunk_all_documents (섹션 기반 청킹)")
    print(f"  3. embed_all_chunks (임베딩 생성)")
    print(f"  4. init_and_store_vectordb (Chroma VectorDB 저장)")
    print(f"  5. extract_features_rag (RAG 기반 Feature 추출)")
    print(f"  6. detect_templates (첨부 양식 감지) ✨ MVP1")
    print(f"  7. 조건부 라우팅 ⚡ TOC_ROUTER")
    print(f"     ├─ extract_toc_from_template (양식 O) ✨ MVP1")
    print(f"     └─ extract_toc_from_announcement_and_attachments (양식 X, 공고+첨부) ✨ MVP1")
    print(f"  8. save_to_csv (개발/테스트 - CSV 로컬 저장)")
    print(f"  9. build_response (최종 응답 생성 + Backend API 호출) ✨ MVP1")

    return batch_app
