package com.example.backend.domain;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;
// Lombok의 @Data가 Getter/Setter/ToString 등을 자동으로 생성해줍니다.

@Data
public class AiChat {
    private Long userIdx;
    private String userId;
    private Long projectIdx;
    private String userMessage;
    private String aiResponse;

// ------------------- 💡 LangGraph 응답 수용 필드 (기존 필드) -------------------
    
    // 1. LangGraph가 생성한 최종 텍스트를 받는 필드 (FastAPI: generated_content)
    @JsonProperty("generated_content") 
    private String generatedContent;
    
    // 2. LangGraph의 전체 상태(디버깅 정보)를 받는 필드 (FastAPI: full_process_result)
    @JsonProperty("full_process_result")
    private Map<String, Object> fullProcessResult;

// ------------------- 🔑 LangGraph 멀티턴 및 상태 관리 필드 (추가) -------------------
    
    // 3. 현재 LangGraph 실행 스레드 ID (FastAPI: thread_id)
    // 멀티턴 실행 재개 시 필수
    @JsonProperty("thread_id")
    private String threadId;

    // 4. LangGraph의 현재 실행 상태 (FastAPI: status, 예: waiting_for_input, completed)
    // 프론트엔드에 다음 행동(질문 표시/결과 표시)을 지시하는 데 사용
    @JsonProperty("status")
    private String status;

    // 5. FastAPI의 "message" 필드를 수신하기 위한 필드 추가
    @JsonProperty("message")
    private String message;
    
    // 6. ProseMirror JSON 형식의 완성된 콘텐츠 (에디터용)
    @JsonProperty("completed_content")
    private Map<String, Object> completedContent;
}