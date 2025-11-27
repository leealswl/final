package com.example.backend.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.backend.FastAPI.FastAPIService;
import com.example.backend.domain.AiChat;
import com.example.backend.service.AiChatService;

/**
 * AiChatController
 *  - POST /ai-chat/response : 사용자 채팅 → FastAPI 호출 → DB 저장 → 응답
 *  - GET  /ai-chat/history  : DB에서 채팅 히스토리 조회
 */
@RestController
@RequestMapping("/api/ai-chat")
public class AiChatController {

    // @Autowired
    // FastAPIService fastApi;

    private final AiChatService aiChatService;

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
    public AiChat sendMessage(@RequestBody AiChat chatRequest){
        System.out.println("💬 Chat 요청 수신: " + chatRequest.getUserMessage());
        return aiChatService.processChat(
            chatRequest.getUserMessage(),
            chatRequest.getUserIdx(),
            chatRequest.getProjectIdx(),
            chatRequest.getUserId()
        );
    }

    /**
     * 채팅 히스토리 조회
     */
    @GetMapping("/history")
    public List<AiChat> getChatHistory(){
        return aiChatService.getChatHistory();
    }
}