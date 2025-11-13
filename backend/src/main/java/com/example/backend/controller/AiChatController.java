package com.example.backend.controller;

import com.example.backend.domain.AiChat;
import com.example.backend.service.AiChatService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * AiChatController
 *  - POST /ai-chat/response : 사용자 채팅 → FastAPI 호출 → DB 저장 → 응답
 *  - GET  /ai-chat/history  : DB에서 채팅 히스토리 조회
 */
@RestController
@RequestMapping("/ai-chat")
public class AiChatController {

    private final AiChatService aiChatService;

    @Autowired
    public AiChatController(AiChatService aiChatService){
        this.aiChatService = aiChatService;
    }

    /**
     * 사용자 메시지 처리
     * {
     *   "userMessage": "안녕하세요",
     *   "userIDx": 1,
     *   "projectIDx": 1
     * }
     */
    @PostMapping("/response")
    public AiChat sendMessage(@RequestBody ChatRequest chatRequest){
        return aiChatService.processChat(
                chatRequest.getUserMessage(),
                chatRequest.getUserIDx(),
                chatRequest.getProjectIDx()
        );
    }

    /**
     * 채팅 히스토리 조회
     */
    @GetMapping("/history")
    public List<AiChat> getChatHistory(){
        return aiChatService.getChatHistory();
    }

    /**
     * 요청 DTO
     */
    public static class ChatRequest {
        private String userMessage;
        private Long userIDx;
        private Long projectIDx;

        // Getter & Setter
        public String getUserMessage() {
            return userMessage;
        }
        public void setUserMessage(String userMessage) {
            this.userMessage = userMessage;
        }
        public Long getUserIDx() {
            return userIDx;
        }
        public void setUserIDx(Long userIDx) {
            this.userIDx = userIDx;
        }
        public Long getProjectIDx() {
            return projectIDx;
        }
        public void setProjectIDx(Long projectIDx) {
            this.projectIDx = projectIDx;
        }
    }
}